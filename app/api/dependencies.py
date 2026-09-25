"""
Dependency endpoints -- this is where cycle prevention actually happens.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Task, Dependency
from app.schemas import DependencyCreate, DependencyOut
from app.engine.cycle import would_create_cycle

router = APIRouter(prefix="/api/dependencies", tags=["dependencies"])


@router.post("", response_model=DependencyOut, status_code=201)
def create_dependency(payload: DependencyCreate, db: Session = Depends(get_db)):
    # Both tasks must exist.
    task = db.query(Task).filter(Task.id == payload.task_id).first()
    prereq = db.query(Task).filter(Task.id == payload.prerequisite_id).first()
    if not task or not prereq:
        raise HTTPException(status_code=404, detail="Task or prerequisite not found")

    # Duplicate check (DB has a UniqueConstraint too, but we want a clean error message).
    existing = (
        db.query(Dependency)
        .filter(
            Dependency.task_id == payload.task_id,
            Dependency.prerequisite_id == payload.prerequisite_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="This dependency already exists")

    # Build current graph BEFORE inserting, then check the new edge.
    graph = {}
    for dep in db.query(Dependency).all():
        graph.setdefault(dep.task_id, []).append(dep.prerequisite_id)

    if would_create_cycle(graph, payload.task_id, payload.prerequisite_id):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Adding this dependency would create a cycle: "
                f"task {payload.task_id} cannot depend on task {payload.prerequisite_id} "
                f"because {payload.prerequisite_id} already (transitively) depends on "
                f"{payload.task_id}."
            ),
        )

    # Safe to insert -- single transaction, all-or-nothing.
    dependency = Dependency(
        task_id=payload.task_id,
        prerequisite_id=payload.prerequisite_id,
    )
    db.add(dependency)
    db.commit()
    db.refresh(dependency)
    return dependency


@router.delete("/{dependency_id}", status_code=204)
def delete_dependency(dependency_id: int, db: Session = Depends(get_db)):
    dependency = db.query(Dependency).filter(Dependency.id == dependency_id).first()
    if not dependency:
        raise HTTPException(status_code=404, detail="Dependency not found")
    db.delete(dependency)
    db.commit()
    return None