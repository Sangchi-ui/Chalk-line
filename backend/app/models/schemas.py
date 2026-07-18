"""
Shared data contracts.

The core design decision: one AI call produces a single, engine-agnostic
SceneSpec from the faculty's prompt. That SceneSpec is then handed to
*two independent renderers* — one that turns it into Manim Python (2D),
one that turns it into a Three.js scene description (3D). Neither
renderer talks to the other; both only depend on this shared shape.
This keeps the 2D and 3D outputs mathematically consistent (same domain,
same labeled objects) without coupling the two rendering pipelines.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class Mode(str, Enum):
    TWO_D = "2d"
    THREE_D = "3d"


# ---------------------------------------------------------------------------
# Incoming request from the frontend chat panel
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    mode: Mode
    # optional: id of a previous job, if the faculty is refining ("make it blue")
    refine_job_id: Optional[str] = None


# ---------------------------------------------------------------------------
# The shared intermediate representation
# ---------------------------------------------------------------------------

class SceneObject(BaseModel):
    """One mathematical object to render: a curve, surface, shape, label, etc."""
    id: str
    kind: Literal[
        "function_2d", "parametric_2d", "surface_3d", "curve_3d",
        "point", "vector", "axes", "circle", "polygon", "text_label",
        "angle_marker", "shaded_region", "solid"
    ]
    # Free-form params interpreted by each renderer (e.g. {"expr": "x**2", "domain": [-3,3]})
    params: dict[str, Any] = Field(default_factory=dict)
    color: Optional[str] = None
    label: Optional[str] = None


class SceneSpec(BaseModel):
    """Engine-agnostic description of what to draw, produced once by the LLM."""
    topic: str
    summary: str
    domain: Mode  # informs the LLM's own sense of intended dimensionality
    axes: dict[str, Any] = Field(default_factory=dict)
    objects: list[SceneObject] = Field(default_factory=list)
    animations: list[dict[str, Any]] = Field(default_factory=list)
    camera_hint: Optional[dict[str, Any]] = None  # only meaningful for 3D


# ---------------------------------------------------------------------------
# Job tracking (in-memory; swap for Redis/DB later if needed)
# ---------------------------------------------------------------------------

class JobStatus(str, Enum):
    QUEUED = "queued"
    PLANNING = "planning"       # LLM building the SceneSpec
    CODEGEN = "codegen"         # LLM building Manim/Three.js code from spec
    RENDERING = "rendering"     # manim subprocess running (2D only)
    DONE = "done"
    ERROR = "error"


class Job(BaseModel):
    id: str
    mode: Mode
    prompt: str
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0        # 0..1, coarse-grained
    message: str = ""
    scene_spec: Optional[SceneSpec] = None
    video_url: Optional[str] = None       # 2D result
    scene_payload: Optional[dict] = None  # 3D result (renderer-ready params)
    error: Optional[str] = None


class GenerateResponse(BaseModel):
    job_id: str
    status: JobStatus
    mode: Mode
    video_url: Optional[str] = None
    scene_spec: Optional[dict] = None
    duration_seconds: Optional[float] = None
