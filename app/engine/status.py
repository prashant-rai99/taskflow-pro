"""
Blocked/Ready status -- computed live from the graph, never stored.

Rule: a task is READY only if it is "effectively done" is NOT required
for itself, but ALL of its prerequisites must be "effectively done".
A task with no prerequisites is always Ready.

Key idea (this is what makes rollback-on-regression work automatically):
a task is "effectively done" only if:
  (a) its own column label is "done", AND
  (b) all of ITS prerequisites are also "effectively done" (recursive).

So if a deep prerequisite regresses, the "effectively done" status
breaks and cascades upward through every dependent task -- even if
their own column label still says "done". We never trust a stored
label in isolation; we always recompute from the graph.
"""

from typing import Dict, List

DONE_COLUMN = "done"


def _is_effectively_done(
    task_id: int,
    columns: Dict[int, str],
    graph: Dict[int, List[int]],
    memo: Dict[int, bool],
) -> bool:
    if task_id in memo:
        return memo[task_id]

    # Own label must say done...
    if columns.get(task_id) != DONE_COLUMN:
        memo[task_id] = False
        return False

    # ...AND every prerequisite must also be effectively done (recursive).
    for prereq_id in graph.get(task_id, []):
        if not _is_effectively_done(prereq_id, columns, graph, memo):
            memo[task_id] = False
            return False

    memo[task_id] = True
    return True


def compute_status(
    columns: Dict[int, str],
    graph: Dict[int, List[int]],
) -> Dict[int, str]:
    memo: Dict[int, bool] = {}
    result: Dict[int, str] = {}

    for task_id in columns:
        prereq_ids = graph.get(task_id, [])

        if not prereq_ids:
            result[task_id] = "ready"
            continue

        all_prereqs_done = all(
            _is_effectively_done(prereq_id, columns, graph, memo)
            for prereq_id in prereq_ids
        )
        result[task_id] = "ready" if all_prereqs_done else "blocked"

    return result
