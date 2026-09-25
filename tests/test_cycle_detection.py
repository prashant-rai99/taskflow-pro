"""
Cycle detection tests.

Rule: adding an edge (task_id depends_on prerequisite_id) must be
rejected if a path already exists from task_id back to prerequisite_id
in the OTHER direction -- i.e. if prerequisite_id is already reachable
FROM task_id. That would create a cycle.

Graph representation used by the engine (kept DB-agnostic so these
tests run with zero DB setup): a plain dict adjacency list,
{ task_id: [prerequisite_id, prerequisite_id, ...] }
"""

import pytest
from app.engine.cycle import would_create_cycle


def test_empty_graph_allows_any_edge():
    graph = {}
    assert would_create_cycle(graph, task_id=1, prerequisite_id=2) is False


def test_simple_chain_no_cycle():
    # B depends on A. Adding C depends on B is fine.
    graph = {2: [1]}  # task 2 depends on task 1
    assert would_create_cycle(graph, task_id=3, prerequisite_id=2) is False


def test_direct_reverse_edge_is_cycle():
    # A depends on B already exists (1 -> 2).
    # Now trying B depends on A (2 -> 1) must be rejected.
    graph = {1: [2]}
    assert would_create_cycle(graph, task_id=2, prerequisite_id=1) is True


def test_indirect_cycle_a_b_c_a():
    # A->B->C exists (A depends on B, B depends on C).
    # Adding C depends on A closes the loop A->B->C->A.
    graph = {1: [2], 2: [3]}
    assert would_create_cycle(graph, task_id=3, prerequisite_id=1) is True


def test_self_dependency_is_cycle():
    graph = {}
    assert would_create_cycle(graph, task_id=1, prerequisite_id=1) is True


def test_diamond_shape_is_not_a_cycle():
    # A is depended on by both B and C, and D depends on both B and C.
    # This is the diamond shape from the problem statement -- must be allowed.
    graph = {2: [1], 3: [1], 4: [2, 3]}
    # Adding another edge D depends on A directly should still be fine (no cycle)
    assert would_create_cycle(graph, task_id=4, prerequisite_id=1) is False


def test_unrelated_branch_no_false_positive():
    # Two separate chains that never touch -- must not be flagged.
    graph = {2: [1], 4: [3]}
    assert would_create_cycle(graph, task_id=2, prerequisite_id=3) is False