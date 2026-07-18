from __future__ import annotations
import os
import time
from fastapi import APIRouter, HTTPException

from app.models.schemas import GenerateRequest, GenerateResponse, JobStatus, Mode
from app.services import job_store
from app.services.scene_spec_service import build_scene_spec
from app.services.manim_service import generate_manim_code, render_manim_scene, ManimRenderError
from app.services.threejs_service import generate_threejs_payload
from app.services.llm_client import LLMError
from app.services.skills_loader import SkillNotFoundError

router = APIRouter(prefix="/api", tags=["generate"])


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    job = job_store.create_job(req.prompt, req.mode)
    started = time.monotonic()

    try:
        # --- Step 1: shared scene spec (same for both modes) ---
        job = job_store.update_job(job.id, status=JobStatus.PLANNING, progress=0.2,
                                    message="Interpreting the topic")
        scene_spec = await build_scene_spec(req.prompt, req.mode)
        job = job_store.update_job(job.id, scene_spec=scene_spec)

        # --- Step 2: engine-specific codegen, grounded in your skills ---
        job = job_store.update_job(job.id, status=JobStatus.CODEGEN, progress=0.45,
                                    message="Writing render code")

        if req.mode == Mode.TWO_D:
            code = await generate_manim_code(scene_spec)

            job = job_store.update_job(job.id, status=JobStatus.RENDERING, progress=0.65,
                                        message="Rendering animation")
            mp4_path = await render_manim_scene(job.id, code)

            video_url = f"/renders/manim/{mp4_path.name}"
            job = job_store.update_job(
                job.id, status=JobStatus.DONE, progress=1.0,
                message="Done", video_url=video_url,
            )
            return GenerateResponse(
                job_id=job.id, status=job.status, mode=req.mode,
                video_url=video_url, scene_spec=scene_spec.model_dump(),
                duration_seconds=round(time.monotonic() - started, 2),
            )

        else:  # 3D
            payload = await generate_threejs_payload(scene_spec)
            job = job_store.update_job(
                job.id, status=JobStatus.DONE, progress=1.0,
                message="Done", scene_payload=payload,
            )
            return GenerateResponse(
                job_id=job.id, status=job.status, mode=req.mode,
                scene_spec=payload,  # frontend expects scene_spec field either way
                duration_seconds=round(time.monotonic() - started, 2),
            )

    except SkillNotFoundError as e:
        job_store.update_job(job.id, status=JobStatus.ERROR, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except LLMError as e:
        job_store.update_job(job.id, status=JobStatus.ERROR, error=str(e))
        raise HTTPException(status_code=502, detail=f"Model provider error: {e}")
    except ManimRenderError as e:
        job_store.update_job(job.id, status=JobStatus.ERROR, error=str(e))
        raise HTTPException(status_code=500, detail=f"Render error: {e}")
    except Exception as e:  # noqa: BLE001 — surface unexpected errors to the dev during build-out
        job_store.update_job(job.id, status=JobStatus.ERROR, error=str(e))
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
