from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Task, Dependency
from app.engine.critical_path import compute_critical_path

router = APIRouter(prefix="/api", tags=["critical-path"])


@router.get("/critical-path")
def get_critical_path(db: Session = Depends(get_db)):
    all_tasks = db.query(Task).all()
    graph = {}
    for dep in db.query(Dependency).all():
        graph.setdefault(dep.task_id, []).append(dep.prerequisite_id)

    schedule_input = {
        t.id: {"planned_start": t.planned_start, "duration_days": t.duration_days}
        for t in all_tasks
    }
    result = compute_critical_path(schedule_input, graph)
    task_by_id = {t.id: t for t in all_tasks}

    return {
        "path": [{"id": tid, "title": task_by_id[tid].title} for tid in result["path"]],
        "total_duration_days": result["total_duration_days"],
        "project_end_date": result["project_end_date"],
    }
