"""
Scheduling engine -- derived dates, no compounding.

Core rule: a task's computed start is the max of:
  - its own planned_start
  - the computed END of every prerequisite

Dates are NEVER stored deltas or accumulated offsets -- they are
recomputed from scratch every time by walking the graph in dependency
order (topological order). This is what makes "no compounding" hold
automatically: a converging diamond (A -> B, A -> C, B -> D, C -> D)
naturally takes max(B.end, C.end) for D, never B.end + C.end or double
counting A's slip twice.

Graph convention matches cycle.py: adjacency = { task_id: [prerequisite_id, ...] }
tasks: { task_id: {"planned_start": date, "duration_days": int} }
"""

from datetime import date, timedelta
from typing import Dict, List, TypedDict


class TaskInput(TypedDict):
    planned_start: date
    duration_days: int


class ScheduleResult(TypedDict):
    start: date
    end: date


def _topological_order(
    tasks: Dict[int, TaskInput], graph: Dict[int, List[int]]
) -> List[int]:
    """Kahn's algorithm. Assumes the graph is already verified acyclic
    (cycle.py's would_create_cycle must be checked BEFORE any edge is
    persisted, so by the time we schedule, cycles are impossible)."""
    in_degree = {task_id: 0 for task_id in tasks}
    # in_degree here = number of prerequisites a task has, since we need
    # all prerequisites resolved before we can compute this task's dates.
    for task_id in tasks:
        in_degree[task_id] = len(graph.get(task_id, []))

    # reverse adjacency: for each prerequisite, which tasks depend on it
    dependents: Dict[int, List[int]] = {task_id: [] for task_id in tasks}
    for task_id, prereqs in graph.items():
        for prereq_id in prereqs:
            dependents.setdefault(prereq_id, []).append(task_id)

    queue = [task_id for task_id, deg in in_degree.items() if deg == 0]
    order = []

    while queue:
        current = queue.pop(0)
        order.append(current)
        for dependent in dependents.get(current, []):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(order) != len(tasks):
        # Should never happen if cycle prevention worked upstream.
        raise ValueError(
            "Graph contains a cycle -- cannot schedule. "
            "This indicates cycle prevention was bypassed."
        )

    return order


def compute_schedule(
    tasks: Dict[int, TaskInput],
    graph: Dict[int, List[int]],
) -> Dict[int, ScheduleResult]:
    order = _topological_order(tasks, graph)
    result: Dict[int, ScheduleResult] = {}

    for task_id in order:
        task = tasks[task_id]
        prereq_ids = graph.get(task_id, [])

        candidate_start = task["planned_start"]
        for prereq_id in prereq_ids:
            prereq_end = result[prereq_id]["end"]
            if prereq_end > candidate_start:
                candidate_start = prereq_end

        computed_start = candidate_start
        computed_end = computed_start + timedelta(days=task["duration_days"])

        result[task_id] = {"start": computed_start, "end": computed_end}

    return result
