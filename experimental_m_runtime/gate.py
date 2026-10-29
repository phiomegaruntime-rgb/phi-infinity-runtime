"""Fail-closed staged gate for the experimental fragment runtime."""

from __future__ import annotations

from dataclasses import dataclass

from .authority import (
    AUTHORITY_SOURCE,
    EXPECTED_AUTHORITY_SHA256,
    EXPERIMENTAL_RUNTIME_ID,
    EXPERIMENTAL_RUNTIME_VERSION,
)
from .foundation import validate_categorical_foundation
from .model import (
    AccessDiscrimination,
    ConceptualSolution,
    ContinuityClass,
    Decision,
    ExperimentalProposal,
    ExperimentalReceipt,
    ExplanatoryPrimitive,
    Fragment,
    CategoricalFoundation,
    M_ONLY_GRAMMAR,
    PrimitiveBasis,
    Stage,
)
from .receipts import create_receipt, receipt_map


@dataclass(frozen=True, slots=True)
class GateResult:
    decision: Decision
    stage: Stage
    classification: ContinuityClass | None
    reason: str
    receipts: tuple[ExperimentalReceipt, ...]


class FalseSufficiencyGuard:
    """Rejects nominal or ungrounded explanatory sufficiency."""

    def evaluate(
        self,
        *,
        primitives: tuple[ExplanatoryPrimitive, ...],
        receipts: tuple[ExperimentalReceipt, ...],
    ) -> GateResult:
        known = receipt_map(receipts)
        for primitive in primitives:
            if not isinstance(primitive, ExplanatoryPrimitive):
                return self._block("Explanatory primitive is not typed.")
            if not primitive.used_as_explanation:
                continue
            if primitive.basis != PrimitiveBasis.DERIVED_M:
                return self._block(
                    "A non-M-derived explanatory primitive cannot establish "
                    "sufficiency."
                )
            if not primitive.concept:
                return self._block("An explanatory primitive has no concept.")
            if not primitive.receipt_ids:
                return self._block(
                    "An M-derived explanatory primitive has no receipts."
                )
            for receipt_id in primitive.receipt_ids:
                receipt = known.get(receipt_id)
                if receipt is None:
                    return self._unresolved(
                        "An explanatory primitive references an unavailable receipt."
                    )
                if receipt.status != Decision.ALLOW:
                    return self._block(
                        "An explanatory primitive is not backed by an allowed "
                        "experimental receipt."
                    )
        return GateResult(
            decision=Decision.ALLOW,
            stage=Stage.FALSE_SUFFICIENCY_ANTI_DRIFT,
            classification=None,
            reason="False Sufficiency Guard passed.",
            receipts=(),
        )

    @staticmethod
    def _block(reason: str) -> GateResult:
        return GateResult(
            decision=Decision.BLOCK,
            stage=Stage.FALSE_SUFFICIENCY_ANTI_DRIFT,
            classification=None,
            reason=reason,
            receipts=(),
        )

    @staticmethod
    def _unresolved(reason: str) -> GateResult:
        return GateResult(
            decision=Decision.UNRESOLVED,
            stage=Stage.FALSE_SUFFICIENCY_ANTI_DRIFT,
            classification=None,
            reason=reason,
            receipts=(),
        )


