"""
Task CRUD endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Task, Dependency
from app.schemas import TaskCreate, TaskUpdate, TaskOut
from app.engine.schedule import compute_schedule
from app.engine.status import compute_status

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _build_graph(db: Session):
    """adjacency = { task_id: [prerequisite_id, ...] } from the dependencies table."""
    graph = {}
    for dep in db.query(Dependency).all():
        graph.setdefault(dep.task_id, []).append(dep.prerequisite_id)
    return graph


def _attach_computed_fields(tasks: list[Task], db: Session) -> list[TaskOut]:
    """Given raw Task rows, attach live-computed schedule + status."""
    graph = _build_graph(db)

    schedule_input = {
        t.id: {"planned_start": t.planned_start, "duration_days": t.duration_days}
        for t in tasks
    }
    schedule_result = compute_schedule(schedule_input, graph)

    columns = {t.id: t.column for t in tasks}
    status_result = compute_status(columns, graph)

    output = []
    for t in tasks:
        task_out = TaskOut.model_validate(t)
        task_out.computed_start = schedule_result[t.id]["start"]
        task_out.computed_end = schedule_result[t.id]["end"]
        task_out.status = status_result[t.id]
        output.append(task_out)
    return output


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.column, Task.position).all()
    if not tasks:
        return []
    return _attach_computed_fields(tasks, db)


@router.post("", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return _attach_computed_fields([task], db)[0]


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(task, field, value)
    task.version += 1

    db.commit()
    db.refresh(task)
    return _attach_computed_fields([task], db)[0]


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return None
