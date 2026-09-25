"""
Property-based tests for compute_status.

Strategy: random acyclic graph (same construction pattern) + random
column assignment per task (backlog/in_progress/review/done, chosen
independently at random -- this naturally creates rollback-like
scenarios where a "done" task has a non-done ancestor).

Invariant checked: a task is "ready" if and only if ALL of its
prerequisites are "effectively done" (own column == done AND all
THEIR prerequisites are effectively done, recursively) -- verified
against a brute-force reference that just walks the full ancestor
chain without memoization tricks.
"""

from typing import Dict, List
from hypothesis import given, strategies as st, settings

from app.engine.status import compute_status

COLUMN_CHOICES = ["backlog", "in_progress", "review", "done"]


@st.composite
def status_scenario(draw):
    n = draw(st.integers(min_value=1, max_value=8))
    graph: Dict[int, List[int]] = {}
    columns: Dict[int, str] = {}

    for node in range(1, n + 1):
        columns[node] = draw(st.sampled_from(COLUMN_CHOICES))
        if node > 1:
            possible_prereqs = list(range(1, node))
            chosen = draw(
                st.lists(
                    st.sampled_from(possible_prereqs),
                    unique=True,
                    max_size=len(possible_prereqs),
                )
            )
            if chosen:
                graph[node] = chosen

    return columns, graph


def brute_force_effectively_done(task_id, columns, graph, visiting=None):
    """No memoization, recomputes the full ancestor chain every call --
    intentionally naive/slow but obviously correct."""
    if columns.get(task_id) != "done":
        return False
    for prereq_id in graph.get(task_id, []):
        if not brute_force_effectively_done(prereq_id, columns, graph):
            return False
    return True


def brute_force_compute_status(columns, graph):
    result = {}
    for task_id in columns:
        prereq_ids = graph.get(task_id, [])
        if not prereq_ids:
            result[task_id] = "ready"
            continue
        all_done = all(
            brute_force_effectively_done(p, columns, graph) for p in prereq_ids
        )
        result[task_id] = "ready" if all_done else "blocked"
    return result


@settings(max_examples=300)
@given(status_scenario())
def test_matches_brute_force_reference(data):
    columns, graph = data
    fast_result = compute_status(columns, graph)
    reference_result = brute_force_compute_status(columns, graph)
    assert fast_result == reference_result, (
        f"Mismatch on columns={columns}, graph={graph}: "
        f"fast={fast_result}, reference={reference_result}"
    )


@settings(max_examples=300)
@given(status_scenario())
def test_no_prerequisites_always_ready(data):
    columns, graph = data
    result = compute_status(columns, graph)
    for task_id in columns:
        if not graph.get(task_id):
            assert result[task_id] == "ready"
