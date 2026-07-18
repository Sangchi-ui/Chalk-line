from __future__ import annotations
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import generate, health

app = FastAPI(title="Chalkline API", version="0.1.0")

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

render_dir = Path(os.getenv("RENDER_DIR", "./renders")).resolve()
render_dir.mkdir(parents=True, exist_ok=True)
(render_dir / "manim").mkdir(exist_ok=True)
app.mount("/renders", StaticFiles(directory=str(render_dir)), name="renders")

app.include_router(generate.router)
app.include_router(health.router)


@app.get("/")
async def root():
    return {"service": "chalkline-api", "docs": "/docs", "health": "/api/health"}
