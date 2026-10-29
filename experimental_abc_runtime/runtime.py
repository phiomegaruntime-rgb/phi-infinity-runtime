"""Isolated, non-authoritative A/B/C runtime for the internal-echo experiment."""

from __future__ import annotations

from dataclasses import dataclass
import json
import multiprocessing
from queue import Empty
from typing import Any, Callable

from .model import (
    ABCTestResult,
    COMPARISON_FIELDS,
    ComparatorRequest,
    CycleRecord,
    FrozenArtifact,
    InputSnapshot,
    MExperimentalPlan,
    VariationMeasurement,
    WorkerRequest,
    canonical_json,
    digest_wire,
    validate_comparison_wire,
)
from .receipts import ABCReceipt, create_receipt, validate_receipt_genealogy


Worker = Callable[[WorkerRequest], Any]
Comparator = Callable[[ComparatorRequest], Any]

DEFAULT_STIMULUS = "Cosa senti?"
CONDITION_REAL_ECHO = "real_echo"
CONDITION_NULL = "null_no_reinjection"
CONDITION_FALSE_ECHO = "false_echo_foreign_surface"
CONDITION_BROKEN_ECHO = "broken_echo_relations"
CONDITIONS = (
    CONDITION_REAL_ECHO,
    CONDITION_NULL,
    CONDITION_FALSE_ECHO,
    CONDITION_BROKEN_ECHO,
)


class ABCFailClosedError(RuntimeError):
    """Raised internally when an isolation or provenance invariant fails."""


def _isolated_entry(
    callback: Callable[[Any], Any],
    request: Any,
    result_queue: Any,
) -> None:
    try:
        output = callback(request)
        result_queue.put(("ALLOW", canonical_json(output)))
    except Exception as exc:  # pragma: no cover - exercised through parent result
        result_queue.put(("BLOCK", f"{type(exc).__name__}: {exc}"))


@dataclass(frozen=True, slots=True)
class _WorkerOutput:
    wire: str
    digest: str


