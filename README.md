# Chalkline Backend

FastAPI backend for Chalkline. Turns a faculty prompt into either a rendered
Manim video (2D) or a Three.js scene payload (3D), using your hand-built,
empirically-tested SKILL.md files as the authoritative reference for codegen.

## Pipeline (matches the two decisions we made)

```
prompt ──► scene_spec_service (LLM call #1)
              │
              ▼
        SceneSpec (shared, engine-agnostic JSON)
              │
        ┌─────┴─────┐
        ▼           ▼
  manim_service   threejs_service     (LLM call #2, grounded in your skill)
   (2D: Manim         (3D: JSON payload
   Python code,        the browser's
   subprocess           Three.js scene
   render → mp4)        consumes directly)
        │                   │
        ▼                   ▼
   /renders/manim/*.mp4   returned inline
```

One LLM call decides *what math to show* (SceneSpec). A second, engine-specific
call decides *how to draw it*, but only after being handed your tested skill
file as context — so codegen is grounded in verified API patterns, not the
model's general (possibly outdated) training knowledge of Manim/Three.js.

## Setup

```bash
cd chalkline-backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env`:
1. Pick `LLM_PROVIDER` (gemini | groq | mistral) and set its API key.
2. **Point `MANIM_SKILL_PATH` and `THREEJS_SKILL_PATH` at your actual
   SKILL.md files.** Two placeholder folders exist at `skills/manim/` and
   `skills/threejs/` — drop your real SKILL.md into each, or point the env
   vars at wherever they already live on disk.

System requirements for the 2D path:
- `ffmpeg` on PATH (Manim needs it to mux video)
- A LaTeX distribution if your Manim skill relies on `Tex`/`MathTex` (optional
  otherwise — plain `Text` doesn't need it)

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Check `/api/health` first — it reports whether both skill files loaded and
whether the `manim` CLI is on PATH, before you try a real generation.

## Frontend wiring

The `chalkline.html` frontend calls `POST /api/generate` with
`{ prompt, mode: "2d"|"3d" }` and expects:

- 2D: `{ job_id, status, video_url, scene_spec, duration_seconds }` — the
  video is served from `/renders/manim/{job_id}.mp4` (mounted as a static dir).
- 3D: `{ job_id, status, scene_spec, duration_seconds }` — here `scene_spec`
  is actually the Three.js geometry payload (objects/camera/grid), ready for
  the frontend's `initThree()` to build meshes from directly — no `eval`,
  no code shown in the UI.

If the frontend is opened as a static file (not served from the same origin
as the API), set `window.CHALKLINE_API_BASE = "http://localhost:8000"` before
the app's script runs, or edit `API_BASE` directly in `chalkline.html`.

## Notes / next steps

- Jobs are stored in-memory (`app/services/job_store.py`) — fine for one
  faculty machine, swap for Redis if you ever need multiple workers.
- Generated Manim code goes through a basic pattern blocklist
  (`_FORBIDDEN_PATTERNS` in `manim_service.py`) before being run as a
  subprocess. This is a guardrail, not a sandbox — for shared/multi-user
  deployment, run the `manim` subprocess inside a locked-down container.
- `MANIM_QUALITY=l` (draft/480p15) is the default for fast iteration during
  a live class; bump to `m` or `h` for recorded material.
- The 3D payload's `expr` fields are simple math strings (not executed
  server-side) — you'll need a small expression evaluator on the frontend
  (e.g. mathjs, already available per your artifact environment) to turn
  `"u**2 + v**2"` into actual vertex positions in `initThree()`.