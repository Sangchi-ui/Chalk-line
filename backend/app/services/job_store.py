"""In-memory job registry. Fine for a single-process classroom tool;
swap for Redis if you ever need multiple backend workers."""

from __future__ import annotations
import uuid
from app.models.schemas import Job, Mode, JobStatus

_jobs: dict[str, Job] = {}


def create_job(prompt: str, mode: Mode) -> Job:
    job = Job(id=uuid.uuid4().hex[:12], mode=mode, prompt=prompt)
    _jobs[job.id] = job
    return job


def get_job(job_id: str) -> Job | None:
    return _jobs.get(job_id)


def update_job(job_id: str, **fields) -> Job:
    job = _jobs[job_id]
    updated = job.model_copy(update=fields)
    _jobs[job_id] = updated
    return updated
