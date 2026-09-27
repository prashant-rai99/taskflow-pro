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
    graph = {}
    for dep in db.query(Dependency).all():
        graph.setdefault(dep.task_id, []).append(dep.prerequisite_id)
    return graph


def _compute_all(db: Session) -> dict[int, TaskOut]:
    """
    Fetch ALL tasks and compute schedule + status over the FULL graph.
    This must always run on the complete task set -- the schedule and
    status engines need every task's dependencies present, not just
    the one being created/updated, otherwise the topological sort
    breaks (missing nodes it expects to see).

    Returns a dict keyed by task_id for easy lookup.
    """
    all_tasks = db.query(Task).all()
    graph = _build_graph(db)

    schedule_input = {
        t.id: {"planned_start": t.planned_start, "duration_days": t.duration_days}
        for t in all_tasks
    }
    schedule_result = compute_schedule(schedule_input, graph)

    columns = {t.id: t.column for t in all_tasks}
    status_result = compute_status(columns, graph)

    output = {}
    for t in all_tasks:
        task_out = TaskOut.model_validate(t)
        task_out.computed_start = schedule_result[t.id]["start"]
        task_out.computed_end = schedule_result[t.id]["end"]
        task_out.status = status_result[t.id]
        output[t.id] = task_out
    return output


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    computed = _compute_all(db)
    tasks = db.query(Task).order_by(Task.column, Task.position).all()
    return [computed[t.id] for t in tasks]


@router.post("", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)

    computed = _compute_all(db)
    return computed[task.id]


@router.get("/{task_id}/explain-status")
def explain_status(task_id: int, db: Session = Depends(get_db)):
    """
    Deterministic explanation of why a task is Blocked or Ready --
    NOT AI-generated. Walks the dependency graph and reports exactly
    which prerequisites (direct or transitive) are not yet Done.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    all_tasks = db.query(Task).all()
    task_by_id = {t.id: t for t in all_tasks}
    graph = _build_graph(db)

    def is_effectively_done(tid, memo={}):
        if tid in memo:
            return memo[tid]
        t = task_by_id.get(tid)
        if t is None or t.column != "done":
            memo[tid] = False
            return False
        for prereq_id in graph.get(tid, []):
            if not is_effectively_done(prereq_id, memo):
                memo[tid] = False
                return False
        memo[tid] = True
        return True

    blocking_reasons = []
    for prereq_id in graph.get(task_id, []):
        if not is_effectively_done(prereq_id):
            prereq_task = task_by_id.get(prereq_id)
            blocking_reasons.append(
                {
                    "prerequisite_id": prereq_id,
                    "prerequisite_title": (
                        prereq_task.title if prereq_task else "(unknown)"
                    ),
                    "current_column": (
                        prereq_task.column if prereq_task else "(unknown)"
                    ),
                }
            )

    is_blocked = len(blocking_reasons) > 0

    return {
        "task_id": task_id,
        "task_title": task.title,
        "is_blocked": is_blocked,
        "blocking_reasons": blocking_reasons,
        "explanation": (
            f"This task is blocked because {len(blocking_reasons)} prerequisite(s) "
            f"are not yet Done."
            if is_blocked
            else "This task is ready -- all prerequisites are Done (or it has none)."
        ),
    }


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

    computed = _compute_all(db)
    return computed[task_id]


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return None