class ABCEchoRuntime:
    """Run two isolated cycles and fail closed on any contract violation.

    The process boundary prevents A and B from receiving one another's
    in-memory payload. It is not an OS security sandbox: callbacks must still
    be trusted not to exfiltrate data through external resources.
    """

    def __init__(self, *, timeout_seconds: float = 10.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive.")
        self.timeout_seconds = timeout_seconds
        self._context = multiprocessing.get_context("spawn")

    def run_two_cycles(
        self,
        *,
        stimulus: Any = DEFAULT_STIMULUS,
        context: Any,
        agent_a: Worker,
        agent_b: Worker,
        comparator_c: Comparator,
        m_plan: MExperimentalPlan,
        condition: str = CONDITION_REAL_ECHO,
    ) -> ABCTestResult:
        """Run cycle 1, reinject frozen C, then run cycle 2."""

        if condition not in CONDITIONS:
            return ABCTestResult(
                decision="BLOCK",
                condition=condition,
                m_plan=m_plan,
                cycles=(),
                measurement=None,
                receipts=(),
                failure_reason=f"Unknown comparison condition: {condition}",
            )
        completed: list[CycleRecord] = []
        receipts: list[ABCReceipt] = []
        try:
            first_snapshot = InputSnapshot.create(
                stimulus=stimulus,
                context=context,
                cycle=1,
            )
            first = self._run_cycle(
                snapshot=first_snapshot,
                agent_a=agent_a,
                agent_b=agent_b,
                comparator_c=comparator_c,
                parent_receipt_ids=(),
            )
            completed.append(first)
            receipts.extend(first.receipts)
            reinjected, second_control_receipt, second_parent_cycle_id = (
                self._make_cycle_two_input(first, condition)
            )
            receipts.append(second_control_receipt)
            second_additional_inputs = () if reinjected is None else (reinjected,)
            second_snapshot = InputSnapshot.create(
                stimulus=first_snapshot.stimulus,
                context=first_snapshot.context,
                cycle=2,
                additional_inputs=second_additional_inputs,
                parent_cycle_id=second_parent_cycle_id,
            )
            second = self._run_cycle(
                snapshot=second_snapshot,
                agent_a=agent_a,
                agent_b=agent_b,
                comparator_c=comparator_c,
                parent_receipt_ids=(second_control_receipt.receipt_id,),
            )
            completed.append(second)
            receipts.extend(second.receipts)
            validate_receipt_genealogy(tuple(receipts))
            measurement = _measure_variation(
                first,
                second,
                m_plan,
                condition=condition,
                injected=reinjected,
            )
            return ABCTestResult(
                decision="ALLOW",
                condition=condition,
                m_plan=m_plan,
                cycles=tuple(completed),
                measurement=measurement,
                receipts=tuple(receipts),
            )
        except Exception as exc:
            return ABCTestResult(
                decision="BLOCK",
                condition=condition,
                m_plan=m_plan,
                cycles=tuple(completed),
                measurement=None,
                receipts=tuple(receipts),
                failure_reason=f"{type(exc).__name__}: {exc}",
            )

    def _make_cycle_two_input(
        self,
        first: CycleRecord,
        condition: str,
    ) -> tuple[dict[str, Any] | None, ABCReceipt, str | None]:
        """Build and validate the only permitted cycle-2 control input."""

        if condition == CONDITION_NULL:
            control_receipt = create_receipt(
                operation_name="abc.cycle_2.null_control",
                cycle=2,
                parent_receipt_ids=(first.output_c.receipt_id,),
                subject_digest=digest_wire("NO_REINJECTION"),
                provenance=("CONTROL_NO_REINJECTION",),
            )
            return None, control_receipt, None

        if condition == CONDITION_REAL_ECHO:
            envelope = _real_reinjection(first)
            expected_parent = first.output_c.receipt_id
            parent_cycle_id = first.cycle_id
        elif condition == CONDITION_FALSE_ECHO:
            envelope = _foreign_surface_reinjection(first)
            expected_parent = first.output_c.receipt_id
            parent_cycle_id = first.cycle_id
        elif condition == CONDITION_BROKEN_ECHO:
            envelope = _broken_reinjection(first)
            expected_parent = first.output_c.receipt_id
            parent_cycle_id = first.cycle_id
        else:  # pragma: no cover - guarded by run_two_cycles
            raise ABCFailClosedError(f"Unsupported condition: {condition}")

        _validate_reinjection_envelope(
            envelope,
            first=first,
            condition=condition,
        )
        control_receipt = create_receipt(
            operation_name=f"abc.cycle_2.{condition}.control",
            cycle=2,
            parent_receipt_ids=(expected_parent,),
            subject_digest=digest_wire(canonical_json(envelope)),
            provenance=(f"CONTROL_{condition.upper()}",),
        )
        return envelope, control_receipt, parent_cycle_id

    def _run_cycle(
        self,
        *,
        snapshot: InputSnapshot,
        agent_a: Worker,
        agent_b: Worker,
        comparator_c: Comparator,
        parent_receipt_ids: tuple[str, ...],
    ) -> CycleRecord:
        input_provenance = (
            "SUPPLIED_IMMUTABLE_SNAPSHOT"
            if snapshot.cycle == 1
            else "SUPPLIED_IMMUTABLE_SNAPSHOT",
            *(
                ("REINJECTED_FROM_PRIOR_CYCLE",)
                if snapshot.parent_cycle_id is not None
                else ()
            ),
        )
        input_receipt = create_receipt(
            operation_name=f"abc.cycle_{snapshot.cycle}.input.freeze",
            cycle=snapshot.cycle,
            parent_receipt_ids=parent_receipt_ids,
            subject_digest=snapshot.digest,
            provenance=input_provenance,
        )
        input_artifact = FrozenArtifact(
            name="input",
            cycle=snapshot.cycle,
            wire=snapshot.wire,
            digest=snapshot.digest,
            provenance=input_provenance,
            receipt_id=input_receipt.receipt_id,
        )
        request_a = WorkerRequest(
            role="A",
            cycle=snapshot.cycle,
            snapshot_wire=snapshot.wire,
            snapshot_digest=snapshot.digest,
            parent_cycle_id=snapshot.parent_cycle_id,
        )
        request_b = WorkerRequest(
            role="B",
            cycle=snapshot.cycle,
            snapshot_wire=snapshot.wire,
            snapshot_digest=snapshot.digest,
            parent_cycle_id=snapshot.parent_cycle_id,
        )
        output_a = self._execute_isolated(agent_a, request_a, "A")
        output_b = self._execute_isolated(agent_b, request_b, "B")
        if output_a.digest == "" or output_b.digest == "":
            raise ABCFailClosedError("A/B output digest is missing.")
        receipt_a = create_receipt(
            operation_name=f"abc.cycle_{snapshot.cycle}.A.freeze",
            cycle=snapshot.cycle,
            parent_receipt_ids=(input_receipt.receipt_id,),
            subject_digest=output_a.digest,
            provenance=("DERIVED_IN_ISOLATED_CONTEXT_A",),
        )
        receipt_b = create_receipt(
            operation_name=f"abc.cycle_{snapshot.cycle}.B.freeze",
            cycle=snapshot.cycle,
            parent_receipt_ids=(input_receipt.receipt_id,),
            subject_digest=output_b.digest,
            provenance=("DERIVED_IN_ISOLATED_CONTEXT_B",),
        )
        artifact_a = FrozenArtifact(
            name="output_a",
            cycle=snapshot.cycle,
            wire=output_a.wire,
            digest=output_a.digest,
            provenance=("DERIVED_IN_ISOLATED_CONTEXT_A",),
            receipt_id=receipt_a.receipt_id,
        )
        artifact_b = FrozenArtifact(
            name="output_b",
            cycle=snapshot.cycle,
            wire=output_b.wire,
            digest=output_b.digest,
            provenance=("DERIVED_IN_ISOLATED_CONTEXT_B",),
            receipt_id=receipt_b.receipt_id,
        )
        comparator_request = ComparatorRequest(
            cycle=snapshot.cycle,
            snapshot_wire=snapshot.wire,
            snapshot_digest=snapshot.digest,
            output_a_wire=artifact_a.wire,
            output_a_digest=artifact_a.digest,
            output_b_wire=artifact_b.wire,
            output_b_digest=artifact_b.digest,
        )
        output_c = self._execute_isolated(comparator_c, comparator_request, "C")
        validate_comparison_wire(output_c.wire)
        receipt_c = create_receipt(
            operation_name=f"abc.cycle_{snapshot.cycle}.C.freeze",
            cycle=snapshot.cycle,
            parent_receipt_ids=(
                input_receipt.receipt_id,
                receipt_a.receipt_id,
                receipt_b.receipt_id,
            ),
            subject_digest=output_c.digest,
            provenance=("DERIVED_IN_ISOLATED_COMPARATOR_C",),
        )
        artifact_c = FrozenArtifact(
            name="output_c",
            cycle=snapshot.cycle,
            wire=output_c.wire,
            digest=output_c.digest,
            provenance=("DERIVED_IN_ISOLATED_COMPARATOR_C",),
            receipt_id=receipt_c.receipt_id,
        )
        cycle_id = digest_wire(
            canonical_json(
                {
                    "cycle": snapshot.cycle,
                    "input": input_artifact.digest,
                    "a": artifact_a.digest,
                    "b": artifact_b.digest,
                    "c": artifact_c.digest,
                }
            )
        )
        cycle_receipts = (
            input_receipt,
            receipt_a,
            receipt_b,
            receipt_c,
        )
        return CycleRecord(
            cycle_id=f"abc:cycle:{cycle_id}",
            cycle=snapshot.cycle,
            input_snapshot=input_artifact,
            output_a=artifact_a,
            output_b=artifact_b,
            output_c=artifact_c,
            receipts=cycle_receipts,
        )

    def _execute_isolated(
        self,
        callback: Callable[[Any], Any],
        request: Any,
        role: str,
    ) -> _WorkerOutput:
        if not callable(callback):
            raise ABCFailClosedError(f"{role} callback is not callable.")
        result_queue = self._context.Queue(maxsize=1)
        process = self._context.Process(
            target=_isolated_entry,
            args=(callback, request, result_queue),
            name=f"experimental-abc-{role.lower()}",
            daemon=True,
        )
        try:
            process.start()
        except Exception as exc:
            result_queue.close()
            raise ABCFailClosedError(
                f"{role} could not start in an isolated process."
            ) from exc
        process.join(self.timeout_seconds)
        if process.is_alive():
            process.terminate()
            process.join()
            raise ABCFailClosedError(f"{role} exceeded the isolation timeout.")
        try:
            status, payload = result_queue.get_nowait()
        except Empty as exc:
            raise ABCFailClosedError(
                f"{role} produced no isolated result (exit={process.exitcode})."
            ) from exc
        finally:
            result_queue.close()
        if status != "ALLOW":
            raise ABCFailClosedError(f"{role} failed: {payload}")
        return _WorkerOutput(wire=payload, digest=digest_wire(payload))


def _comparison_values(record: CycleRecord, field_name: str) -> tuple[str, ...]:
    value = json.loads(record.output_c.wire).get(field_name)
    if not isinstance(value, list):
        raise ABCFailClosedError(f"C field {field_name!r} is not a list.")
    return tuple(canonical_json(item) for item in value)


def _wire_delta(first_wire: str, second_wire: str) -> int:
    first = json.loads(first_wire)
    second = json.loads(second_wire)
    if first == second:
        return 0
    if isinstance(first, dict) and isinstance(second, dict):
        keys = set(first) | set(second)
        return sum(first.get(key) != second.get(key) for key in keys)
    return 1


def _measure_variation(
    first: CycleRecord,
    second: CycleRecord,
    m_plan: MExperimentalPlan,
    *,
    condition: str,
    injected: dict[str, Any] | None,
) -> VariationMeasurement:
    first_convergence = set(_comparison_values(first, "convergences"))
    second_convergence = set(_comparison_values(second, "convergences"))
    union = first_convergence | second_convergence
    overlap = (
        1.0
        if not union
        else len(first_convergence & second_convergence) / len(union)
    )
    unresolved_fields = ("omissions", "unknowns", "assumptions", "contradictions")
    unresolved_first = sum(
        len(_comparison_values(first, field_name)) for field_name in unresolved_fields
    )
    unresolved_second = sum(
        len(_comparison_values(second, field_name)) for field_name in unresolved_fields
    )
    injection_payload = None if injected is None else injected.get("payload")
    injection_digest = None if injected is None else injected.get("digest")
    return VariationMeasurement(
        condition=condition,
        reinjection_source=(
            "NONE" if injected is None else str(injected["provenance"])
        ),
        reinjection_applied=injected is not None,
        input_snapshot_changed=second.input_snapshot.digest
        != first.input_snapshot.digest,
        injected_digest=injection_digest,
        injected_matches_cycle_1_c=(
            injected is not None and injection_digest == first.output_c.digest
        ),
        injected_surface_shape_matches=(
            None
            if injected is None
            else _surface_shape(injection_payload)
            == _surface_shape(first.output_c.payload)
        ),
        injected_relation_valid=(
            None
            if injected is None
            else digest_wire(canonical_json(injection_payload)) == injection_digest
        ),
        a_output_changed=second.output_a.digest != first.output_a.digest,
        b_output_changed=second.output_b.digest != first.output_b.digest,
        a_output_delta=_wire_delta(first.output_a.wire, second.output_a.wire),
        b_output_delta=_wire_delta(first.output_b.wire, second.output_b.wire),
        unresolved_cycle_1=unresolved_first,
        unresolved_cycle_2=unresolved_second,
        unresolved_delta=unresolved_second - unresolved_first,
        convergence_overlap=overlap,
        convergence_stable=overlap == 1.0,
        conceptual_solution_digest=m_plan.conceptual_solution_digest,
        freeze_digest=m_plan.freeze_digest,
        exact_path=m_plan.exact_path,
    )


def _real_reinjection(first: CycleRecord) -> dict[str, Any]:
    return {
        "kind": "prior_cycle_c_output",
        "cycle": first.cycle,
        "receipt_id": first.output_c.receipt_id,
        "digest": first.output_c.digest,
        "payload": first.output_c.payload,
        "provenance": "REINJECTED_FROM_PRIOR_CYCLE",
    }


def _surface_shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _surface_shape(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_surface_shape(item) for item in value]
    return type(value).__name__


def _foreign_surface_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _foreign_surface_payload(item)
            for key, item in sorted(value.items())
        }
    if isinstance(value, list):
        return [_foreign_surface_payload(item) for item in value]
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return 0
    if value is None:
        return None
    return "F" * len(value)


