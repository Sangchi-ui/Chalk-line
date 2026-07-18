from __future__ import annotations
import os
import shutil
from fastapi import APIRouter
from app.services.skills_loader import skills_health

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    return {
        "ok": True,
        "llm_provider": os.getenv("LLM_PROVIDER", "gemini"),
        "manim_cli_found": shutil.which("manim") is not None,
        "skills": skills_health(),
    }
