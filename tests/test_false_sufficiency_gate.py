from __future__ import annotations

from pathlib import Path

from experimental_false_sufficiency_gate import (
    COUNTEREXAMPLE_MARKER,
    FALSE_SUFFICIENCY_FRAGMENT,
    GATE_AUTHORITY_CLAIM,
    GATE_RESULT_FRAGMENT,
    GLOBAL_SCOPE_FRAGMENT,
    KIND_COUNTEREXAMPLE,
    KIND_SCOPE,
    LOCAL_SCOPE_FRAGMENT,
    PERSISTENCE_FRAGMENT,
    VERDICT_FALSIFIED,
    VERDICT_REOPEN,
    VERDICT_SUPPORTED_LOCAL,
    create_false_sufficiency_gate,
)
from experimental_false_sufficiency_gate.model import (
    COUNTEREXAMPLE_SUPPORT_FRAGMENT,
)
from experimental_m_runtime_v2 import (
    ADMISSION_ALLOW,
    ADMISSION_REOPEN,
    FragmentGraph,
    FragmentNode,
    FragmentRef,
    KIND_ATOM,
    KIND_CLAIM,
    KIND_DEPENDENCY,
    KIND_FRAGMENT,
    KIND_GENEALOGY,
    KIND_INFINITO,
    load_frozen_authority,
)


ROOT = Path(__file__).resolve().parents[1]
CRITERION = FragmentRef("fragment:criterion:gate-test")


def _base_nodes() -> dict[FragmentRef, FragmentNode]:
    authority = load_frozen_authority(ROOT)
    target = FragmentRef("fragment:target:gate-test")
    machine = authority.machine_fragment
    nodes: dict[FragmentRef, FragmentNode] = {
        KIND_FRAGMENT: FragmentNode(KIND_FRAGMENT, KIND_FRAGMENT, (KIND_FRAGMENT,)),
        KIND_ATOM: FragmentNode(KIND_ATOM, KIND_FRAGMENT, (KIND_ATOM,)),
        KIND_INFINITO: FragmentNode(KIND_INFINITO, KIND_FRAGMENT, (KIND_INFINITO,)),
        FragmentRef("kind:authority"): FragmentNode(
            FragmentRef("kind:authority"),
            KIND_FRAGMENT,
            (FragmentRef("kind:authority"),),
        ),
        FragmentRef("kind:freeze"): FragmentNode(
            FragmentRef("kind:freeze"),
            KIND_FRAGMENT,
            (FragmentRef("kind:freeze"),),
        ),
        FragmentRef("kind:machine"): FragmentNode(
            FragmentRef("kind:machine"),
            KIND_FRAGMENT,
            (FragmentRef("kind:machine"),),
        ),
        FragmentRef("kind:target"): FragmentNode(
            FragmentRef("kind:target"),
            KIND_FRAGMENT,
            (FragmentRef("kind:target"),),
        ),
        FragmentRef("kind:receipt"): FragmentNode(
            FragmentRef("kind:receipt"),
            KIND_FRAGMENT,
            (FragmentRef("kind:receipt"),),
        ),
        FragmentRef("kind:output"): FragmentNode(
            FragmentRef("kind:output"),
            KIND_FRAGMENT,
            (FragmentRef("kind:output"),),
        ),
        authority.authority_fragment: FragmentNode(
            authority.authority_fragment,
            FragmentRef("kind:authority"),
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
            FragmentRef("kind:freeze"),
            (
                authority.authority_fragment,
                authority.authority_hash_fragment,
                authority.semantic_hash_fragment,
                authority.runtime_hash_fragment,
            ),
        ),
        machine: FragmentNode(machine, FragmentRef("kind:machine"), authority.path_fragments),
        target: FragmentNode(
            target,
            FragmentRef("kind:target"),
            (
                FragmentRef("fragment:surface:gate-test"),
                FragmentRef("fragment:operator:meta:gate-test"),
            ),
        ),
        FragmentRef("fragment:surface:gate-test"): FragmentNode(
            FragmentRef("fragment:surface:gate-test"), KIND_ATOM, ()
        ),
        FragmentRef("fragment:operator:meta:gate-test"): FragmentNode(
            FragmentRef("fragment:operator:meta:gate-test"), KIND_ATOM, ()
        ),
    }
    for path_fragment in authority.path_fragments:
        nodes[path_fragment] = FragmentNode(path_fragment, KIND_ATOM, ())
    for kind in (
        KIND_CLAIM,
        KIND_GENEALOGY,
        KIND_DEPENDENCY,
        FragmentRef("kind:scope"),
        KIND_COUNTEREXAMPLE,
    ):
        nodes[kind] = FragmentNode(kind, KIND_FRAGMENT, (kind,))
    nodes[FALSE_SUFFICIENCY_FRAGMENT] = FragmentNode(
        FALSE_SUFFICIENCY_FRAGMENT, KIND_ATOM, ()
    )
    nodes[PERSISTENCE_FRAGMENT] = FragmentNode(
        PERSISTENCE_FRAGMENT, FragmentRef("kind:persistence"), ()
    )
    nodes[FragmentRef("kind:persistence")] = FragmentNode(
        FragmentRef("kind:persistence"),
        KIND_FRAGMENT,
        (FragmentRef("kind:persistence"),),
    )
    return nodes


