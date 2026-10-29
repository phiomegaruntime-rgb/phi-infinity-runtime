from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from experimental_m_runtime_v2 import (
    ADMISSION_ALLOW,
    ADMISSION_BLOCK,
    AdmissionBoundary,
    FragmentGraph,
    FragmentNode,
    FragmentOnlyMachine,
    FragmentRef,
    FrozenAuthority,
    KIND_ATOM,
    KIND_AUTHORITY,
    KIND_FREEZE,
    KIND_FRAGMENT,
    KIND_INFINITO,
    KIND_MACHINE,
    KIND_OUTPUT,
    KIND_RECEIPT,
    KIND_TARGET,
    load_frozen_authority,
)


ROOT = Path(__file__).resolve().parents[1]


def ref(value: str) -> FragmentRef:
    return FragmentRef(value)


def _base_nodes(authority: FrozenAuthority) -> dict[FragmentRef, FragmentNode]:
    target = ref("fragment:target")
    machine = authority.machine_fragment
    path_nodes = tuple(authority.path_fragments)
    surface = ref("fragment:surface:required")
    meta_operator = ref("fragment:operator:meta")

    nodes: dict[FragmentRef, FragmentNode] = {
        KIND_FRAGMENT: FragmentNode(KIND_FRAGMENT, KIND_FRAGMENT, (KIND_FRAGMENT,)),
        KIND_ATOM: FragmentNode(KIND_ATOM, KIND_FRAGMENT, (KIND_ATOM,)),
        KIND_INFINITO: FragmentNode(KIND_INFINITO, KIND_FRAGMENT, (KIND_INFINITO,)),
        KIND_AUTHORITY: FragmentNode(KIND_AUTHORITY, KIND_FRAGMENT, (KIND_AUTHORITY,)),
        KIND_FREEZE: FragmentNode(KIND_FREEZE, KIND_FRAGMENT, (KIND_FREEZE,)),
        KIND_MACHINE: FragmentNode(KIND_MACHINE, KIND_FRAGMENT, (KIND_MACHINE,)),
        KIND_TARGET: FragmentNode(KIND_TARGET, KIND_FRAGMENT, (KIND_TARGET,)),
        KIND_RECEIPT: FragmentNode(KIND_RECEIPT, KIND_FRAGMENT, (KIND_RECEIPT,)),
        KIND_OUTPUT: FragmentNode(KIND_OUTPUT, KIND_FRAGMENT, (KIND_OUTPUT,)),
        authority.authority_fragment: FragmentNode(
            authority.authority_fragment,
            KIND_AUTHORITY,
            (
                authority.authority_hash_fragment,
                authority.semantic_hash_fragment,
                authority.runtime_hash_fragment,
                authority.freeze_receipt_fragment,
            ),
        ),
        authority.authority_hash_fragment: FragmentNode(
            authority.authority_hash_fragment, KIND_ATOM, ()
        ),
        authority.semantic_hash_fragment: FragmentNode(
            authority.semantic_hash_fragment, KIND_ATOM, ()
        ),
        authority.runtime_hash_fragment: FragmentNode(
            authority.runtime_hash_fragment, KIND_ATOM, ()
        ),
        authority.freeze_receipt_fragment: FragmentNode(
            authority.freeze_receipt_fragment,
            KIND_FREEZE,
            (
                authority.authority_fragment,
                authority.authority_hash_fragment,
                authority.semantic_hash_fragment,
                authority.runtime_hash_fragment,
            ),
        ),
        machine: FragmentNode(machine, KIND_MACHINE, path_nodes),
        target: FragmentNode(target, KIND_TARGET, (surface, meta_operator)),
        surface: FragmentNode(surface, KIND_ATOM, ()),
        meta_operator: FragmentNode(meta_operator, KIND_ATOM, ()),
    }
    for path_fragment in path_nodes:
        nodes[path_fragment] = FragmentNode(path_fragment, KIND_ATOM, ())
    return nodes


def make_graph(
    authority: FrozenAuthority,
    *,
    path: tuple[FragmentRef, ...] | None = None,
    machine: FragmentRef | None = None,
    nodes: dict[FragmentRef, FragmentNode] | None = None,
) -> FragmentGraph:
    path = authority.path_fragments if path is None else path
    machine = authority.machine_fragment if machine is None else machine
    nodes = _base_nodes(authority) if nodes is None else dict(nodes)
    target = ref("fragment:target")
    infinito = ref("fragment:infinito:input")
    nodes[infinito] = FragmentNode(
        infinito,
        KIND_INFINITO,
        tuple(nodes),
    )
    return FragmentGraph(
        infinito=infinito,
        authority=authority.authority_fragment,
        target=target,
        machine=machine,
        path=path,
        nodes=nodes,
    )


@pytest.fixture
def authority() -> FrozenAuthority:
    return load_frozen_authority(ROOT)


@pytest.fixture
def boundary(authority: FrozenAuthority) -> AdmissionBoundary:
    return AdmissionBoundary(authority, FragmentOnlyMachine(authority.machine_fragment))


