"""
AI dependency suggestion endpoints.

Pipeline: LLM call -> parse/validate (grounding) -> cycle-filter ->
save as PENDING (never auto-applied) -> separate approve/reject endpoints
write to the real Dependency table.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db import get_db
from app.models import Task, Dependency, AISuggestion
from app.ai.providers.groq_provider import GroqProvider
from app.ai.prompts import build_prompt
from app.ai.parser import parse_suggestions, ParseError
from app.engine.cycle import would_create_cycle
from app.schemas import DependencyOut

router = APIRouter(prefix="/api/tasks", tags=["ai-suggestions"])


@router.post("/{task_id}/suggest-dependencies")
def suggest_dependencies(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    other_tasks = db.query(Task).filter(Task.id != task_id).all()
    existing_tasks = [
        {"id": t.id, "title": t.title, "description": t.description}
        for t in other_tasks
    ]
    valid_task_ids = {t.id for t in other_tasks}

    system_prompt, user_prompt = build_prompt(
        new_task_id=task.id,
        new_task_title=task.title,
        new_task_description=task.description,
        existing_tasks=existing_tasks,
    )

    provider = GroqProvider()
    try:
        raw_response = provider.complete(
            user_prompt, system=system_prompt, temperature=0.1
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM provider failed: {e}")

    try:
        suggestions = parse_suggestions(raw_response, valid_task_ids=valid_task_ids)
    except ParseError as e:
        raise HTTPException(
            status_code=502, detail=f"Could not parse LLM response: {e}"
        )

    # Build current graph to cycle-filter suggestions before saving.
    graph = {}
    for dep in db.query(Dependency).all():
        graph.setdefault(dep.task_id, []).append(dep.prerequisite_id)

    saved = []
    skipped_cycles = []

    for s in suggestions:
        if would_create_cycle(graph, task_id, s["prerequisite_id"]):
            skipped_cycles.append(s["prerequisite_id"])
            continue

        # Don't duplicate an existing pending/approved suggestion for the same pair.
        existing = (
            db.query(AISuggestion)
            .filter(
                AISuggestion.task_id == task_id,
                AISuggestion.suggested_prerequisite_id == s["prerequisite_id"],
                AISuggestion.status == "pending",
            )
            .first()
        )
        if existing:
            continue

        suggestion = AISuggestion(
            task_id=task_id,
            suggested_prerequisite_id=s["prerequisite_id"],
            reason=s["reason"],
            evidence=s["evidence"],
            confidence=s["confidence"],
            provider="groq",
            status="pending",
        )
        db.add(suggestion)
        saved.append(suggestion)

    db.commit()
    for s in saved:
        db.refresh(s)

    return {
        "task_id": task_id,
        "suggestions_saved": [
            {
                "id": s.id,
                "suggested_prerequisite_id": s.suggested_prerequisite_id,
                "reason": s.reason,
                "evidence": s.evidence,
                "confidence": s.confidence,
                "status": s.status,
            }
            for s in saved
        ],
        "skipped_due_to_cycle": skipped_cycles,
    }


@router.get("/{task_id}/suggestions")
def list_suggestions(task_id: int, db: Session = Depends(get_db)):
    suggestions = db.query(AISuggestion).filter(AISuggestion.task_id == task_id).all()
    return [
        {
            "id": s.id,
            "suggested_prerequisite_id": s.suggested_prerequisite_id,
            "reason": s.reason,
            "evidence": s.evidence,
            "confidence": s.confidence,
            "provider": s.provider,
            "status": s.status,
        }
        for s in suggestions
    ]


@router.post("/suggestions/{suggestion_id}/approve", response_model=DependencyOut)
def approve_suggestion(suggestion_id: int, db: Session = Depends(get_db)):
    suggestion = db.query(AISuggestion).filter(AISuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if suggestion.status != "pending":
        raise HTTPException(
            status_code=400, detail=f"Suggestion already {suggestion.status}"
        )

    # Check if this dependency already exists (e.g. added manually earlier,
    # or via another suggestion) -- approving should just confirm it, not crash.
    existing = (
        db.query(Dependency)
        .filter(
            Dependency.task_id == suggestion.task_id,
            Dependency.prerequisite_id == suggestion.suggested_prerequisite_id,
        )
        .first()
    )
    if existing:
        suggestion.status = "approved"
        db.commit()
        return existing

    graph = {}
    for dep in db.query(Dependency).all():
        graph.setdefault(dep.task_id, []).append(dep.prerequisite_id)

    if would_create_cycle(
        graph, suggestion.task_id, suggestion.suggested_prerequisite_id
    ):
        suggestion.status = "rejected"
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="Approving this would now create a cycle -- suggestion auto-rejected",
        )

    dependency = Dependency(
        task_id=suggestion.task_id,
        prerequisite_id=suggestion.suggested_prerequisite_id,
    )
    db.add(dependency)
    suggestion.status = "approved"
    db.commit()
    db.refresh(dependency)
    return dependency


@router.post("/suggestions/{suggestion_id}/reject")
def reject_suggestion(suggestion_id: int, db: Session = Depends(get_db)):
    suggestion = db.query(AISuggestion).filter(AISuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    suggestion.status = "rejected"
    db.commit()
    return {"id": suggestion.id, "status": "rejected"}
