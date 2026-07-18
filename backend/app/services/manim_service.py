"""
Step 2a (2D path): turn a SceneSpec into Manim Python code, grounded in your
tested SKILL.md, then actually render it with the `manim` CLI.

"Live/streamed rendering" here means: we don't make the faculty wait on one
opaque black box. We push job-status updates (planning -> codegen ->
rendering -> done) through the Job object as we go, so the frontend's
loading state can show real progress instead of a static spinner. The
render itself is still a batch `manim` subprocess call (Manim has no true
frame-streaming mode), but because MANIM_QUALITY defaults to low/draft
quality, a typical single-concept scene renders in a few seconds.
"""

from __future__ import annotations
import asyncio
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path

from app.models.schemas import SceneSpec
from app.services.llm_client import complete
from app.services.skills_loader import get_manim_skill

_CODEGEN_SYSTEM_TEMPLATE = """You write Manim Python scenes for a live classroom tool.
You MUST follow the conventions, imports, and API patterns in the SKILL
reference below exactly — it was built and empirically verified in a real
sandbox, so do not substitute remembered/assumed Manim API calls that
contradict it.

=== MANIM SKILL REFERENCE (authoritative) ===
{skill_text}
=== END SKILL REFERENCE ===

Output rules:
- Output ONLY a single Python code block's contents — raw Python source, no markdown fences.
- Define exactly one Scene subclass named `GeneratedScene`.
- The scene must be self-contained (no file I/O, no network calls).
- Keep total animation runtime under ~12 seconds so classroom pacing stays tight.
- Use color names/hex from the scene spec's "color" fields where given.
"""


class ManimRenderError(RuntimeError):
    pass


def _sanitize_job_id(job_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "", job_id)


async def generate_manim_code(scene_spec: SceneSpec) -> str:
    skill = get_manim_skill()
    system = _CODEGEN_SYSTEM_TEMPLATE.format(skill_text=skill.text)
    user = (
        "Scene spec (JSON):\n"
        f"{scene_spec.model_dump_json(indent=2)}\n\n"
        "Write the GeneratedScene class now."
    )
    code = await complete(system, user, json_mode=False)
    code = _strip_code_fences(code)
    _basic_safety_check(code)
    return code


def _strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


_FORBIDDEN_PATTERNS = [
    r"\bimport\s+os\b", r"\bimport\s+sys\b", r"\bimport\s+subprocess\b",
    r"\bopen\s*\(", r"\beval\s*\(", r"\bexec\s*\(", r"\b__import__\b",
    r"\brequests\b", r"\bsocket\b",
]


def _basic_safety_check(code: str) -> None:
    """Generated code runs as a local subprocess — this is a guardrail, not a sandbox.
    For production use, run the manim subprocess under a locked-down user/container."""
    for pattern in _FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            raise ManimRenderError(
                f"Generated Manim code contains a disallowed pattern ('{pattern}'). "
                "Refusing to render for safety. Try rephrasing the prompt."
            )
    if "class GeneratedScene" not in code:
        raise ManimRenderError("Generated code did not define a GeneratedScene class.")


async def render_manim_scene(job_id: str, code: str) -> Path:
    """Writes the generated scene to disk and renders it via the manim CLI.
    Returns the path to the produced .mp4."""
    job_id = _sanitize_job_id(job_id)
    render_dir = Path(os.getenv("RENDER_DIR", "./renders")).resolve()
    work_dir = render_dir / "manim" / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    scene_file = work_dir / "scene.py"
    scene_file.write_text(code, encoding="utf-8")

    quality_flag = {"l": "-ql", "m": "-qm", "h": "-qh"}.get(
        os.getenv("MANIM_QUALITY", "l"), "-ql"
    )
    timeout = int(os.getenv("MANIM_TIMEOUT_SECONDS", "90"))

    if shutil.which("manim") is None:
        raise ManimRenderError(
            "The `manim` CLI is not installed/on PATH. "
            "Install it (pip install manim, plus ffmpeg + a LaTeX distro for "
            "Tex-heavy scenes) and try again."
        )

    cmd = [
        "manim", quality_flag, "--media_dir", str(work_dir / "media"),
        str(scene_file), "GeneratedScene",
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(work_dir),
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise ManimRenderError(f"Manim render exceeded {timeout}s timeout and was killed.")

    if proc.returncode != 0:
        raise ManimRenderError(
            f"Manim render failed (exit {proc.returncode}):\n{stderr.decode(errors='replace')[-2000:]}"
        )

    mp4_path = _find_output_mp4(work_dir / "media")
    if mp4_path is None:
        raise ManimRenderError("Manim reported success but no .mp4 output was found.")

    # copy to a stable, flat public path: renders/manim/{job_id}.mp4
    final_path = render_dir / "manim" / f"{job_id}.mp4"
    shutil.copy2(mp4_path, final_path)
    return final_path


def _find_output_mp4(media_dir: Path) -> Path | None:
    if not media_dir.exists():
        return None
    candidates = sorted(media_dir.rglob("GeneratedScene.mp4"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None
