"""
Step 1 of the pipeline: turn the faculty's free-text prompt into a single,
engine-agnostic SceneSpec (see app/models/schemas.py).

This call does NOT know about Manim or Three.js syntax at all — that's the
point. It only reasons about the *mathematics* being requested. The two
codegen services (manim_service, threejs_service) are the only places that
translate this into engine-specific code, each grounded in your tested
SKILL.md files.
"""

from __future__ import annotations
from app.models.schemas import SceneSpec, Mode
from app.services.llm_client import complete, extract_json

_SYSTEM_PROMPT = """You are a math-visualization planner for a classroom tool.
Given a short instruction from a teacher, output ONE JSON object describing
the mathematical scene to visualize. Do NOT write any rendering code.
Do NOT mention Manim or Three.js. Only describe the math.

JSON shape (all fields required unless noted):
{
  "topic": "short human title, e.g. 'Parabola y = x^2'",
  "summary": "1-2 sentence description of what will be shown and why it's pedagogically useful",
  "axes": {"x_range": [min, max], "y_range": [min, max], "z_range": [min, max] (3d only)},
  "objects": [
    {
      "id": "short_snake_case_id",
      "kind": "function_2d | parametric_2d | surface_3d | curve_3d | point | vector | axes | circle | polygon | text_label | angle_marker | shaded_region | solid",
      "params": { ...kind-specific, e.g. {"expr": "x**2", "domain": [-3,3]} for function_2d,
                  or {"expr_x": "u", "expr_y": "v", "expr_z": "u**2+v**2", "u_range":[-2,2], "v_range":[-2,2]} for surface_3d },
      "color": "a css-ish color name or hex, thematically appropriate",
      "label": "optional short label shown next to the object"
    }
  ],
  "animations": [
    {"target": "object_id", "type": "draw | fade_in | transform | trace | rotate | grow", "order": 1}
  ],
  "camera_hint": {"elevation_deg": 25, "azimuth_deg": -45} 
}

Rules:
- Keep objects minimal and focused — 1-4 objects is typical for a single classroom concept.
- Use standard math notation in "expr" fields (Python-eval-able: **, sin, cos, sqrt, pi).
- If the teacher's prompt is ambiguous, make the most pedagogically common assumption
  (e.g. "parabola" -> y = x^2) and say so briefly in "summary".
- Output ONLY the JSON object. No markdown fences, no commentary.
"""


async def build_scene_spec(prompt: str, mode: Mode) -> SceneSpec:
    user_prompt = (
        f"Teacher's instruction: \"{prompt}\"\n"
        f"Target dimensionality: {mode.value} "
        f"({'flat 2D diagram' if mode == Mode.TWO_D else 'a scene meant to be viewed and orbited in 3D'}).\n"
        f"Produce the JSON scene spec now."
    )
    raw = await complete(_SYSTEM_PROMPT, user_prompt, json_mode=True)
    data = extract_json(raw)
    data["domain"] = mode.value
    return SceneSpec(**data)
