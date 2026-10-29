"""Separate fragment-only research gate built on the v2 admission boundary."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from experimental_m_runtime_v2 import (
    ADMISSION_ALLOW,
    ADMISSION_BLOCK,
    ADMISSION_REOPEN,
    AdmissionBoundary,
    AdmissionResult,
    FragmentGraph,
    FragmentNode,
    FragmentOnlyMachine,
    FragmentRef,
    KIND_ATOM,
    KIND_CLAIM,
    KIND_DEPENDENCY,
    KIND_FRAGMENT,
    KIND_GENEALOGY,
    KIND_INFINITO,
    load_frozen_authority,
)

from .authority import FrozenGateAuthority, load_frozen_gate_authority
from .model import (
    COUNTEREXAMPLE_MARKER,
    FALSE_SUFFICIENCY_FRAGMENT,
    GLOBAL_SCOPE_FRAGMENT,
    KIND_COUNTEREXAMPLE,
    KIND_CRITERION,
    KIND_GATE_AUTHORITY,
    KIND_PERSISTENCE,
    KIND_SCOPE,
    LOCAL_SCOPE_FRAGMENT,
    PERSISTENCE_FRAGMENT,
    REASON_ACCESS_INSUFFICIENT,
    REASON_GENERALITY_FALSIFIED,
    REASON_SUPPORTED_LOCAL,
    REASON_UNRESOLVED,
    REASON_UNSUPPORTED_FALSE_SUFFICIENCY,
    VERDICT_ACCESS_INSUFFICIENT,
    VERDICT_FALSIFIED,
    VERDICT_REOPEN,
    VERDICT_SUPPORTED_LOCAL,
    VERDICT_UNRESOLVED,
    GateResult,
)


class FalseSufficiencyGateError(RuntimeError):
    """Raised when the gate input is not a fragment graph."""


class FalseSufficiencyGeneralityGate:
    """Classify structural outcomes after one semantic traversal through v2."""

    def __init__(
        self,
        boundary: AdmissionBoundary,
        authority: FrozenGateAuthority,
    ) -> None:
        self._boundary = boundary
        self._authority = authority

    def evaluate(
        self,
        criterion: FragmentRef,
        graph: FragmentGraph,
    ) -> GateResult:
        if type(criterion) is not FragmentRef:
            raise FalseSufficiencyGateError(
                "Gate criteria must be represented by FragmentRef."
            )
        if type(graph) is not FragmentGraph:
            raise FalseSufficiencyGateError(
                "Gate input must be represented by FragmentGraph."
            )
        prepared = self._prepare_graph(criterion, graph)
        admission = self._boundary.admit(prepared)
        decision, verdict, reason = self._classify(admission)
        result_graph = self._attach_result_fragments(
            admission.graph,
            criterion,
            decision,
            verdict,
            reason,
        )
        return GateResult(
            criterion=criterion,
            verdict=verdict,
            decision=decision,
            reason=reason,
            error=admission.error,
            output=admission.output,
            receipt=admission.receipt,
            graph=result_graph,
        )

    def _prepare_graph(
        self,
        criterion: FragmentRef,
        graph: FragmentGraph,
    ) -> FragmentGraph:
        nodes = dict(graph.nodes)
        gate_authority = self._authority
        gate_refs = (
            gate_authority.authority_fragment,
            gate_authority.authority_hash_fragment,
            gate_authority.hypothesis_fragment,
            gate_authority.falsifier_fragment,
            gate_authority.hypothesis_hash_fragment,
            gate_authority.falsifier_hash_fragment,
        )
        nodes.setdefault(KIND_GATE_AUTHORITY, FragmentNode(
            KIND_GATE_AUTHORITY, KIND_FRAGMENT, (KIND_GATE_AUTHORITY,)
        ))
        nodes.setdefault(KIND_CRITERION, FragmentNode(
            KIND_CRITERION, KIND_FRAGMENT, (KIND_CRITERION,)
        ))
        nodes.setdefault(KIND_PERSISTENCE, FragmentNode(
            KIND_PERSISTENCE, KIND_FRAGMENT, (KIND_PERSISTENCE,)
        ))
        nodes.setdefault(KIND_COUNTEREXAMPLE, FragmentNode(
            KIND_COUNTEREXAMPLE, KIND_FRAGMENT, (KIND_COUNTEREXAMPLE,)
        ))
        nodes.setdefault(KIND_SCOPE, FragmentNode(
            KIND_SCOPE, KIND_FRAGMENT, (KIND_SCOPE,)
        ))
        nodes.setdefault(gate_authority.authority_fragment, FragmentNode(
            gate_authority.authority_fragment,
            KIND_GATE_AUTHORITY,
            gate_refs[1:],
        ))
        for ref in gate_refs[1:]:
            nodes.setdefault(ref, FragmentNode(ref, KIND_ATOM, ()))
        nodes.setdefault(criterion, FragmentNode(
            criterion,
            KIND_CRITERION,
            (gate_authority.hypothesis_fragment, FALSE_SUFFICIENCY_FRAGMENT),
        ))
        nodes.setdefault(PERSISTENCE_FRAGMENT, FragmentNode(
            PERSISTENCE_FRAGMENT,
            KIND_PERSISTENCE,
            (FALSE_SUFFICIENCY_FRAGMENT,),
        ))
        return self._root_graph(graph, nodes, "input")

    def _classify(
        self,
        admission: AdmissionResult,
    ) -> tuple[FragmentRef, FragmentRef, FragmentRef]:
        if admission.decision == ADMISSION_REOPEN:
            return (
                ADMISSION_REOPEN,
                VERDICT_REOPEN,
                REASON_UNSUPPORTED_FALSE_SUFFICIENCY,
            )
        if admission.decision == ADMISSION_BLOCK:
            return (
                ADMISSION_BLOCK,
                VERDICT_ACCESS_INSUFFICIENT,
                REASON_ACCESS_INSUFFICIENT,
            )
        if admission.decision == ADMISSION_ALLOW:
            if self._has_unsupported_scope_propagation(admission.graph):
                return (
                    ADMISSION_REOPEN,
                    VERDICT_REOPEN,
                    REASON_UNSUPPORTED_FALSE_SUFFICIENCY,
                )
            if self._is_structural_counterexample(admission.graph):
                return (
                    ADMISSION_ALLOW,
                    VERDICT_FALSIFIED,
                    REASON_GENERALITY_FALSIFIED,
                )
            return (
                ADMISSION_ALLOW,
                VERDICT_SUPPORTED_LOCAL,
                REASON_SUPPORTED_LOCAL,
            )
        return ADMISSION_BLOCK, VERDICT_UNRESOLVED, REASON_UNRESOLVED

    @staticmethod
    def _has_unsupported_scope_propagation(graph: FragmentGraph) -> bool:
        """Reject conclusions whose declared scope exceeds their support scope."""

        for claim in graph.nodes.values():
            if claim.kind != KIND_CLAIM:
                continue
            support_nodes = [
                graph.nodes[edge]
                for edge in claim.edges
                if edge in graph.nodes
                and graph.nodes[edge].kind in {KIND_GENEALOGY, KIND_DEPENDENCY}
            ]
            conclusion_scopes = {
                edge
                for edge in claim.edges
                if edge in graph.nodes and graph.nodes[edge].kind == KIND_SCOPE
            }
            if not conclusion_scopes:
                continue
            support_scopes = {
                edge
                for support in support_nodes
                for edge in support.edges
                if edge in graph.nodes and graph.nodes[edge].kind == KIND_SCOPE
            }
            if not conclusion_scopes.issubset(support_scopes):
                return True
        return False

    @staticmethod
    def _is_structural_counterexample(graph: FragmentGraph) -> bool:
        marker = graph.nodes.get(COUNTEREXAMPLE_MARKER)
        if marker is None or marker.kind != KIND_COUNTEREXAMPLE:
            return False
        if graph.target not in marker.edges:
            return False
        if LOCAL_SCOPE_FRAGMENT not in marker.edges:
            return False
        if GLOBAL_SCOPE_FRAGMENT in marker.edges:
            return False
        for node in graph.nodes.values():
            if node.kind != KIND_CLAIM:
                continue
            support_kinds = {
                graph.nodes[edge].kind
                for edge in node.edges
                if edge in graph.nodes
            }
            if KIND_GENEALOGY in support_kinds and KIND_DEPENDENCY in support_kinds:
                return True
        return False

    def _attach_result_fragments(
        self,
        graph: FragmentGraph,
        criterion: FragmentRef,
        decision: FragmentRef,
        verdict: FragmentRef,
        reason: FragmentRef,
    ) -> FragmentGraph:
        nodes = dict(graph.nodes)
        nodes.setdefault(decision, FragmentNode(decision, KIND_ATOM, ()))
        nodes.setdefault(verdict, FragmentNode(verdict, KIND_ATOM, ()))
        nodes.setdefault(reason, FragmentNode(reason, KIND_ATOM, ()))
        result_id = hashlib.sha256(
            "|".join((graph.infinito.value, criterion.value, verdict.value)).encode(
                "utf-8"
            )
        ).hexdigest()
        return self._root_graph(graph, nodes, f"result:{result_id}")

    @staticmethod
    def _root_graph(
        graph: FragmentGraph,
        nodes: dict[FragmentRef, FragmentNode],
        suffix: str,
    ) -> FragmentGraph:
        root = FragmentRef(f"fragment:infinito:false-sufficiency-gate:{suffix}")
        nodes[root] = FragmentNode(root, KIND_INFINITO, tuple(nodes))
        return FragmentGraph(
            infinito=root,
            authority=graph.authority,
            target=graph.target,
            machine=graph.machine,
            path=graph.path,
            nodes=nodes,
        )


def create_false_sufficiency_gate(
    repository_root: str | Path,
) -> FalseSufficiencyGeneralityGate:
    root = Path(repository_root).resolve()
    v2_authority = load_frozen_authority(root)
    gate_authority = load_frozen_gate_authority(root)
    boundary = AdmissionBoundary(
        v2_authority,
        FragmentOnlyMachine(v2_authority.machine_fragment),
    )
    return FalseSufficiencyGeneralityGate(boundary, gate_authority)