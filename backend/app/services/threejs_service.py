"""
Step 2b (3D path): turn the same SceneSpec used for Manim into a Three.js
scene, grounded in your tested Three.js SKILL.md.

Unlike Manim, Three.js runs client-side, so there's nothing to "render" on
the server — we generate a small, structured payload the frontend's
initThree() can consume directly to build geometry (safe: no eval of
arbitrary strings) plus optional camera hints for orbit defaults.

Because the underlying math came from the same SceneSpec as the 2D version,
a "parabola" prompt produces the same y = x^2 relationship in both modes —
just rendered as a flat curve in Manim and an interactive surface/curve in
Three.js.
"""

from __future__ import annotations
from app.models.schemas import SceneSpec
from app.services.llm_client import complete, extract_json
from app.services.skills_loader import get_threejs_skill

_CODEGEN_SYSTEM_TEMPLATE = """You translate a math scene spec into Three.js
geometry instructions for a live classroom viewer. You MUST follow the
conventions and API version notes in the SKILL reference below — it was
built and empirically verified in a real sandbox (exact Three.js revision,
which classes exist, which don't). Do not use APIs it doesn't mention
without good reason.

=== THREE.JS SKILL REFERENCE (authoritative) ===
{skill_text}
=== END SKILL REFERENCE ===

Output ONLY a single JSON object (no markdown fences) with this shape:
{{
  "objects": [
    {{
      "id": "matches the scene spec object id",
      "geometry": "parametric | surface_grid | line | points | sphere | box | custom",
      "sampling": {{"u_range": [min,max], "v_range": [min,max], "segments": 40}},
      "expr": {{"x": "u", "y": "v", "z": "u**2+v**2"}},
      "color": "#hexcolor",
      "wireframe": false,
      "label": "optional short label"
    }}
  ],
  "camera": {{"position": [x,y,z], "look_at": [0,0,0]}},
  "grid": {{"size": 10, "divisions": 20}}
}}

Rules:
- Expressions in "expr" must be simple Python/JS-evaluable math (u, v as parameters).
- Every object id must correspond to an object id in the provided scene spec.
- Keep object count minimal (1-4), matching the scene spec.
"""


async def generate_threejs_payload(scene_spec: SceneSpec) -> dict:
    skill = get_threejs_skill()
    system = _CODEGEN_SYSTEM_TEMPLATE.format(skill_text=skill.text)
    user = (
        "Scene spec (JSON):\n"
        f"{scene_spec.model_dump_json(indent=2)}\n\n"
        "Produce the Three.js geometry payload JSON now."
    )
    raw = await complete(system, user, json_mode=True)
    payload = extract_json(raw)
    _basic_validate(payload)
    return payload


def _basic_validate(payload: dict) -> None:
    if "objects" not in payload or not isinstance(payload["objects"], list):
        raise ValueError("Three.js payload missing 'objects' list.")
    if len(payload["objects"]) == 0:
        raise ValueError("Three.js payload has zero objects to render.")