def test_closed_fragment_graph_allows_and_emits_only_fragment_refs(
    boundary: AdmissionBoundary,
    authority: FrozenAuthority,
) -> None:
    result = boundary.admit(make_graph(authority))

    assert result.decision == ADMISSION_ALLOW
    assert isinstance(result.output, FragmentRef)
    assert isinstance(result.reason, FragmentRef)
    assert isinstance(result.error, FragmentRef)
    assert isinstance(result.receipt, FragmentRef)
    assert not isinstance(result.output, dict)
    assert result.graph.validate_closed().is_closed
    assert result.output in result.graph.nodes
    assert result.receipt in result.graph.nodes


def test_raw_string_and_raw_fields_cannot_reach_allow(boundary: AdmissionBoundary) -> None:
    result = boundary.admit(
        {
            "statement": "raw statement",
            "grammar": "raw grammar",
            "surface_bindings": (),
        }
    )

    assert result.decision == ADMISSION_BLOCK
    assert isinstance(result.reason, FragmentRef)
    assert isinstance(result.error, FragmentRef)


def test_missing_surface_representation_is_blocked(
    boundary: AdmissionBoundary,
    authority: FrozenAuthority,
) -> None:
    nodes = _base_nodes(authority)
    del nodes[ref("fragment:surface:required")]

    result = boundary.admit(make_graph(authority, nodes=nodes))

    assert result.decision == ADMISSION_BLOCK


def test_fake_freeze_receipt_with_arbitrary_digest_is_blocked(
    boundary: AdmissionBoundary,
    authority: FrozenAuthority,
) -> None:
    nodes = _base_nodes(authority)
    nodes[authority.authority_fragment] = FragmentNode(
        authority.authority_fragment,
        KIND_AUTHORITY,
        (
            authority.authority_hash_fragment,
            authority.semantic_hash_fragment,
            authority.runtime_hash_fragment,
            ref("receipt:fake:digest"),
        ),
    )
    nodes[ref("receipt:fake:digest")] = FragmentNode(
        ref("receipt:fake:digest"), KIND_RECEIPT, ()
    )

    result = boundary.admit(make_graph(authority, nodes=nodes))

    assert result.decision == ADMISSION_BLOCK


def test_reordered_or_redefined_path_is_blocked(
    boundary: AdmissionBoundary,
    authority: FrozenAuthority,
) -> None:
    reordered = boundary.admit(
        make_graph(authority, path=tuple(reversed(authority.path_fragments)))
    )
    redefined_path = ref("fragment:path:redefined")
    redefined = boundary.admit(
        make_graph(authority, path=(redefined_path,) + authority.path_fragments[1:])
    )

    assert reordered.decision == ADMISSION_BLOCK
    assert redefined.decision == ADMISSION_BLOCK


def test_parallel_path_without_the_authorized_m_machine_is_blocked(
    boundary: AdmissionBoundary,
    authority: FrozenAuthority,
) -> None:
    fake_machine = ref("fragment:operator:parallel-host-machine")
    nodes = _base_nodes(authority)
    nodes[fake_machine] = FragmentNode(fake_machine, KIND_MACHINE, ())

    result = boundary.admit(
        make_graph(authority, machine=fake_machine, nodes=nodes)
    )

    assert result.decision == ADMISSION_BLOCK


def test_meta_operator_missing_from_fragment_graph_is_blocked(
    boundary: AdmissionBoundary,
    authority: FrozenAuthority,
) -> None:
    nodes = _base_nodes(authority)
    del nodes[ref("fragment:operator:meta")]

    result = boundary.admit(make_graph(authority, nodes=nodes))

    assert result.decision == ADMISSION_BLOCK


def test_raw_host_object_is_blocked_before_semantic_admission(
    boundary: AdmissionBoundary,
) -> None:
    result = boundary.admit(object())

    assert result.decision == ADMISSION_BLOCK


def test_pending_authority_or_hash_cannot_reach_allow(
    authority: FrozenAuthority,
) -> None:
    pending = replace(
        authority,
        authority_hash_fragment=ref("hash:AUTHORITY_HASH_PENDING"),
        semantic_hash_fragment=ref("hash:SEMANTIC_HASH_PENDING"),
    )
    boundary = AdmissionBoundary(pending, FragmentOnlyMachine(pending.machine_fragment))

    result = boundary.admit(make_graph(pending))

    assert result.decision == ADMISSION_BLOCK


def test_admission_result_has_no_raw_semantic_output(
    boundary: AdmissionBoundary,
    authority: FrozenAuthority,
) -> None:
    result = boundary.admit(make_graph(authority))

    for value in (
        result.decision,
        result.reason,
        result.error,
        result.output,
        result.receipt,
    ):
        assert isinstance(value, FragmentRef)
    assert all(isinstance(node.ref, FragmentRef) for node in result.graph.nodes.values())
    assert all(isinstance(node.kind, FragmentRef) for node in result.graph.nodes.values())
    assert all(
        isinstance(edge, FragmentRef)
        for node in result.graph.nodes.values()
        for edge in node.edges
    )