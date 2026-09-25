"""
Blocked/Ready status -- computed live from the graph, never stored.

Rule: a task is READY if ALL of its prerequisites are in the "done"
column. A task with NO prerequisites is always Ready (nothing blocking it).
If even ONE prerequisite is not done, the task is BLOCKED.

This must also handle transitive rollback: if a task deep in the chain
moves back to a non-done column, everything downstream that (transitively)
depends on it must become Blocked again -- because Blocked/Ready is
recomputed from current state every time, not cached.
"""

from app.engine.status import compute_status


def make_columns(**kwargs):
    """kwargs: task_id=column_name pairs, e.g. make_columns(1='done', 2='in_progress')"""
    return kwargs


def test_task_with_no_prerequisites_is_ready():
    columns = {1: "backlog"}
    graph = {}
    result = compute_status(columns, graph)
    assert result[1] == "ready"


def test_task_with_done_prerequisite_is_ready():
    columns = {1: "done", 2: "backlog"}
    graph = {2: [1]}
    result = compute_status(columns, graph)
    assert result[2] == "ready"


def test_task_with_undone_prerequisite_is_blocked():
    columns = {1: "in_progress", 2: "backlog"}
    graph = {2: [1]}
    result = compute_status(columns, graph)
    assert result[2] == "blocked"


def test_task_needs_all_prerequisites_done():
    # 3 depends on both 1 and 2. Only 1 is done -- still blocked.
    columns = {1: "done", 2: "in_progress", 3: "backlog"}
    graph = {3: [1, 2]}
    result = compute_status(columns, graph)
    assert result[3] == "blocked"


def test_all_prerequisites_done_makes_task_ready():
    columns = {1: "done", 2: "done", 3: "backlog"}
    graph = {3: [1, 2]}
    result = compute_status(columns, graph)
    assert result[3] == "ready"


def test_rollback_regression_cascades_transitively():
    # Chain: 1 -> (dep) 2 -> (dep) 3, i.e. graph = {2: [1], 3: [2]}
    # All done initially -> all ready. Then task 1 regresses to in_progress.
    # Task 2 must become blocked (direct prereq not done).
    # Task 3 must ALSO become blocked, even though its DIRECT prereq (2)
    # is still marked "done" in the columns dict -- because status must be
    # computed from the CURRENT recursive done-ness of the whole chain,
    # not just the immediate prerequisite's column label.
    columns = {1: "in_progress", 2: "done", 3: "done"}
    graph = {2: [1], 3: [2]}
    result = compute_status(columns, graph)
    assert result[2] == "blocked"
    assert result[3] == "blocked"


def test_diamond_all_paths_must_clear():
    # 4 depends on both 2 and 3, which both depend on 1.
    # 1 regresses -> 2 and 3 become blocked -> 4 must also be blocked,
    # even though 2 and 3's own column might still say "done" (stale label).
    columns = {1: "in_progress", 2: "done", 3: "done", 4: "backlog"}
    graph = {2: [1], 3: [1], 4: [2, 3]}
    result = compute_status(columns, graph)
    assert result[2] == "blocked"
    assert result[3] == "blocked"
    assert result[4] == "blocked"


def test_done_task_itself_has_no_status_conflict():
    # A task that is itself "done" -- status computation still applies to
    # it (e.g. for consistency checks), and since done implies its own
    # prerequisites were satisfied at the time, but we still report based
    # on current state.
    columns = {1: "done"}
    graph = {}
    result = compute_status(columns, graph)
    assert result[1] == "ready"
