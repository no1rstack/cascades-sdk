from cascades_sdk import flow, task
from cascades_sdk.compiler import build_dag_from_flow, canonical_json


@task
def add(a, b):
    return a + b


@task
def mul(a, b):
    return a * b


@flow
def math_flow(a, b):
    x = add(a, b)
    return mul(x, 2)


def test_build_dag_from_flow_contains_nodes_edges_and_return_node():
    dag = build_dag_from_flow(math_flow, {"a": 1, "b": 2})

    assert "nodes" in dag
    assert "edges" in dag
    assert "return_node" in dag
    assert len(dag["nodes"]) == 2
    assert len(dag["edges"]) == 1


def test_canonical_json_is_deterministic():
    dag_1 = build_dag_from_flow(math_flow, {"a": 1, "b": 2})
    dag_2 = build_dag_from_flow(math_flow, {"a": 3, "b": 4})
    assert canonical_json(dag_1) == canonical_json(dag_2)