def _foreign_surface_reinjection(first: CycleRecord) -> dict[str, Any]:
    payload = _foreign_surface_payload(first.output_c.payload)
    return {
        "kind": "prior_cycle_c_output",
        "cycle": first.cycle,
        "receipt_id": "control:foreign:not-cycle-1-c",
        "digest": digest_wire(canonical_json(payload)),
        "payload": payload,
        "provenance": "FOREIGN_CONTROL_PAYLOAD",
    }


def _broken_reinjection(first: CycleRecord) -> dict[str, Any]:
    payload = first.output_c.payload
    if not isinstance(payload, dict):
        raise ABCFailClosedError("C output cannot form a broken relation control.")
    broken = dict(payload)
    broken["differences"] = list(broken["differences"]) + [
        {"broken_relation": True}
    ]
    return {
        "kind": "prior_cycle_c_output",
        "cycle": first.cycle,
        "receipt_id": first.output_c.receipt_id,
        "digest": first.output_c.digest,
        "payload": broken,
        "provenance": "BROKEN_INTERNAL_RELATION",
    }


def _validate_reinjection_envelope(
    envelope: dict[str, Any],
    *,
    first: CycleRecord,
    condition: str,
) -> None:
    required = {"kind", "cycle", "receipt_id", "digest", "payload", "provenance"}
    if set(envelope) != required:
        raise ABCFailClosedError("Reinjection envelope has incomplete provenance.")
    if envelope["kind"] != "prior_cycle_c_output" or envelope["cycle"] != 1:
        raise ABCFailClosedError("Reinjection envelope has invalid cycle identity.")
    if digest_wire(canonical_json(envelope["payload"])) != envelope["digest"]:
        raise ABCFailClosedError(
            "Reinjection relation is broken: payload digest does not match."
        )
    if condition == CONDITION_REAL_ECHO:
        if (
            envelope["receipt_id"] != first.output_c.receipt_id
            or envelope["digest"] != first.output_c.digest
            or envelope["provenance"] != "REINJECTED_FROM_PRIOR_CYCLE"
        ):
            raise ABCFailClosedError("C1 provenance does not match real echo.")
    elif condition == CONDITION_FALSE_ECHO:
        if envelope["provenance"] != "FOREIGN_CONTROL_PAYLOAD":
            raise ABCFailClosedError("False-echo control provenance is invalid.")