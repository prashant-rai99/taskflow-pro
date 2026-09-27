"""
What-if preview -- simulate a hypothetical duration/start change,
recompute schedule in-memory (never writes to DB), show the shift.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Task, Dependency
from app.engine.schedule import compute_schedule

router = APIRouter(prefix="/api", tags=["what-if"])


class WhatIfRequest(BaseModel):
    task_id: int
    new_duration_days: Optional[int] = None
    new_planned_start: Optional[date] = None


@router.post("/what-if")
def what_if_preview(payload: WhatIfRequest, db: Session = Depends(get_db)):
    all_tasks = db.query(Task).all()
    task_by_id = {t.id: t for t in all_tasks}
    if payload.task_id not in task_by_id:
        raise HTTPException(status_code=404, detail="Task not found")

    graph = {}
    for dep in db.query(Dependency).all():
        graph.setdefault(dep.task_id, []).append(dep.prerequisite_id)

    original_input = {
        t.id: {"planned_start": t.planned_start, "duration_days": t.duration_days}
        for t in all_tasks
    }
    original_schedule = compute_schedule(original_input, graph)

    hypothetical_input = {tid: dict(v) for tid, v in original_input.items()}
    if payload.new_duration_days is not None:
        hypothetical_input[payload.task_id]["duration_days"] = payload.new_duration_days
    if payload.new_planned_start is not None:
        hypothetical_input[payload.task_id]["planned_start"] = payload.new_planned_start

    hypothetical_schedule = compute_schedule(hypothetical_input, graph)

    changes = []
    for tid in original_schedule:
        orig_end, new_end = (
            original_schedule[tid]["end"],
            hypothetical_schedule[tid]["end"],
        )
        if orig_end != new_end:
            changes.append(
                {
                    "task_id": tid,
                    "title": task_by_id[tid].title,
                    "original_end": orig_end,
                    "new_end": new_end,
                    "shift_days": (new_end - orig_end).days,
                }
            )

    return {
        "task_id": payload.task_id,
        "changes": changes,
        "project_end_before": max(s["end"] for s in original_schedule.values()),
        "project_end_after": max(s["end"] for s in hypothetical_schedule.values()),
    }
