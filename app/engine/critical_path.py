"""
Critical path -- the longest dependency chain by total duration.
Bonus feature per problem statement. Reuses schedule.py's derived
computation: walks backward from whichever task ends latest, at each
step picking the prerequisite that actually constrained the start date.
"""

from typing import Dict, List, TypedDict
from datetime import date

from app.engine.schedule import compute_schedule, TaskInput


class CriticalPathResult(TypedDict):
    path: List[int]
    total_duration_days: int
    project_end_date: date


def compute_critical_path(
    tasks: Dict[int, TaskInput], graph: Dict[int, List[int]]
) -> CriticalPathResult:
    if not tasks:
        return {"path": [], "total_duration_days": 0, "project_end_date": None}

    schedule = compute_schedule(tasks, graph)
    project_end_date = max(s["end"] for s in schedule.values())
    end_candidates = [
        tid for tid, s in schedule.items() if s["end"] == project_end_date
    ]

    def walk_back(task_id: int) -> List[int]:
        path = [task_id]
        current = task_id
        while True:
            prereqs = graph.get(current, [])
            if not prereqs:
                break
            current_start = schedule[current]["start"]
            critical_prereq = next(
                (p for p in prereqs if schedule[p]["end"] == current_start), None
            )
            if critical_prereq is None:
                break
            path.append(critical_prereq)
            current = critical_prereq
        return list(reversed(path))

    best_path = []
    for end_task in end_candidates:
        candidate = walk_back(end_task)
        if len(candidate) > len(best_path):
            best_path = candidate

    total_duration = sum(tasks[tid]["duration_days"] for tid in best_path)
    return {
        "path": best_path,
        "total_duration_days": total_duration,
        "project_end_date": project_end_date,
    }
