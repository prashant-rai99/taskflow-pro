"""
Cycle detection for the dependency graph.

Graph convention: adjacency = { task_id: [prerequisite_id, ...] }
An edge task_id -> prerequisite_id means "task_id depends on prerequisite_id"
(prerequisite_id must be Done before task_id can proceed).

Adding a NEW edge (task_id depends_on prerequisite_id) creates a cycle
if and only if prerequisite_id can already reach task_id in the
EXISTING graph -- i.e. there's already a path
prerequisite_id -> ... -> task_id.
If such a path exists, and we now also add task_id -> prerequisite_id,
we'd close a loop.

We check this with a simple BFS/DFS from prerequisite_id, walking
FORWARD along existing edges (prerequisite_id -> its own prerequisites),
looking for task_id.
"""

from typing import Dict, List


def would_create_cycle(
    graph: Dict[int, List[int]],
    task_id: int,
    prerequisite_id: int,
) -> bool:
    # Self-dependency is trivially a cycle.
    if task_id == prerequisite_id:
        return True

    # Walk forward from prerequisite_id through EXISTING edges.
    # If we can reach task_id, then prerequisite_id already (transitively)
    # depends on task_id -- adding task_id -> prerequisite_id would close the loop.
    visited = set()
    stack = [prerequisite_id]

    while stack:
        current = stack.pop()
        if current == task_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        stack.extend(graph.get(current, []))

    return False
