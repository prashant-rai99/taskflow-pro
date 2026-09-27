from datetime import date
from app.engine.critical_path import compute_critical_path


def make_task(planned_start, duration_days):
    return {"planned_start": planned_start, "duration_days": duration_days}


def test_single_task_path():
    tasks = {1: make_task(date(2026, 1, 1), 3)}
    result = compute_critical_path(tasks, {})
    assert result["path"] == [1]
    assert result["total_duration_days"] == 3


def test_simple_chain():
    tasks = {1: make_task(date(2026, 1, 1), 3), 2: make_task(date(2026, 1, 1), 2)}
    graph = {2: [1]}
    result = compute_critical_path(tasks, graph)
    assert result["path"] == [1, 2]
    assert result["total_duration_days"] == 5


def test_diamond_picks_longer_branch():
    # A(3d) -> B(1d) -> D(1d); A(3d) -> C(5d) -> D(1d). Critical path goes via C.
    tasks = {
        1: make_task(date(2026, 1, 1), 3),
        2: make_task(date(2026, 1, 1), 1),
        3: make_task(date(2026, 1, 1), 5),
        4: make_task(date(2026, 1, 1), 1),
    }
    graph = {2: [1], 3: [1], 4: [2, 3]}
    result = compute_critical_path(tasks, graph)
    assert result["path"] == [1, 3, 4]
    assert result["total_duration_days"] == 9


def test_unconstrained_start_breaks_chain():
    tasks = {1: make_task(date(2026, 1, 1), 1), 2: make_task(date(2026, 6, 1), 10)}
    graph = {2: [1]}
    result = compute_critical_path(tasks, graph)
    assert result["path"] == [2]
