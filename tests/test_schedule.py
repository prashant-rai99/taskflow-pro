"""
Scheduling engine tests -- derived dates, no compounding.

Graph convention here matches cycle.py: adjacency = { task_id: [prerequisite_id, ...] }
Each task also has its own planned_start (date) and duration_days (int).

compute_schedule(tasks, dependencies) returns:
    { task_id: {"start": date, "end": date} }
"""

from datetime import date
from app.engine.schedule import compute_schedule


def make_task(planned_start, duration_days):
    return {"planned_start": planned_start, "duration_days": duration_days}


def test_single_task_no_dependencies():
    tasks = {1: make_task(date(2026, 1, 1), 3)}
    graph = {}
    result = compute_schedule(tasks, graph)
    assert result[1]["start"] == date(2026, 1, 1)
    assert result[1]["end"] == date(2026, 1, 4)  # 3 days: 1,2,3 -> ends day 4


def test_simple_chain_b_starts_after_a_ends():
    # A: 1 Jan, 3 days -> ends 4 Jan
    # B depends on A, B's own planned_start is 1 Jan (irrelevant, A pushes it later)
    tasks = {
        1: make_task(date(2026, 1, 1), 3),
        2: make_task(date(2026, 1, 1), 2),
    }
    graph = {2: [1]}  # task 2 depends on task 1
    result = compute_schedule(tasks, graph)
    assert result[1]["end"] == date(2026, 1, 4)
    assert result[2]["start"] == date(2026, 1, 4)
    assert result[2]["end"] == date(2026, 1, 6)


def test_own_planned_start_wins_if_later_than_prerequisites():
    # A ends 4 Jan, but B's own planned_start is 10 Jan (later) -- B should
    # start on its own planned date, not be pulled earlier by A.
    tasks = {
        1: make_task(date(2026, 1, 1), 3),
        2: make_task(date(2026, 1, 10), 2),
    }
    graph = {2: [1]}
    result = compute_schedule(tasks, graph)
    assert result[2]["start"] == date(2026, 1, 10)


def test_diamond_no_compounding():
    # A: 1 Jan, 1 day -> ends 2 Jan
    # B depends on A: 1 day -> starts 2 Jan, ends 3 Jan
    # C depends on A: 1 day -> starts 2 Jan, ends 3 Jan
    # D depends on BOTH B and C: 1 day
    # If compounding incorrectly, D might start at 4 Jan (2+1+1) via double count.
    # Correct: D starts at max(B.end, C.end) = 3 Jan, ends 4 Jan.
    tasks = {
        1: make_task(date(2026, 1, 1), 1),
        2: make_task(date(2026, 1, 1), 1),  # B
        3: make_task(date(2026, 1, 1), 1),  # C
        4: make_task(date(2026, 1, 1), 1),  # D
    }
    graph = {2: [1], 3: [1], 4: [2, 3]}
    result = compute_schedule(tasks, graph)
    assert result[4]["start"] == date(2026, 1, 3)
    assert result[4]["end"] == date(2026, 1, 4)


def test_task_a_slips_by_3_days_d_shifts_by_3_not_6():
    # Original: A ends 2 Jan, B & C end 3 Jan, D starts 3 Jan.
    # Now A slips: duration 1 -> 4 days, A ends 5 Jan.
    # B & C both shift to end 6 Jan. D must start 6 Jan (shift of +3), NOT 9 Jan (+6).
    tasks = {
        1: make_task(date(2026, 1, 1), 4),  # slipped from 1 to 4 days
        2: make_task(date(2026, 1, 1), 1),
        3: make_task(date(2026, 1, 1), 1),
        4: make_task(date(2026, 1, 1), 1),
    }
    graph = {2: [1], 3: [1], 4: [2, 3]}
    result = compute_schedule(tasks, graph)
    assert result[4]["start"] == date(2026, 1, 6)
    assert result[4]["end"] == date(2026, 1, 7)


def test_idempotent_recompute_gives_same_result():
    tasks = {
        1: make_task(date(2026, 1, 1), 2),
        2: make_task(date(2026, 1, 1), 3),
    }
    graph = {2: [1]}
    result1 = compute_schedule(tasks, graph)
    result2 = compute_schedule(tasks, graph)
    assert result1 == result2
