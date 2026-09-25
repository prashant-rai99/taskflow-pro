"""
Property-based tests for compute_schedule using Hypothesis.

Strategy: generate a random acyclic graph (same construction as
test_cycle_detection_properties.py -- edges only go from higher-numbered
nodes to lower ones, so it's guaranteed acyclic) with random durations
and planned_start offsets. Then verify two invariants that must ALWAYS
hold, regardless of graph shape:

1. Every task's computed start is >= its own planned_start.
2. Every task's computed start is >= the computed end of every one of
   its direct prerequisites (the "no compounding, derived-not-accumulated"
   invariant -- this is what catches double-counting bugs).
"""

from datetime import date, timedelta
from typing import Dict, List

from hypothesis import given, strategies as st, settings

from app.engine.schedule import compute_schedule

BASE_DATE = date(2026, 1, 1)


@st.composite
def scheduling_graph(draw):
    """Build a guaranteed-acyclic graph with 1-8 nodes, each with a
    random planned_start offset (0-10 days from BASE_DATE) and a
    random duration (1-10 days)."""
    n = draw(st.integers(min_value=1, max_value=8))

    tasks: Dict[int, dict] = {}
    graph: Dict[int, List[int]] = {}

    for node in range(1, n + 1):
        offset_days = draw(st.integers(min_value=0, max_value=10))
        duration = draw(st.integers(min_value=1, max_value=10))
        tasks[node] = {
            "planned_start": BASE_DATE + timedelta(days=offset_days),
            "duration_days": duration,
        }
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

    return tasks, graph


@settings(max_examples=300)
@given(scheduling_graph())
def test_start_never_before_own_planned_start(data):
    tasks, graph = data
    result = compute_schedule(tasks, graph)
    for task_id, task in tasks.items():
        assert result[task_id]["start"] >= task["planned_start"], (
            f"Task {task_id} computed start {result[task_id]['start']} "
            f"is before its own planned_start {task['planned_start']}"
        )


@settings(max_examples=300)
@given(scheduling_graph())
def test_start_never_before_any_prerequisite_end(data):
    tasks, graph = data
    result = compute_schedule(tasks, graph)
    for task_id, prereq_ids in graph.items():
        for prereq_id in prereq_ids:
            assert result[task_id]["start"] >= result[prereq_id]["end"], (
                f"Task {task_id} starts at {result[task_id]['start']} but "
                f"prerequisite {prereq_id} doesn't end until {result[prereq_id]['end']} "
                f"-- possible compounding/double-counting bug"
            )


@settings(max_examples=300)
@given(scheduling_graph())
def test_end_equals_start_plus_duration(data):
    tasks, graph = data
    result = compute_schedule(tasks, graph)
    for task_id, task in tasks.items():
        expected_end = result[task_id]["start"] + timedelta(days=task["duration_days"])
        assert result[task_id]["end"] == expected_end


@settings(max_examples=300)
@given(scheduling_graph())
def test_recompute_is_idempotent(data):
    tasks, graph = data
    result1 = compute_schedule(tasks, graph)
    result2 = compute_schedule(tasks, graph)
    assert result1 == result2