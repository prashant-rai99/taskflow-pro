"""
Task breakdown generator endpoint -- describe a feature, get back
proposed sub-tasks + dependencies, created directly as real tasks
(in the "backlog" column) with real dependency rows.

Unlike suggest-dependencies (which needs human approval before writing
to the Dependency table, since it's guessing about EXISTING work),
here the LLM is proposing brand-new tasks that don't exist yet -- so
there's no "wrong existing dependency" risk. We still validate
structurally (see breakdown_parser.py) before writing anything.
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Task, Dependency
from app.ai.providers.groq_provider import GroqProvider
from app.ai.breakdown_prompts import build_breakdown_prompt
from app.ai.breakdown_parser import parse_breakdown, BreakdownParseError

router = APIRouter(prefix="/api/breakdown", tags=["ai-breakdown"])


class BreakdownRequest(BaseModel):
    feature_description: str
    planned_start: date = None


@router.post("")
def generate_breakdown(payload: BreakdownRequest, db: Session = Depends(get_db)):
    provider = GroqProvider()
    system_prompt, user_prompt = build_breakdown_prompt(payload.feature_description)

    try:
        raw_response = provider.complete(
            user_prompt, system=system_prompt, temperature=0.2
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM provider failed: {e}")

    try:
        subtasks = parse_breakdown(raw_response)
    except BreakdownParseError as e:
        raise HTTPException(
            status_code=502, detail=f"Could not parse LLM response: {e}"
        )

    start_date = payload.planned_start or date.today()

    # Create all tasks first (so we have real DB ids), THEN create
    # dependencies -- since dependencies reference other tasks' ids.
    created_tasks: dict[int, Task] = {}  # llm_index -> Task row

    for st in subtasks:
        task = Task(
            title=st["title"],
            description=st["description"],
            column="backlog",
            position=0,
            planned_start=start_date,
            duration_days=st["duration_days"],
        )
        db.add(task)
        db.flush()  # get task.id without committing yet
        created_tasks[st["index"]] = task

    db.commit()
    for task in created_tasks.values():
        db.refresh(task)

    dependencies_created = []
    for st in subtasks:
        this_task = created_tasks[st["index"]]
        for dep_index in st["depends_on_indices"]:
            prereq_task = created_tasks.get(dep_index)
            if prereq_task is None:
                continue
            dependency = Dependency(
                task_id=this_task.id, prerequisite_id=prereq_task.id
            )
            db.add(dependency)
            dependencies_created.append((this_task.id, prereq_task.id))

    db.commit()

    return {
        "feature_description": payload.feature_description,
        "tasks_created": [
            {"id": t.id, "title": t.title, "duration_days": t.duration_days}
            for t in created_tasks.values()
        ],
        "dependencies_created": [
            {"task_id": a, "prerequisite_id": b} for a, b in dependencies_created
        ],
    }