def _graph(nodes: dict[FragmentRef, FragmentNode] | None = None) -> FragmentGraph:
    authority = load_frozen_authority(ROOT)
    all_nodes = _base_nodes()
    if nodes:
        all_nodes.update(nodes)
    infinito = FragmentRef("fragment:infinito:gate-test")
    all_nodes[infinito] = FragmentNode(infinito, KIND_INFINITO, tuple(all_nodes))
    return FragmentGraph(
        infinito=infinito,
        authority=authority.authority_fragment,
        target=FragmentRef("fragment:target:gate-test"),
        machine=authority.machine_fragment,
        path=authority.path_fragments,
        nodes=all_nodes,
    )


def _support(
    name: str,
    *,
    scope: FragmentRef | None = None,
) -> tuple[FragmentRef, FragmentRef, dict[FragmentRef, FragmentNode]]:
    genealogy = FragmentRef(f"fragment:genealogy:{name}")
    dependency = FragmentRef(f"fragment:dependency:{name}")
    nodes = {
        genealogy: FragmentNode(
            genealogy,
            KIND_GENEALOGY,
            () if scope is None else (scope,),
        ),
        dependency: FragmentNode(
            dependency,
            KIND_DEPENDENCY,
            () if scope is None else (scope,),
        ),
    }
    return genealogy, dependency, nodes


def _claim(
    ref: FragmentRef,
    edges: tuple[FragmentRef, ...],
) -> FragmentNode:
    return FragmentNode(ref, KIND_CLAIM, edges)


def _result(gate, graph: FragmentGraph):
    return gate.evaluate(CRITERION, graph)


def test_supported_closure_is_local_and_not_universal() -> None:
    result = _result(create_false_sufficiency_gate(ROOT), _graph())

    assert result.decision == ADMISSION_ALLOW
    assert result.verdict == VERDICT_SUPPORTED_LOCAL
    assert result.verdict != FragmentRef("verdict:UNIVERSAL")


def test_claim_without_genealogy_reopens() -> None:
    genealogy, dependency, support = _support("missing-genealogy")
    claim = FragmentRef("fragment:claim:missing-genealogy")
    support[claim] = _claim(claim, (dependency,))

    result = _result(create_false_sufficiency_gate(ROOT), _graph(support))

    assert result.decision == ADMISSION_REOPEN
    assert result.verdict == VERDICT_REOPEN


def test_claim_without_dependency_reopens() -> None:
    genealogy, dependency, support = _support("missing-dependency")
    claim = FragmentRef("fragment:claim:missing-dependency")
    support[claim] = _claim(claim, (genealogy,))

    result = _result(create_false_sufficiency_gate(ROOT), _graph(support))

    assert result.decision == ADMISSION_REOPEN
    assert result.verdict == VERDICT_REOPEN


def test_unsupported_false_sufficiency_rule_reopens_recursively() -> None:
    genealogy, dependency, support = _support("self-rule")
    support[FALSE_SUFFICIENCY_FRAGMENT] = _claim(
        FALSE_SUFFICIENCY_FRAGMENT,
        (genealogy,),
    )

    result = _result(create_false_sufficiency_gate(ROOT), _graph(support))

    assert result.decision == ADMISSION_REOPEN
    assert result.verdict == VERDICT_REOPEN


def test_propagation_beyond_genealogy_reopens() -> None:
    genealogy, dependency, support = _support(
        "propagation",
        scope=LOCAL_SCOPE_FRAGMENT,
    )
    support[LOCAL_SCOPE_FRAGMENT] = FragmentNode(
        LOCAL_SCOPE_FRAGMENT,
        KIND_SCOPE,
        (),
    )
    support[GLOBAL_SCOPE_FRAGMENT] = FragmentNode(
        GLOBAL_SCOPE_FRAGMENT,
        KIND_SCOPE,
        (),
    )
    claim = FragmentRef("fragment:claim:global-propagation")
    support[claim] = _claim(
        claim,
        (genealogy, dependency, GLOBAL_SCOPE_FRAGMENT),
    )

    result = _result(create_false_sufficiency_gate(ROOT), _graph(support))

    assert result.decision == ADMISSION_REOPEN
    assert result.verdict == VERDICT_REOPEN


def test_supported_structural_counterexample_is_falsified() -> None:
    genealogy, dependency, support = _support("counterexample")
    support[LOCAL_SCOPE_FRAGMENT] = FragmentNode(
        LOCAL_SCOPE_FRAGMENT,
        KIND_SCOPE,
        (),
    )
    support[COUNTEREXAMPLE_MARKER] = FragmentNode(
        COUNTEREXAMPLE_MARKER,
        KIND_COUNTEREXAMPLE,
        (FragmentRef("fragment:target:gate-test"), LOCAL_SCOPE_FRAGMENT),
    )
    claim = FragmentRef("fragment:claim:counterexample")
    support[claim] = _claim(claim, (genealogy, dependency))

    result = _result(create_false_sufficiency_gate(ROOT), _graph(support))

    assert result.decision == ADMISSION_ALLOW
    assert result.verdict == VERDICT_FALSIFIED


def test_gate_test_and_falsifier_claims_are_self_checked() -> None:
    nodes: dict[FragmentRef, FragmentNode] = {}
    for name, ref in (
        ("gate-authority", GATE_AUTHORITY_CLAIM),
        ("gate-result", GATE_RESULT_FRAGMENT),
        ("falsifier", COUNTEREXAMPLE_SUPPORT_FRAGMENT),
    ):
        genealogy, dependency, support = _support(f"self-{name}")
        nodes.update(support)
        nodes[ref] = _claim(ref, (genealogy, dependency))

    result = _result(create_false_sufficiency_gate(ROOT), _graph(nodes))

    assert result.decision == ADMISSION_ALLOW
    assert result.verdict == VERDICT_SUPPORTED_LOCAL