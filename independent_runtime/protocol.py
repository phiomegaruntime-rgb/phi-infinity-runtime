from __future__ import annotations

from typing import Any

from experimental_m_runtime_v2.model import (
    KIND_ATOM,
    KIND_AUTHORITY,
    KIND_FRAGMENT,
    KIND_INFINITO,
    KIND_MACHINE,
    KIND_OUTPUT,
    KIND_RECEIPT,
    KIND_TARGET,
    FragmentGraph,
    FragmentNode,
    FragmentRef,
)


TARGET_ID = "fragment:target:numerical-step"


class FragmentProtocolError(ValueError):
    pass


_KIND_VALUES = {
    KIND_ATOM.value, KIND_AUTHORITY.value, KIND_FRAGMENT.value,
    KIND_INFINITO.value, KIND_MACHINE.value, KIND_OUTPUT.value,
    KIND_RECEIPT.value, KIND_TARGET.value,
}


def _ref(value: object) -> FragmentRef:
    if type(value) is not str or not (
        value.startswith("fragment:") or value in _KIND_VALUES
    ):
        raise FragmentProtocolError("reference is not a registered fragment ref")
    return FragmentRef(value)


def _fragment(value: object) -> FragmentRef:
    result = _ref(value)
    if not result.value.startswith("fragment:"):
        raise FragmentProtocolError("graph anchors must be fragment refs")
    return result


def decode_graph(value: object) -> FragmentGraph:
    if type(value) is not dict or set(value) != {
        "infinito", "authority", "target", "machine", "path", "nodes"
    }:
        raise FragmentProtocolError("input must be one exact fragment graph")
    if type(value["path"]) is not list or type(value["nodes"]) is not list:
        raise FragmentProtocolError("path and nodes must be fragment lists")
    nodes: dict[FragmentRef, FragmentNode] = {}
    for raw in value["nodes"]:
        if type(raw) is not dict or set(raw) != {"ref", "kind", "edges"}:
            raise FragmentProtocolError("node is not an exact fragment record")
        ref = _ref(raw["ref"])
        kind = _ref(raw["kind"])
        edges_raw = raw["edges"]
        if type(edges_raw) is not list:
            raise FragmentProtocolError("fragment edges must be a list")
        node = FragmentNode(ref, kind, tuple(_ref(item) for item in edges_raw))
        if ref in nodes:
            raise FragmentProtocolError("duplicate fragment node")
        nodes[ref] = node
    try:
        graph = FragmentGraph(
            infinito=_fragment(value["infinito"]),
            authority=_fragment(value["authority"]),
            target=_fragment(value["target"]),
            machine=_fragment(value["machine"]),
            path=tuple(_ref(item) for item in value["path"]),
            nodes=nodes,
        )
    except (TypeError, ValueError) as exc:
        raise FragmentProtocolError("invalid fragment graph") from exc
    if not graph.validate_closed().is_closed:
        raise FragmentProtocolError("fragment graph is not closed")
    return graph


def encode_graph(graph: FragmentGraph) -> dict[str, Any]:
    if type(graph) is not FragmentGraph or not graph.validate_closed().is_closed:
        raise FragmentProtocolError("output must be a closed fragment graph")
    return {
        "infinito": graph.infinito.value,
        "authority": graph.authority.value,
        "target": graph.target.value,
        "machine": graph.machine.value,
        "path": [item.value for item in graph.path],
        "nodes": [
            {
                "ref": node.ref.value,
                "kind": node.kind.value,
                "edges": [edge.value for edge in node.edges],
            }
            for node in sorted(graph.nodes.values(), key=lambda n: n.ref.value)
        ],
    }


def make_request_graph(runtime_identity: str) -> FragmentGraph:
    infinito = FragmentRef("fragment:infinito:request")
    authority = FragmentRef(f"fragment:authority:{runtime_identity}")
    target = FragmentRef(TARGET_ID)
    machine = FragmentRef(f"fragment:machine:{runtime_identity}")
    path_ref = FragmentRef("fragment:path:numerical-step")
    type_nodes = {
        ref: FragmentNode(ref, KIND_ATOM, ())
        for ref in (
            KIND_ATOM, KIND_AUTHORITY, KIND_FRAGMENT, KIND_INFINITO,
            KIND_MACHINE, KIND_OUTPUT, KIND_RECEIPT, KIND_TARGET
        )
    }
    nodes = {
        **type_nodes,
        authority: FragmentNode(authority, KIND_AUTHORITY, ()),
        target: FragmentNode(target, KIND_TARGET, ()),
        machine: FragmentNode(machine, KIND_MACHINE, ()),
        path_ref: FragmentNode(path_ref, KIND_FRAGMENT, ()),
        infinito: FragmentNode(
            infinito, KIND_INFINITO, (authority, target, machine, path_ref)
        ),
    }
    graph = FragmentGraph(
        infinito, authority, target, machine, (path_ref,), nodes
    )
    if not graph.validate_closed().is_closed:
        raise FragmentProtocolError("internal request graph construction failed")
    return graph


def make_unresolved_output(
    graph: FragmentGraph, receipt_digest: str, decision_text: str = "UNRESOLVED"
) -> FragmentGraph:
    decision = FragmentRef(f"fragment:decision:{decision_text}")
    receipt = FragmentRef(f"fragment:receipt:{receipt_digest}")
    output = FragmentRef(f"fragment:output:{receipt_digest}")
    root = FragmentRef(f"fragment:infinito:result:{receipt_digest}")
    nodes = dict(graph.nodes)
    nodes[decision] = FragmentNode(decision, KIND_ATOM, ())
    nodes[receipt] = FragmentNode(receipt, KIND_RECEIPT, (decision, graph.target))
    nodes[output] = FragmentNode(output, KIND_OUTPUT, (receipt, decision))
    nodes[root] = FragmentNode(
        root, KIND_INFINITO, (graph.infinito, graph.authority,
                              graph.target, graph.machine, output)
    )
    result = FragmentGraph(
        root, graph.authority, graph.target, graph.machine,
        graph.path + (decision, receipt, output), nodes
    )
    if not result.validate_closed().is_closed:
        raise FragmentProtocolError("internal result graph construction failed")
    return result

