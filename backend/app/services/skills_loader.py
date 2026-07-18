"""
Loads your hand-built, empirically-tested SKILL.md files for Manim and
Three.js, and feeds their contents to the LLM as system-prompt context
whenever we ask it to generate code in either engine.

This is the reason we don't let the model "wing it" from general training
knowledge: your skills encode verified API patterns (what actually works in
your sandbox), so codegen prompts are grounded in that rather than in
whatever the model half-remembers about Manim/Three.js versions.

Point MANIM_SKILL_PATH / THREEJS_SKILL_PATH (see .env.example) at your
SKILL.md files. If a file is missing, we fail loudly and early rather than
silently generating unverified code — better to know immediately than to
debug a bad render later.
"""

from __future__ import annotations
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


class SkillNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True)
class SkillContent:
    name: str
    path: Path
    text: str


def _load_skill_file(env_var: str, default_path: str, skill_name: str) -> SkillContent:
    raw_path = os.getenv(env_var, default_path)
    path = Path(raw_path).expanduser().resolve()

    if not path.exists():
        raise SkillNotFoundError(
            f"[{skill_name}] SKILL.md not found at '{path}'. "
            f"Set {env_var} in your .env to point at the SKILL.md you built "
            f"and empirically tested for {skill_name}, then restart the server."
        )

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise SkillNotFoundError(f"[{skill_name}] SKILL.md at '{path}' is empty.")

    return SkillContent(name=skill_name, path=path, text=text)


@lru_cache(maxsize=1)
def get_manim_skill() -> SkillContent:
    return _load_skill_file("MANIM_SKILL_PATH", "./skills/manim/SKILL.md", "manim")


@lru_cache(maxsize=1)
def get_threejs_skill() -> SkillContent:
    return _load_skill_file("THREEJS_SKILL_PATH", "./skills/threejs/SKILL.md", "threejs")


def skills_health() -> dict:
    """Used by /api/health so the UI/dev can see at a glance which skills loaded."""
    out = {}
    for name, loader in (("manim", get_manim_skill), ("threejs", get_threejs_skill)):
        try:
            skill = loader()
            out[name] = {"loaded": True, "path": str(skill.path), "chars": len(skill.text)}
        except SkillNotFoundError as e:
            out[name] = {"loaded": False, "error": str(e)}
    return out