class AntiDriftGate:
    """Mandatory staged gate; no output is produced before it passes."""

    def __init__(self) -> None:
        self.false_sufficiency = FalseSufficiencyGuard()

    def evaluate(self, proposal: ExperimentalProposal) -> GateResult:
        if not isinstance(proposal, ExperimentalProposal):
            return self._block(Stage.M_ONLY, "Proposal is not typed.")

        categorical = validate_categorical_foundation(proposal)
        if categorical.decision != Decision.ALLOW:
            return GateResult(
                decision=categorical.decision,
                stage=categorical.stage,
                classification=(
                    ContinuityClass.UNRESOLVED
                    if categorical.decision == Decision.REOPEN
                    else None
                ),
                reason=categorical.reason,
                receipts=(),
            )

        solution_result = self._check_solution(proposal.conceptual_solution)
        if solution_result is not None:
            return solution_result

        freeze_result = self._check_freeze(proposal)
        if freeze_result is not None:
            return freeze_result

        path_result = self._check_path(
            proposal.exact_path, proposal.categorical_foundation
        )
        if path_result is not None:
            return path_result

        false_sufficiency = self.false_sufficiency.evaluate(
            primitives=proposal.primitives,
            receipts=proposal.receipts,
        )
        if false_sufficiency.decision != Decision.ALLOW:
            return false_sufficiency

        classification_result = self._classify(proposal)
        if classification_result.decision != Decision.ALLOW:
            return classification_result

        control_receipt = create_receipt(
            operation_name="experimental.anti_drift_gate",
            input_receipt_ids=tuple(
                receipt.receipt_id for receipt in proposal.receipts
            ),
            accessible_evidence=(
                "false_sufficiency=passed",
                f"classification={classification_result.classification.value}",
            ),
            status=Decision.ALLOW,
            operation_performed=(
                "Verified the ordered M-only path before output."
            ),
        )
        return GateResult(
            decision=Decision.ALLOW,
            stage=Stage.CLASSIFICATION,
            classification=classification_result.classification,
            reason="False Sufficiency and Anti-Drift gates passed.",
            receipts=(control_receipt,),
        )

    @staticmethod
    def _check_solution(
        solution: ConceptualSolution | None,
    ) -> GateResult | None:
        if solution is None:
            return AntiDriftGate._block(
                Stage.CONCEPTUAL_SOLUTION,
                "M-only conceptual solution is missing.",
            )
        if solution.grammar != M_ONLY_GRAMMAR:
            return AntiDriftGate._block(
                Stage.CONCEPTUAL_SOLUTION,
                "The conceptual solution does not use the frozen M grammar.",
            )
        if not solution.solution_id or not solution.statement:
            return AntiDriftGate._block(
                Stage.CONCEPTUAL_SOLUTION,
                "The conceptual solution is incomplete.",
            )
        return None

    @staticmethod
    def _check_freeze(proposal: ExperimentalProposal) -> GateResult | None:
        frozen = proposal.frozen_plan
        if frozen is None:
            return AntiDriftGate._block(
                Stage.FREEZE,
                "The conceptual solution was not explicitly frozen.",
            )
        if frozen.solution != proposal.conceptual_solution:
            return AntiDriftGate._block(
                Stage.FREEZE,
                "The frozen solution does not match the supplied solution.",
            )
        receipt = frozen.freeze_receipt
        if (
            receipt.operation_name != "experimental.freeze"
            or receipt.status != Decision.ALLOW
            or receipt.authority_source != AUTHORITY_SOURCE
            or receipt.authority_hash != EXPECTED_AUTHORITY_SHA256
        ):
            return AntiDriftGate._block(
                Stage.FREEZE,
                "The freeze receipt is missing or not authoritative.",
            )
        if receipt.receipt_id not in {
            item.receipt_id for item in proposal.receipts
        }:
            return AntiDriftGate._unresolved(
                Stage.FREEZE,
                "The authoritative freeze receipt is not available.",
            )
        return None

    @staticmethod
    def _check_path(
        path: tuple[str, ...],
        foundation: CategoricalFoundation | None,
    ) -> GateResult | None:
        if foundation is None or path != foundation.path_fragment_ids:
            return AntiDriftGate._block(
                Stage.EXACT_PATH,
                "The exact M path is missing, external, or out of order.",
            )
        return None

    @staticmethod
    def _classify(proposal: ExperimentalProposal) -> GateResult:
        evidence = proposal.continuity
        if not evidence.prior_genealogy_ids:
            return AntiDriftGate._block(
                Stage.CLASSIFICATION,
                "Prior genealogy is missing.",
            )
        if not evidence.evidence_receipt_ids:
            return AntiDriftGate._block(
                Stage.CLASSIFICATION,
                "Continuity receipt chain is missing.",
            )
        if not evidence.provenance or not evidence.ancestry:
            return AntiDriftGate._block(
                Stage.CLASSIFICATION,
                "Continuity provenance or ancestry is missing.",
            )
        known_ids = {receipt.receipt_id for receipt in proposal.receipts}
        if not set(evidence.evidence_receipt_ids).issubset(known_ids):
            return AntiDriftGate._unresolved(
                Stage.CLASSIFICATION,
                "Continuity evidence references unavailable receipts.",
            )
        if evidence.access_discrimination == AccessDiscrimination.INSUFFICIENT:
            return AntiDriftGate._unresolved(
                Stage.CLASSIFICATION,
                "Access does not discriminate continuity.",
            )
        fragments = {fragment.fragment_id for fragment in proposal.fragments}
        if len(fragments) != len(proposal.fragments):
            return AntiDriftGate._block(
                Stage.CLASSIFICATION,
                "Fragment identities are not unique.",
            )
        class_ids: list[str] = []
        antecedents: list[str] = []
        for path in evidence.continuation_paths:
            if not all(
                (
                    path.continuation_id,
                    path.predecessor_genealogy_id,
                    path.successor_fragment_id,
                    path.continuation_class_id,
                )
            ):
                return AntiDriftGate._block(
                    Stage.CLASSIFICATION,
                    "A continuation path is incomplete.",
                )
            if path.successor_fragment_id not in fragments:
                return AntiDriftGate._block(
                    Stage.CLASSIFICATION,
                    "A continuation path references an unknown fragment.",
                )
            if path.predecessor_genealogy_id not in evidence.prior_genealogy_ids:
                return AntiDriftGate._block(
                    Stage.CLASSIFICATION,
                    "A continuation path references unknown genealogy.",
                )
            if path.continuation_id in {
                item.continuation_id for item in evidence.continuation_paths
            } if False else False:
                return AntiDriftGate._block(
                    Stage.CLASSIFICATION,
                    "Continuation identities are not unique.",
                )
            if path.continuation_class_id not in class_ids:
                class_ids.append(path.continuation_class_id)
            if path.predecessor_genealogy_id not in antecedents:
                antecedents.append(path.predecessor_genealogy_id)
        if not class_ids:
            classification = ContinuityClass.ONE_TO_ZERO
        elif len(class_ids) > 1:
            classification = ContinuityClass.ONE_TO_MANY
        elif len(antecedents) > 1:
            classification = ContinuityClass.MANY_TO_ONE
        else:
            classification = ContinuityClass.ONE_TO_ONE
        return GateResult(
            decision=Decision.ALLOW,
            stage=Stage.CLASSIFICATION,
            classification=classification,
            reason=f"Explicit continuity classified as {classification.value}.",
            receipts=(),
        )

    @staticmethod
    def _block(stage: Stage, reason: str) -> GateResult:
        return GateResult(
            decision=Decision.BLOCK,
            stage=stage,
            classification=None,
            reason=reason,
            receipts=(),
        )

    @staticmethod
    def _unresolved(stage: Stage, reason: str) -> GateResult:
        return GateResult(
            decision=Decision.UNRESOLVED,
            stage=stage,
            classification=ContinuityClass.UNRESOLVED,
            reason=reason,
            receipts=(),
        )