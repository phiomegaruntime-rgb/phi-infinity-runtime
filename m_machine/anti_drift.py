"""Mandatory anti-drift controls for substantive M conclusions.

This module is an operational boundary around the frozen M kernel.  It does
not create propositions, alter authority, infer genealogy, or repair missing
evidence.  It only decides whether a supplied conclusion may close.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from .continuity_structure import (
    AccessDiscrimination,
    ContinuityEvaluation,
    ContinuityOutcome,
)
from .receipts import DerivationReceipt


GateDecision = Literal["ALLOW", "REJECT", "UNRESOLVED"]
GateControl = Literal["CONTINUE", "REOPEN"]


class AntiDriftReasonCode(str, Enum):
    HUMAN_PRIMITIVE_NOT_DERIVED = "HUMAN_PRIMITIVE_NOT_DERIVED"
    IDENTITY_NOMINAL_BASIS = "IDENTITY_NOMINAL_BASIS"
    IDENTITY_CONTINUITY_EVIDENCE_MISSING = (
        "IDENTITY_CONTINUITY_EVIDENCE_MISSING"
    )
    IDENTITY_CLASSIFICATION_MISMATCH = "IDENTITY_CLASSIFICATION_MISMATCH"
    CESSATION_FROM_ACCESS_LOSS = "CESSATION_FROM_ACCESS_LOSS"
    BOUNDARY_GENEALOGY_MISSING = "BOUNDARY_GENEALOGY_MISSING"
    INSUFFICIENT_ACCESS_FOR_STATUS = "INSUFFICIENT_ACCESS_FOR_STATUS"
    SEQUENCE_MISSING = "SEQUENCE_MISSING"
    SEQUENCE_OUT_OF_ORDER = "SEQUENCE_OUT_OF_ORDER"
    SEQUENCE_EVIDENCE_MISSING = "SEQUENCE_EVIDENCE_MISSING"
    RECEIPT_NOT_DERIVED_M = "RECEIPT_NOT_DERIVED_M"
    GATE_INPUT_MALFORMED = "GATE_INPUT_MALFORMED"
    GATE_PASSED = "GATE_PASSED"


class DerivationPhase(str, Enum):
    M_DERIVED = "M_DERIVED"
    CONCEPTUAL_SOLUTION = "CONCEPTUAL_SOLUTION"
    FROZEN = "FROZEN"
    EXACT_PATH = "EXACT_PATH"
    EXECUTION_VERIFIED = "EXECUTION_VERIFIED"
    NUMBERS = "NUMBERS"


_PHASE_ORDER = (
    DerivationPhase.M_DERIVED,
    DerivationPhase.CONCEPTUAL_SOLUTION,
    DerivationPhase.FROZEN,
    DerivationPhase.EXACT_PATH,
    DerivationPhase.EXECUTION_VERIFIED,
    DerivationPhase.NUMBERS,
)


@dataclass(frozen=True, slots=True)
class DerivationSequence:
    """An explicit ordered sequence required before a conclusion can close."""

    completed_phases: tuple[DerivationPhase, ...]
    evidence_receipt_ids: tuple[str, ...] = ()
    frozen_authority_verified: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "completed_phases",
            tuple(DerivationPhase(item) for item in self.completed_phases),
        )
        object.__setattr__(
            self,
            "evidence_receipt_ids",
            tuple(self.evidence_receipt_ids),
        )

    def supports(self, target: DerivationPhase) -> bool:
        target = DerivationPhase(target)
        required = _PHASE_ORDER[: _PHASE_ORDER.index(target) + 1]
        return (
            self.completed_phases == required
            and bool(self.evidence_receipt_ids)
            and (
                target.value in {
                    DerivationPhase.M_DERIVED.value,
                    DerivationPhase.CONCEPTUAL_SOLUTION.value,
                }
                or self.frozen_authority_verified
            )
        )


class PrimitiveBasis(str, Enum):
    DERIVED_M = "DERIVED_M"
    REGISTERED_ACCESS = "REGISTERED_ACCESS"
    UNDECLARED = "UNDECLARED"


@dataclass(frozen=True, slots=True)
class ExplanatoryPrimitive:
    """A concept explicitly presented as an explanation input.

    A primitive is admissible only when it is either backed by DERIVED_M
    receipts or declared as supplied access.  This does not make registered
    access a conclusion and it cannot authorize identity classification.
    """

    concept: str
    derived_receipt_ids: tuple[str, ...] = ()
    registered_access_ids: tuple[str, ...] = ()
    used_as_explanation: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "derived_receipt_ids", tuple(self.derived_receipt_ids)
        )
        object.__setattr__(
            self, "registered_access_ids", tuple(self.registered_access_ids)
        )


class IdentityBasis(str, Enum):
    MECHANICAL_GENEALOGY = "MECHANICAL_GENEALOGY"
    NAME = "NAME"
    LABEL = "LABEL"
    STATE_SIMILARITY = "STATE_SIMILARITY"
    DIFFERENCE = "DIFFERENCE"
    ACCESS_LOSS = "ACCESS_LOSS"
    HUMAN_CATEGORY = "HUMAN_CATEGORY"


class ContinuityClass(str, Enum):
    ONE_TO_ONE = "1→1"
    ONE_TO_ZERO = "1→0"
    ONE_TO_MANY = "1→n"
    MANY_TO_ONE = "n→1"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class IdentityContinuityClaim:
    """A classification request that must be genealogy-derived."""

    basis: IdentityBasis
    classification: ContinuityClass
    evaluation: ContinuityEvaluation | None = None
    access_discrimination: AccessDiscrimination = (
        AccessDiscrimination.COMPLETE
    )
    inferred_from_access_loss: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "basis", IdentityBasis(self.basis))
        object.__setattr__(
            self,
            "classification",
            ContinuityClass(self.classification),
        )
        object.__setattr__(
            self,
            "access_discrimination",
            AccessDiscrimination(self.access_discrimination),
        )


@dataclass(frozen=True, slots=True)
class GateEvaluation:
    decision: GateDecision
    control: GateControl
    reason_code: AntiDriftReasonCode
    exact_reason: str
    evidence: tuple[str, ...] = ()

    @property
    def close_allowed(self) -> bool:
        return self.decision == "ALLOW" and self.control == "CONTINUE"


_STATUS_ASSERTIONS = frozenset({"PASS", "SAFE", "SAME", "DIFFERENT"})
_OUTCOME_TO_CLASS = {
    ContinuityOutcome.CONTINUOUS_TRANSFORMATION: ContinuityClass.ONE_TO_ONE,
    ContinuityOutcome.CONTINUITY_CEASED: ContinuityClass.ONE_TO_ZERO,
    ContinuityOutcome.BRANCHED_OR_NON_UNIQUE_IDENTITY: ContinuityClass.ONE_TO_MANY,
    ContinuityOutcome.FUSED_OR_COMPOSITE_CONTINUITY: ContinuityClass.MANY_TO_ONE,
    ContinuityOutcome.UNRESOLVED: ContinuityClass.UNRESOLVED,
}


def _allow(reason: str, evidence: tuple[str, ...] = ()) -> GateEvaluation:
    return GateEvaluation(
        "ALLOW",
        "CONTINUE",
        AntiDriftReasonCode.GATE_PASSED,
        reason,
        evidence,
    )


def _reject(
    code: AntiDriftReasonCode,
    reason: str,
    evidence: tuple[str, ...] = (),
) -> GateEvaluation:
    return GateEvaluation("REJECT", "REOPEN", code, reason, evidence)


def _unresolved(
    code: AntiDriftReasonCode,
    reason: str,
    evidence: tuple[str, ...] = (),
) -> GateEvaluation:
    return GateEvaluation("UNRESOLVED", "REOPEN", code, reason, evidence)


class FalseSufficiencyGuard:
    """Reject explanatory primitives that have no M or access provenance."""

    @staticmethod
    def evaluate(
        primitives: tuple[ExplanatoryPrimitive, ...] = (),
        *,
        receipts: tuple[DerivationReceipt, ...] = (),
    ) -> GateEvaluation:
        receipt_by_id = {receipt.receipt_id: receipt for receipt in receipts}
        for primitive in tuple(primitives):
            if not isinstance(primitive, ExplanatoryPrimitive):
                return _reject(
                    AntiDriftReasonCode.GATE_INPUT_MALFORMED,
                    "Every explanatory primitive must be explicit and typed.",
                )
            if not primitive.used_as_explanation:
                continue
            if not primitive.concept:
                return _reject(
                    AntiDriftReasonCode.HUMAN_PRIMITIVE_NOT_DERIVED,
                    "An explanatory primitive has no declared concept.",
                )
            if primitive.derived_receipt_ids:
                missing = tuple(
                    receipt_id
                    for receipt_id in primitive.derived_receipt_ids
                    if receipt_id not in receipt_by_id
                )
                if missing:
                    return _unresolved(
                        AntiDriftReasonCode.RECEIPT_NOT_DERIVED_M,
                        "The explanatory primitive references unavailable "
                        f"M receipts: {missing}.",
                    )
                if any(
                    receipt_by_id[receipt_id].status != "DERIVED_M"
                    for receipt_id in primitive.derived_receipt_ids
                ):
                    return _reject(
                        AntiDriftReasonCode.RECEIPT_NOT_DERIVED_M,
                        "An explanatory primitive is not backed exclusively "
                        "by DERIVED_M receipts.",
                    )
                continue
            if primitive.registered_access_ids:
                continue
            return _reject(
                AntiDriftReasonCode.HUMAN_PRIMITIVE_NOT_DERIVED,
                f"Explanatory primitive {primitive.concept!r} is neither "
                "M-derived nor registered as supplied access.",
            )
        return _allow(
            "All explanatory primitives are M-derived or explicitly "
            "registered access."
        )


class AntiDriftGate:
    """Mandatory non-generative gate before a substantive conclusion closes."""

    def __init__(self) -> None:
        self.false_sufficiency = FalseSufficiencyGuard()

    def evaluate(
        self,
        *,
        primitives: tuple[ExplanatoryPrimitive, ...] = (),
        receipts: tuple[DerivationReceipt, ...] = (),
        identity_claim: IdentityContinuityClaim | None = None,
        boundary_assumed: bool = False,
        boundary_genealogy_ids: tuple[str, ...] = (),
        status_assertion: str | None = None,
        access_discrimination: AccessDiscrimination | None = None,
        sequence: DerivationSequence | None = None,
        target_phase: DerivationPhase | None = None,
    ) -> GateEvaluation:
        primitive_result = self.false_sufficiency.evaluate(
            primitives,
            receipts=receipts,
        )
        if not primitive_result.close_allowed:
            return primitive_result

        if boundary_assumed and not tuple(boundary_genealogy_ids):
            return _reject(
                AntiDriftReasonCode.BOUNDARY_GENEALOGY_MISSING,
                "A boundary was assumed without explicit genealogy.",
            )

        if (
            access_discrimination == AccessDiscrimination.INSUFFICIENT
            and status_assertion is not None
            and status_assertion.upper() in _STATUS_ASSERTIONS
        ):
            return _reject(
                AntiDriftReasonCode.INSUFFICIENT_ACCESS_FOR_STATUS,
                "PASS/SAFE/SAME/DIFFERENT cannot close under insufficient "
                "access or discriminability.",
            )
        if access_discrimination == AccessDiscrimination.INSUFFICIENT:
            return _unresolved(
                AntiDriftReasonCode.INSUFFICIENT_ACCESS_FOR_STATUS,
                "Access or discriminability is insufficient; the conclusion "
                "must remain UNRESOLVED and reopen the missing frontier.",
            )

        if identity_claim is not None:
            identity_result = self._evaluate_identity(identity_claim)
            if not identity_result.close_allowed:
                return identity_result

        if target_phase is not None:
            if sequence is None:
                return _unresolved(
                    AntiDriftReasonCode.SEQUENCE_MISSING,
                    "A substantive conclusion requires an explicit ordered "
                    "M → solution → FREEZE → path → verification sequence.",
                )
            try:
                supported = sequence.supports(target_phase)
            except (TypeError, ValueError):
                return _reject(
                    AntiDriftReasonCode.SEQUENCE_OUT_OF_ORDER,
                    "The supplied derivation sequence is malformed or out of "
                    "order and was not repaired.",
                )
            if not supported:
                return _reject(
                    AntiDriftReasonCode.SEQUENCE_OUT_OF_ORDER,
                    "The supplied derivation sequence does not contain the "
                    "required ordered phases.",
                )
            known_receipts = {receipt.receipt_id for receipt in receipts}
            if not set(sequence.evidence_receipt_ids).issubset(known_receipts):
                return _unresolved(
                    AntiDriftReasonCode.SEQUENCE_EVIDENCE_MISSING,
                    "Sequence evidence receipts are not available in the "
                    "current M receipt set.",
                )

        return _allow(
            "No false sufficiency, nominal identity, access-loss cessation, "
            "ungrounded boundary, insufficient-access status, or sequence "
            "drift was admitted."
        )

    @staticmethod
    def _evaluate_identity(
        claim: IdentityContinuityClaim,
    ) -> GateEvaluation:
        if claim.basis != IdentityBasis.MECHANICAL_GENEALOGY:
            return _reject(
                AntiDriftReasonCode.IDENTITY_NOMINAL_BASIS,
                "Identity or continuity cannot be derived from name, label, "
                "state similarity, simple difference, access loss, or a "
                "human category.",
            )
        if claim.inferred_from_access_loss:
            return _reject(
                AntiDriftReasonCode.CESSATION_FROM_ACCESS_LOSS,
                "Loss of access cannot establish continuity cessation.",
            )
        if claim.evaluation is None:
            return _unresolved(
                AntiDriftReasonCode.IDENTITY_CONTINUITY_EVIDENCE_MISSING,
                "Mechanical genealogy evaluation is missing.",
            )
        evaluation = claim.evaluation
        if claim.access_discrimination == AccessDiscrimination.INSUFFICIENT:
            return _unresolved(
                AntiDriftReasonCode.IDENTITY_CONTINUITY_EVIDENCE_MISSING,
                "Continuity access is insufficient; no continuity class may "
                "be selected.",
            )
        if evaluation.decision == "UNRESOLVED":
            if claim.classification == ContinuityClass.UNRESOLVED:
                return _unresolved(
                    AntiDriftReasonCode.IDENTITY_CONTINUITY_EVIDENCE_MISSING,
                    "The supplied continuity evaluation is UNRESOLVED.",
                )
            return _reject(
                AntiDriftReasonCode.IDENTITY_CLASSIFICATION_MISMATCH,
                "An unresolved genealogy cannot be converted into a "
                "continuity class.",
            )
        if (
            evaluation.decision != "ALLOW"
            or evaluation.genealogy is None
            or evaluation.receipt.status != "DERIVED_M"
        ):
            return _reject(
                AntiDriftReasonCode.IDENTITY_CONTINUITY_EVIDENCE_MISSING,
                "Identity classification requires an allowed, receipt-bearing "
                "mechanical genealogy.",
            )
        expected = _OUTCOME_TO_CLASS.get(evaluation.outcome)
        if expected != claim.classification:
            return _reject(
                AntiDriftReasonCode.IDENTITY_CLASSIFICATION_MISMATCH,
                "The requested continuity class does not match the supplied "
                "mechanical genealogy outcome.",
            )
        return _allow(
            "Continuity classification is derived only from the supplied "
            "receipt-bearing mechanical genealogy."
        )

    @staticmethod
    def control_receipt(
        evaluation: GateEvaluation,
        *,
        input_receipt_ids: tuple[str, ...] = (),
    ) -> DerivationReceipt:
        status = "EXECUTION_CONTROL" if evaluation.close_allowed else "REOPEN"
        return DerivationReceipt.create(
            operation_name="m.anti_drift_gate",
            authoritative_source_file="m_machine/anti_drift.py",
            authoritative_clause="Anti-Drift Gate operational control boundary",
            input_receipt_ids=tuple(input_receipt_ids),
            accessible_evidence=(
                f"decision={evaluation.decision}",
                f"control={evaluation.control}",
                f"reason_code={evaluation.reason_code.value}",
            ),
            operation_performed="Applied the mandatory anti-drift controls.",
            resulting_difference_or_consequence=evaluation.exact_reason,
            status=status,
            implementation_source="m_machine/anti_drift.py",
            clause_id="anti-drift-gate-v1",
        )


def runtime_m_sequence(
    receipts: tuple[DerivationReceipt, ...],
) -> DerivationSequence:
    """Build the verified sequence for an already scheduled M execution."""

    if not receipts or any(receipt.status != "DERIVED_M" for receipt in receipts):
        raise ValueError(
            "A runtime M sequence requires only DERIVED_M receipts."
        )
    return DerivationSequence(
        completed_phases=(
            DerivationPhase.M_DERIVED,
            DerivationPhase.CONCEPTUAL_SOLUTION,
            DerivationPhase.FROZEN,
            DerivationPhase.EXACT_PATH,
            DerivationPhase.EXECUTION_VERIFIED,
        ),
        evidence_receipt_ids=tuple(receipt.receipt_id for receipt in receipts),
        frozen_authority_verified=True,
    )


class GatedMProposal:
    """Adapter that makes the anti-drift gate mandatory for proposals."""

    def __init__(self, guardrail: object) -> None:
        self.guardrail = guardrail
        self.gate = AntiDriftGate()

    def verify(
        self,
        proposal: object,
        *,
        primitives: tuple[ExplanatoryPrimitive, ...] = (),
        receipts: tuple[DerivationReceipt, ...] = (),
        identity_claim: IdentityContinuityClaim | None = None,
        boundary_assumed: bool = False,
        boundary_genealogy_ids: tuple[str, ...] = (),
        status_assertion: str | None = None,
        access_discrimination: AccessDiscrimination | None = None,
        sequence: DerivationSequence | None = None,
        target_phase: DerivationPhase = DerivationPhase.EXECUTION_VERIFIED,
    ):
        """Gate first; invoke the historical verifier only after ALLOW.

        The underlying guardrail decision is returned unchanged on ALLOW so
        its existing API and frozen behavior remain intact.  On gate failure,
        a GateEvaluation is returned and no proposal verification occurs.
        """

        gate_result = self.gate.evaluate(
            primitives=primitives,
            receipts=receipts,
            identity_claim=identity_claim,
            boundary_assumed=boundary_assumed,
            boundary_genealogy_ids=boundary_genealogy_ids,
            status_assertion=status_assertion,
            access_discrimination=access_discrimination,
            sequence=sequence,
            target_phase=target_phase,
        )
        if not gate_result.close_allowed:
            return gate_result
        return self.guardrail.verify(proposal)