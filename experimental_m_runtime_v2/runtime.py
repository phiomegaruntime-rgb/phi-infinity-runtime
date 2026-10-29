"""Independent fragment-only admission runtime v2."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from .authority import FrozenAuthority, load_frozen_authority
from .model import (
    ADMISSION_ALLOW,
    ADMISSION_BLOCK,
    ADMISSION_REOPEN,
    KIND_ATOM,
    KIND_AUTHORITY,
    KIND_CLAIM,
    KIND_DEPENDENCY,
    KIND_FREEZE,
    KIND_FRAGMENT,
    KIND_GENEALOGY,
    KIND_INFINITO,
    KIND_MACHINE,
    KIND_OUTPUT,
    KIND_RECEIPT,
    KIND_TARGET,
    AdmissionResult,
    FragmentGraph,
    FragmentNode,
    FragmentRef,
)


@dataclass(frozen=True, slots=True)
class _MachineResult:
    decision: FragmentRef
    reason: FragmentRef
    error: FragmentRef
    output: FragmentRef
    receipt: FragmentRef
    graph: FragmentGraph


class FragmentOnlyMachine:
    """Internal M-only executor; it accepts no semantic host values."""

    def __init__(self, machine_fragment: FragmentRef) -> None:
        if type(machine_fragment) is not FragmentRef:
            raise TypeError("The M machine identity must be a FragmentRef.")
        self._machine_fragment = machine_fragment

    def _run(
        self,
        graph: FragmentGraph,
        authority: FrozenAuthority,
    ) -> _MachineResult:
        if type(graph) is not FragmentGraph:
            raise TypeError("M execution requires a FragmentGraph.")
        if graph.machine != self._machine_fragment:
            raise ValueError("The graph does not authorize this M machine.")
        closed = graph.validate_closed()
        if not closed.is_closed:
            raise ValueError("M execution requires a closed FragmentGraph.")

        decision = ADMISSION_ALLOW
        reason_code = "allow"
        error_code = "none"
        for node in graph.nodes.values():
            if node.kind != KIND_CLAIM:
                continue
            support_kinds = {
                graph.nodes[edge].kind
                for edge in node.edges
                if edge in graph.nodes
            }
            if KIND_GENEALOGY not in support_kinds or KIND_DEPENDENCY not in support_kinds:
                decision = ADMISSION_REOPEN
                reason_code = "unsupported-false-sufficiency"
                error_code = "genealogy-or-dependency-frontier"
                break

        digest = hashlib.sha256(
            "|".join(
                (
                    graph.infinito.value,
                    graph.authority.value,
                    graph.target.value,
                    graph.machine.value,
                    *(item.value for item in graph.path),
                    decision.value,
                    reason_code,
                )
            ).encode("utf-8")
        ).hexdigest()
        decision_fragment = decision
        reason_fragment = FragmentRef(f"fragment:reason:{reason_code}:{digest}")
        error_fragment = FragmentRef(f"fragment:error:{error_code}:{digest}")
        receipt_fragment = FragmentRef(f"fragment:receipt:execution:{digest}")
        output_fragment = FragmentRef(f"fragment:output:{digest}")
        nodes = dict(graph.nodes)
        nodes[decision_fragment] = FragmentNode(
            decision_fragment,
            KIND_ATOM,
            (),
        )
        nodes[reason_fragment] = FragmentNode(reason_fragment, KIND_ATOM, ())
        nodes[error_fragment] = FragmentNode(error_fragment, KIND_ATOM, ())
        nodes[receipt_fragment] = FragmentNode(
            receipt_fragment,
            KIND_RECEIPT,
            tuple(dict.fromkeys((
                authority.authority_fragment,
                authority.freeze_receipt_fragment,
                authority.anti_false_sufficiency_rule,
                graph.target,
                graph.machine,
                decision_fragment,
                reason_fragment,
                error_fragment,
                *graph.path,
            ))),
        )
        nodes[output_fragment] = FragmentNode(
            output_fragment,
            KIND_OUTPUT,
            (
                graph.target,
                receipt_fragment,
                decision_fragment,
                reason_fragment,
                error_fragment,
            ),
        )
        result_root = FragmentRef(f"fragment:infinito:result:{digest}")
        nodes[result_root] = FragmentNode(
            result_root,
            KIND_INFINITO,
            tuple(nodes),
        )
        result_graph = FragmentGraph(
            infinito=result_root,
            authority=graph.authority,
            target=graph.target,
            machine=graph.machine,
            path=graph.path,
            nodes=nodes,
        )
        return _MachineResult(
            decision=decision_fragment,
            reason=reason_fragment,
            error=error_fragment,
            output=output_fragment,
            receipt=receipt_fragment,
            graph=result_graph,
        )


class AdmissionBoundary:
    """The only public v2 path capable of returning an ALLOW decision."""

    def __init__(
        self,
        authority: FrozenAuthority,
        machine: FragmentOnlyMachine,
    ) -> None:
        self._authority = authority
        self._machine = machine

    def admit(self, snapshot: object) -> AdmissionResult:
        if type(snapshot) is not FragmentGraph:
            return _diagnostic_result(
                ADMISSION_BLOCK,
                "raw-host-input",
                "raw-host-value",
            )
        precheck = self._pre_execution_closure(snapshot)
        if precheck is not None:
            return precheck

        execution = self._machine._run(snapshot, self._authority)
        postcheck = execution.graph.validate_closed()
        if not postcheck.is_closed:
            return _diagnostic_result(
                ADMISSION_BLOCK,
                "output-closure-failed",
                "non-fragment-output",
            )
        return AdmissionResult(
            decision=execution.decision,
            reason=execution.reason,
            error=execution.error,
            output=execution.output,
            receipt=execution.receipt,
            graph=execution.graph,
        )

    def _pre_execution_closure(
        self,
        graph: FragmentGraph,
    ) -> AdmissionResult | None:
        closure = graph.validate_closed()
        if not closure.is_closed:
            return _diagnostic_result(
                ADMISSION_BLOCK,
                "input-closure-failed",
                closure.reason.value,
            )
        authority = self._authority
        all_authority_refs = (
            authority.authority_fragment,
            authority.authority_hash_fragment,
            authority.semantic_hash_fragment,
            authority.runtime_hash_fragment,
            authority.freeze_receipt_fragment,
            authority.machine_fragment,
            authority.anti_false_sufficiency_rule,
            *authority.path_fragments,
        )
        if any("PENDING" in item.value for item in all_authority_refs):
            return _diagnostic_result(
                ADMISSION_BLOCK,
                "authority-pending",
                "pending-authority",
            )
        if graph.authority != authority.authority_fragment:
            return _diagnostic_result(
                ADMISSION_BLOCK,
                "authority-root-mismatch",
                "authority-not-frozen",
            )
        if graph.machine != authority.machine_fragment:
            return _diagnostic_result(
                ADMISSION_BLOCK,
                "parallel-machine-not-authorized",
                "m-machine-not-authorized",
            )
        if graph.path != authority.path_fragments:
            return _diagnostic_result(
                ADMISSION_BLOCK,
                "exact-path-mismatch",
                "path-reordered-or-redefined",
            )
        required = (
            authority.authority_fragment,
            authority.authority_hash_fragment,
            authority.semantic_hash_fragment,
            authority.runtime_hash_fragment,
            authority.freeze_receipt_fragment,
            authority.anti_false_sufficiency_rule,
            *authority.path_fragments,
        )
        if any(item not in graph.nodes for item in required):
            return _diagnostic_result(
                ADMISSION_BLOCK,
                "authority-or-rule-not-represented",
                "unrepresented-authority-or-rule",
            )
        authority_node = graph.nodes[authority.authority_fragment]
        if authority_node.kind != KIND_AUTHORITY:
            return _diagnostic_result(
                ADMISSION_BLOCK,
                "authority-kind-mismatch",
                "authority-not-fragment",
            )
        if not {
            authority.authority_hash_fragment,
            authority.semantic_hash_fragment,
            authority.runtime_hash_fragment,
            authority.freeze_receipt_fragment,
        }.issubset(authority_node.edges):
            return _diagnostic_result(
                ADMISSION_BLOCK,
                "authority-edge-mismatch",
                "forged-freeze-receipt",
            )
        freeze_node = graph.nodes[authority.freeze_receipt_fragment]
        if freeze_node.kind != KIND_FREEZE or not {
            authority.authority_fragment,
            authority.authority_hash_fragment,
            authority.semantic_hash_fragment,
            authority.runtime_hash_fragment,
        }.issubset(freeze_node.edges):
            return _diagnostic_result(
                ADMISSION_BLOCK,
                "freeze-receipt-mismatch",
                "forged-freeze-receipt",
            )
        if graph.target not in graph.nodes:
            return _diagnostic_result(
                ADMISSION_BLOCK,
                "target-not-represented",
                "target-outside-infinito",
            )
        if self._machine._machine_fragment != authority.machine_fragment:
            return _diagnostic_result(
                ADMISSION_BLOCK,
                "machine-identity-mismatch",
                "machine-not-authority-bound",
            )
        return None


def _diagnostic_result(
    decision: FragmentRef,
    reason_code: str,
    error_code: str,
) -> AdmissionResult:
    suffix = hashlib.sha256(
        f"{decision.value}:{reason_code}:{error_code}".encode("utf-8")
    ).hexdigest()
    infinito = FragmentRef(f"fragment:infinito:diagnostic:{suffix}")
    authority = FragmentRef(f"fragment:authority:diagnostic:{suffix}")
    target = FragmentRef(f"fragment:target:diagnostic:{suffix}")
    machine = FragmentRef(f"fragment:machine:diagnostic:{suffix}")
    path = (FragmentRef(f"fragment:path:diagnostic:{suffix}"),)
    reason = FragmentRef(f"fragment:reason:{reason_code}:{suffix}")
    error = FragmentRef(f"fragment:error:{error_code}:{suffix}")
    output = FragmentRef(f"fragment:output:diagnostic:{suffix}")
    receipt = FragmentRef(f"fragment:receipt:diagnostic:{suffix}")
    decision_ref = decision
    nodes: dict[FragmentRef, FragmentNode] = {
        KIND_FRAGMENT: FragmentNode(KIND_FRAGMENT, KIND_FRAGMENT, (KIND_FRAGMENT,)),
        KIND_ATOM: FragmentNode(KIND_ATOM, KIND_FRAGMENT, (KIND_ATOM,)),
        KIND_INFINITO: FragmentNode(KIND_INFINITO, KIND_FRAGMENT, (KIND_INFINITO,)),
        KIND_AUTHORITY: FragmentNode(KIND_AUTHORITY, KIND_FRAGMENT, (KIND_AUTHORITY,)),
        KIND_MACHINE: FragmentNode(KIND_MACHINE, KIND_FRAGMENT, (KIND_MACHINE,)),
        KIND_TARGET: FragmentNode(KIND_TARGET, KIND_FRAGMENT, (KIND_TARGET,)),
        KIND_RECEIPT: FragmentNode(KIND_RECEIPT, KIND_FRAGMENT, (KIND_RECEIPT,)),
        KIND_OUTPUT: FragmentNode(KIND_OUTPUT, KIND_FRAGMENT, (KIND_OUTPUT,)),
        authority: FragmentNode(authority, KIND_AUTHORITY, ()),
        target: FragmentNode(target, KIND_TARGET, ()),
        machine: FragmentNode(machine, KIND_MACHINE, ()),
        path[0]: FragmentNode(path[0], KIND_ATOM, ()),
        reason: FragmentNode(reason, KIND_ATOM, ()),
        error: FragmentNode(error, KIND_ATOM, ()),
        output: FragmentNode(
            output,
            KIND_OUTPUT,
            (target, reason, error),
        ),
        receipt: FragmentNode(
            receipt,
            KIND_RECEIPT,
            (target, reason, error),
        ),
        decision_ref: FragmentNode(
            decision_ref,
            KIND_ATOM,
            (),
        ),
    }
    nodes[infinito] = FragmentNode(
        infinito,
        KIND_INFINITO,
        tuple(nodes),
    )
    graph = FragmentGraph(
        infinito=infinito,
        authority=authority,
        target=target,
        machine=machine,
        path=path,
        nodes=nodes,
    )
    return AdmissionResult(
        decision=decision_ref,
        reason=reason,
        error=error,
        output=output,
        receipt=receipt,
        graph=graph,
    )