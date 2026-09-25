"""
Property-based tests for would_create_cycle using Hypothesis.

Strategy: generate a random small DAG (guaranteed acyclic, built by only
allowing edges from higher-numbered nodes to lower-numbered ones -- this
constructs graphs that are cycle-free by construction). Then pick a
candidate new edge and compare our fast BFS-based function against a
brute-force reference that just checks all paths.
"""

from typing import Dict, List
from hypothesis import given, strategies as st, settings

from app.engine.cycle import would_create_cycle


def brute_force_would_create_cycle(
    graph: Dict[int, List[int]], task_id: int, prerequisite_id: int
) -> bool:
    """Reference implementation: build the graph WITH the new edge added,
    then check if any node can reach itself (full cycle scan)."""
    if task_id == prerequisite_id:
        return True

    new_graph = {k: list(v) for k, v in graph.items()}
    new_graph.setdefault(task_id, []).append(prerequisite_id)

    # DFS-based cycle check across the whole graph after insertion
    def has_cycle_from(start, visiting, visited):
        if start in visiting:
            return True
        if start in visited:
            return False
        visiting.add(start)
        for neighbor in new_graph.get(start, []):
            if has_cycle_from(neighbor, visiting, visited):
                return True
        visiting.remove(start)
        visited.add(start)
        return False

    visited = set()
    for node in list(new_graph.keys()):
        if has_cycle_from(node, set(), visited):
            return True
    return False


# Nodes are small ints 1..8, so graphs stay small and tests run fast.
node_ids = st.integers(min_value=1, max_value=8)


@st.composite
def dag_and_candidate_edge(draw):
    """Build a guaranteed-acyclic graph: edges only go from a higher
    node number to a lower one (n -> m where m < n). Then draw a
    candidate (task_id, prerequisite_id) pair to test -- which may or
    may not introduce a cycle."""
    n = draw(st.integers(min_value=2, max_value=8))
    graph: Dict[int, List[int]] = {}
    for node in range(2, n + 1):
        # each node may depend on some subset of lower-numbered nodes
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

    task_id = draw(node_ids)
    prerequisite_id = draw(node_ids)
    return graph, task_id, prerequisite_id


@settings(max_examples=500)
@given(dag_and_candidate_edge())
def test_matches_brute_force_reference(data):
    graph, task_id, prerequisite_id = data
    fast_result = would_create_cycle(graph, task_id, prerequisite_id)
    reference_result = brute_force_would_create_cycle(graph, task_id, prerequisite_id)
    assert fast_result == reference_result, (
        f"Mismatch on graph={graph}, task_id={task_id}, "
        f"prerequisite_id={prerequisite_id}: "
        f"fast={fast_result}, brute_force={reference_result}"
    )
