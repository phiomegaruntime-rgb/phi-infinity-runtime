"""Deterministic, non-generative verification of proposed M derivations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from .grounding import GroundingAncestry, GroundingRegistry, default_grounding_registry
from .mechanical_propositions import (
    ConstructorPolicy,
    FrozenPropositionTypeRegistry,
    MechanicalProposition,
    PropositionOrigin,
    PropositionStatus,
    PropositionType,
    WitnessStatus,
    default_proposition_type_registry,
)
from .mechanical_rules import default_mechanical_rule_registry
from .proof_kernel import FrozenRuleRegistry, RuleClass
from .receipts import DerivationReceipt


GuardrailStatus = Literal["ALLOW", "BLOCK", "UNRESOLVED", "REOPEN"]


class GuardrailReasonCode(str, Enum):
    AUTHORITY_DECLARATION_MISSING = "AUTHORITY_DECLARATION_MISSING"
    AUTHORITY_MISMATCH = "AUTHORITY_MISMATCH"
    CONCLUSION_ABSENT = "CONCLUSION_ABSENT"
    CONSTRUCTOR_POLICY_VIOLATION = "CONSTRUCTOR_POLICY_VIOLATION"
    GENEALOGY_REVOKED = "GENEALOGY_REVOKED"
    INFORMATION_ACCESS_MISSING = "INFORMATION_ACCESS_MISSING"
    ORIGIN_NOT_AUTHORIZED = "ORIGIN_NOT_AUTHORIZED"
    PREMISE_ABSENT = "PREMISE_ABSENT"
    PREMISE_SET_NOT_EXACT = "PREMISE_SET_NOT_EXACT"
    PREMISE_TYPE_MISMATCH = "PREMISE_TYPE_MISMATCH"
    PROPOSAL_MALFORMED = "PROPOSAL_MALFORMED"
    PROVENANCE_NOT_PRESERVABLE = "PROVENANCE_NOT_PRESERVABLE"
    RECEIPT_MISMATCH = "RECEIPT_MISMATCH"
    RECEIPT_REFERENCE_MISSING = "RECEIPT_REFERENCE_MISSING"
    REPRESENTATION_SHORTCUT = "REPRESENTATION_SHORTCUT"
    RULE_IDENTITY_MISMATCH = "RULE_IDENTITY_MISMATCH"
    RULE_NOT_REGISTERED = "RULE_NOT_REGISTERED"
    SCOPE_INCOMPATIBLE = "SCOPE_INCOMPATIBLE"
    SCOPE_MISSING = "SCOPE_MISSING"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    SCOPE_UNAUTHORIZED = "SCOPE_UNAUTHORIZED"
    SOURCE_CLAIM_UNAUTHORIZED = "SOURCE_CLAIM_UNAUTHORIZED"
    WITNESS_STATUS_INVALID = "WITNESS_STATUS_INVALID"
    VERIFICATION_PASSED = "VERIFICATION_PASSED"


@dataclass(frozen=True, slots=True)
class ProposedProposition:
    """Untrusted proposition metadata supplied for verification only."""

    proposition_id: str
    predicate_type: PropositionType
    mechanical_scope: tuple[tuple[str, str], ...]
    subject_receipt_ids: tuple[str, ...]
    proposition_status: PropositionStatus
    witness_status: WitnessStatus
    parent_receipt_ids: tuple[str, ...] = ()
    proof_genealogies: tuple[Any, ...] = ()
    origin: PropositionOrigin = PropositionOrigin.DERIVED_M
    grounding_ancestry: GroundingAncestry | None = None
    historically_valid: bool = True
    currently_applicable: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "predicate_type", PropositionType(self.predicate_type))
        object.__setattr__(
            self, "proposition_status", PropositionStatus(self.proposition_status)
        )
        object.__setattr__(
            self, "witness_status", WitnessStatus(self.witness_status)
        )
        object.__setattr__(self, "origin", PropositionOrigin(self.origin))
        object.__setattr__(self, "mechanical_scope", tuple(self.mechanical_scope))
        object.__setattr__(
            self, "subject_receipt_ids", tuple(self.subject_receipt_ids)
        )
        object.__setattr__(
            self, "parent_receipt_ids", tuple(self.parent_receipt_ids)
        )
        object.__setattr__(self, "proof_genealogies", tuple(self.proof_genealogies))

    @classmethod
    def from_proposition(
        cls, proposition: MechanicalProposition
    ) -> "ProposedProposition":
        return cls(
            proposition_id=proposition.proposition_id,
            predicate_type=proposition.predicate_type,
            mechanical_scope=proposition.mechanical_scope,
            subject_receipt_ids=proposition.subject_receipt_ids,
            proposition_status=proposition.proposition_status,
            witness_status=proposition.witness_status,
            parent_receipt_ids=proposition.parent_receipt_ids,
            proof_genealogies=proposition.proof_genealogies,
            origin=proposition.origin,
            grounding_ancestry=proposition.grounding_ancestry,
            historically_valid=proposition.historically_valid,
            currently_applicable=proposition.currently_applicable,
        )


PropositionLike = ProposedProposition | MechanicalProposition


@dataclass(frozen=True, slots=True)
class DerivationProposal:
    """An explicit user proposal; no premise discovery is performed."""

    rule_id: str | None
    premises: tuple[PropositionLike, ...]
    conclusion: PropositionLike | None
    premise_receipt_ids: tuple[str, ...] = ()
    supporting_receipts: tuple[DerivationReceipt, ...] = ()
    conclusion_receipt: DerivationReceipt | None = None
    rule_version: str | None = None
    rule_semantic_hash: str | None = None
    implementation_id: str | None = None
    implementation_hash: str | None = None
    authority_source: str | None = None
    authority_range: tuple[int, int] | None = None
    authority_range_hash: str | None = None
    missing_access_dimensions: tuple[str, ...] = ()
    shortcut_claims: tuple[str, ...] = ()
    source_claim: bool = False


@dataclass(frozen=True, slots=True)
class GuardrailDecision:
    decision: GuardrailStatus
    reason_code: GuardrailReasonCode
    exact_reason: str
    evidence: tuple[str, ...] = ()
    authority_reference: str = ""
    premise_ids: tuple[str, ...] = ()
    conclusion_id: str = ""


_CURRENT_ALLOWED_ORIGINS = {
    "M_RULE_REAL_DIFFERENCE_IMPLIES_CONSEQUENCE_EXISTENCE_V1": (
        PropositionOrigin.DERIVED_M,
    )
}

_SHORTCUT_NAMES = frozenset(
    {
        "ACCESSRECORD",
        "AMENDMENT04",
        "ASSERTION_ID",
        "CHANNEL",
        "HASH",
        "HUMAN_LABEL",
        "ID",
        "PAYLOAD",
        "POSITION",
        "SIMULATION",
        "STATISTICS",
        "TIMESTAMP",
        "TRACE_ID",
    }
)


class MGuardrail:
    """Verify explicit M derivation proposals without executing them."""

    def __init__(
        self,
        *,
        proposition_types: FrozenPropositionTypeRegistry | None = None,
        rule_registry: FrozenRuleRegistry | None = None,
        grounding_registry: GroundingRegistry | None = None,
    ) -> None:
        self.proposition_types = proposition_types or default_proposition_type_registry()
        self.rule_registry = rule_registry or default_mechanical_rule_registry()
        self.grounding_registry = grounding_registry or default_grounding_registry()

    def verify(self, proposal: DerivationProposal) -> GuardrailDecision:
        """Return exactly one decision; never infer or repair proposal data."""
        try:
            return self._verify(proposal)
        except (KeyError, TypeError, ValueError) as exc:
            return GuardrailDecision(
                "BLOCK",
                GuardrailReasonCode.PROPOSAL_MALFORMED,
                f"Proposal is malformed and was not repaired: {exc}",
            )

    def _verify(self, proposal: DerivationProposal) -> GuardrailDecision:
        if not isinstance(proposal, DerivationProposal):
            return self._block(
                GuardrailReasonCode.PROPOSAL_MALFORMED,
                "The guardrail accepts only an explicit DerivationProposal.",
            )
        if proposal.source_claim:
            return self._block(
                GuardrailReasonCode.SOURCE_CLAIM_UNAUTHORIZED,
                "The proposal claims source-level semantics, which are outside "
                "the current M authority boundary.",
            )
        shortcut = next(
            (
                item
                for item in proposal.shortcut_claims
                if str(item).upper() in _SHORTCUT_NAMES
            ),
            None,
        )
        if shortcut is not None:
            return self._block(
                GuardrailReasonCode.REPRESENTATION_SHORTCUT,
                f"Representation shortcut {shortcut!r} cannot establish a "
                "mechanical premise or conclusion.",
            )
        if not proposal.rule_id:
            return self._unresolved(
                GuardrailReasonCode.RULE_IDENTITY_MISMATCH,
                "No rule identity was declared; the proposed derivation cannot "
                "be matched to frozen mechanical authority.",
            )
        try:
            rule = self.rule_registry.get(proposal.rule_id)
        except KeyError:
            return self._block(
                GuardrailReasonCode.RULE_NOT_REGISTERED,
                f"Rule {proposal.rule_id!r} is not registered in the frozen "
                "mechanical rule registry.",
            )
        if rule.rule_class != RuleClass.MECHANICAL_INFERENCE_RULE:
            return self._block(
                GuardrailReasonCode.RULE_IDENTITY_MISMATCH,
                f"Rule {rule.rule_id!r} is not a mechanical inference rule.",
            )
        authority = (
            proposal.authority_source,
            proposal.authority_range,
            proposal.authority_range_hash,
        )
        if any(item is None for item in authority):
            return self._block(
                GuardrailReasonCode.AUTHORITY_DECLARATION_MISSING,
                "Authority source, inclusive range, and exact range hash are all "
                "required for a proposed rule application.",
            )
        if authority != (
            rule.authority_source,
            rule.authority_range,
            rule.authority_range_hash,
        ):
            return self._block(
                GuardrailReasonCode.AUTHORITY_MISMATCH,
                "The declared authority source, range, or range hash does not "
                "match the frozen rule identity.",
            )
        declared_rule_identity = (
            proposal.rule_version,
            proposal.rule_semantic_hash,
            proposal.implementation_id,
            proposal.implementation_hash,
        )
        expected_rule_identity = (
            rule.version,
            rule.semantic_specification_hash,
            rule.implementation_id,
            rule.implementation_hash,
        )
        for label, declared, expected in zip(
            ("version", "semantic hash", "implementation ID", "implementation hash"),
            declared_rule_identity,
            expected_rule_identity,
        ):
            if declared is not None and declared != expected:
                return self._block(
                    GuardrailReasonCode.RULE_IDENTITY_MISMATCH,
                    f"Declared rule {label} does not match frozen rule identity.",
                )
        expected_premise_types = tuple(
            self._schema_type(schema) for schema in rule.premise_schema
        )
        if proposal.conclusion is None:
            return self._unresolved(
                GuardrailReasonCode.CONCLUSION_ABSENT,
                "No proposed conclusion was supplied; the derivation cannot be "
                "accepted or repaired automatically.",
            )
        if len(proposal.premises) < len(expected_premise_types):
            return self._unresolved(
                GuardrailReasonCode.PREMISE_ABSENT,
                f"Expected {len(expected_premise_types)} exact premise(s), but "
                f"only {len(proposal.premises)} were supplied.",
            )
        if len(proposal.premises) > len(expected_premise_types):
            return self._block(
                GuardrailReasonCode.PREMISE_SET_NOT_EXACT,
                "Extra premises were supplied; the guardrail will not choose a "
                "proof path or silently ignore them.",
            )
        if proposal.missing_access_dimensions:
            return self._reopen(
                GuardrailReasonCode.INFORMATION_ACCESS_MISSING,
                "Required access information is missing: "
                + ", ".join(proposal.missing_access_dimensions)
                + ". The guardrail will not guess or complete it.",
            )
        premises = tuple(self._as_proposed(item) for item in proposal.premises)
        conclusion = self._as_proposed(proposal.conclusion)
        premise_ids = tuple(item.proposition_id for item in premises)
        for index, (premise, expected_type) in enumerate(
            zip(premises, expected_premise_types), start=1
        ):
            if premise.predicate_type != expected_type:
                return self._block(
                    GuardrailReasonCode.PREMISE_TYPE_MISMATCH,
                    f"Premise {index} has type {premise.predicate_type.value}, "
                    f"but the frozen rule requires {expected_type.value}.",
                    premise_ids,
                    conclusion.proposition_id,
                )
            if premise.origin not in _CURRENT_ALLOWED_ORIGINS.get(
                rule.rule_id, (PropositionOrigin.DERIVED_M,)
            ):
                return self._block(
                    GuardrailReasonCode.ORIGIN_NOT_AUTHORIZED,
                    f"Premise {index} has origin {premise.origin.value}, which is "
                    "not authorized for this current rule path.",
                    premise_ids,
                    conclusion.proposition_id,
                )
            if not premise.historically_valid or not premise.currently_applicable:
                return self._block(
                    GuardrailReasonCode.GENEALOGY_REVOKED,
                    f"Premise {index} is not historically valid and currently "
                    "applicable at the same time.",
                    premise_ids,
                    conclusion.proposition_id,
                )
            if self._ancestry_revoked(premise.grounding_ancestry):
                return self._block(
                    GuardrailReasonCode.GENEALOGY_REVOKED,
                    f"Premise {index} depends on revoked grounding ancestry.",
                    premise_ids,
                    conclusion.proposition_id,
                )
        if not proposal.premise_receipt_ids:
            return self._block(
                GuardrailReasonCode.RECEIPT_REFERENCE_MISSING,
                "Exact premise receipt references were not supplied.",
                premise_ids,
                conclusion.proposition_id,
            )
        expected_receipt_ids = tuple(
            receipt_id
            for premise in premises
            for receipt_id in premise.subject_receipt_ids
        )
        if tuple(proposal.premise_receipt_ids) != expected_receipt_ids:
            return self._block(
                GuardrailReasonCode.RECEIPT_MISMATCH,
                "Declared premise receipt references do not exactly match the "
                "premise subject receipts.",
                premise_ids,
                conclusion.proposition_id,
            )
        supporting_ids = tuple(
            receipt.receipt_id for receipt in proposal.supporting_receipts
        )
        if not set(proposal.premise_receipt_ids).issubset(supporting_ids):
            return self._block(
                GuardrailReasonCode.RECEIPT_MISMATCH,
                "The supporting receipt set does not contain every exact premise "
                "receipt reference.",
                premise_ids,
                conclusion.proposition_id,
            )
        supporting_by_id = {
            receipt.receipt_id: receipt for receipt in proposal.supporting_receipts
        }
        if any(
            supporting_by_id[item].status != "DERIVED_M"
            for item in proposal.premise_receipt_ids
        ):
            return self._block(
                GuardrailReasonCode.RECEIPT_MISMATCH,
                "A premise receipt is not a DERIVED_M receipt for this "
                "mechanical-rule proposal.",
                premise_ids,
                conclusion.proposition_id,
            )
        try:
            for item in premises + (conclusion,):
                self.proposition_types.validate_scope(
                    item.predicate_type, item.mechanical_scope
                )
        except ValueError as exc:
            code = (
                GuardrailReasonCode.SCOPE_INCOMPATIBLE
                if conclusion.predicate_type
                == PropositionType.REAL_DIFFERENCE_EXISTS
                else GuardrailReasonCode.SCOPE_UNAUTHORIZED
            )
            return self._block(
                code,
                f"An exact proposition scope is not representable by its frozen "
                f"type schema: {exc}.",
                premise_ids,
                conclusion.proposition_id,
            )
        if not conclusion.mechanical_scope:
            return self._reopen(
                GuardrailReasonCode.SCOPE_MISSING,
                "The proposed conclusion has no exact mechanical scope.",
                premise_ids,
                conclusion.proposition_id,
            )
        if any(not item.mechanical_scope for item in premises):
            return self._reopen(
                GuardrailReasonCode.SCOPE_MISSING,
                "At least one premise has no exact mechanical scope.",
                premise_ids,
                conclusion.proposition_id,
            )
        if any(
            set(self.proposition_types.get(item.predicate_type).scope_schema)
            - {name for name, _ in item.mechanical_scope}
            for item in premises + (conclusion,)
        ):
            return self._reopen(
                GuardrailReasonCode.SCOPE_MISSING,
                "A proposition scope is missing an authority-defined dimension; "
                "the guardrail will not complete it.",
                premise_ids,
                conclusion.proposition_id,
            )
        if any(item.mechanical_scope != conclusion.mechanical_scope for item in premises):
            return self._block(
                GuardrailReasonCode.SCOPE_MISMATCH,
                "Premise and conclusion scopes are not exactly identical; no scope "
                "projection or globalization is authorized.",
                premise_ids,
                conclusion.proposition_id,
            )
        if conclusion.predicate_type != self._conclusion_type(rule):
            return self._block(
                GuardrailReasonCode.PREMISE_TYPE_MISMATCH,
                f"Conclusion has type {conclusion.predicate_type.value}, but the "
                f"frozen rule requires {self._conclusion_type(rule).value}.",
                premise_ids,
                conclusion.proposition_id,
            )
        conclusion_spec = self.proposition_types.get(conclusion.predicate_type)
        if conclusion_spec.constructor_policy != ConstructorPolicy.MECHANICAL_RULE_ONLY:
            return self._block(
                GuardrailReasonCode.CONSTRUCTOR_POLICY_VIOLATION,
                "The proposed conclusion type is not constructible by a frozen "
                "mechanical rule under its current constructor policy.",
                premise_ids,
                conclusion.proposition_id,
            )
        if conclusion.origin != PropositionOrigin.DERIVED_M:
            return self._block(
                GuardrailReasonCode.ORIGIN_NOT_AUTHORIZED,
                "A mechanical inference conclusion must have origin DERIVED_M.",
                premise_ids,
                conclusion.proposition_id,
            )
        if conclusion.proposition_status != PropositionStatus.MECHANICAL_EXISTENCE_PROVED:
            return self._block(
                GuardrailReasonCode.CONSTRUCTOR_POLICY_VIOLATION,
                "The conclusion status is not MECHANICAL_EXISTENCE_PROVED.",
                premise_ids,
                conclusion.proposition_id,
            )
        if conclusion.witness_status != WitnessStatus.WITNESS_FREE:
            return self._block(
                GuardrailReasonCode.WITNESS_STATUS_INVALID,
                "The proposed mechanical conclusion constructs or claims a "
                "witness, which this rule does not authorize.",
                premise_ids,
                conclusion.proposition_id,
            )
        expected_identity = self.proposition_types.proposition_identity(
            conclusion.predicate_type,
            conclusion.mechanical_scope,
            conclusion.subject_receipt_ids,
        )
        if conclusion.proposition_id != expected_identity:
            return self._block(
                GuardrailReasonCode.RULE_IDENTITY_MISMATCH,
                "The proposed conclusion identity does not match its frozen type, "
                "exact scope, and subject receipts.",
                premise_ids,
                conclusion.proposition_id,
            )
        if conclusion.parent_receipt_ids != tuple(proposal.premise_receipt_ids):
            return self._block(
                GuardrailReasonCode.RECEIPT_MISMATCH,
                "The conclusion does not preserve the exact premise receipt "
                "references as its parent receipts.",
                premise_ids,
                conclusion.proposition_id,
            )
        if not conclusion.proof_genealogies:
            return self._block(
                GuardrailReasonCode.PROVENANCE_NOT_PRESERVABLE,
                "The proposed conclusion has no proof genealogy.",
                premise_ids,
                conclusion.proposition_id,
            )
        inherited_genealogies = tuple(
            genealogy
            for premise in premises
            for genealogy in premise.proof_genealogies
        )
        if any(
            genealogy not in conclusion.proof_genealogies
            for genealogy in inherited_genealogies
        ):
            missing_genealogies = tuple(
                genealogy
                for genealogy in inherited_genealogies
                if genealogy not in conclusion.proof_genealogies
            )
            return self._block(
                GuardrailReasonCode.PROVENANCE_NOT_PRESERVABLE,
                "The proposed conclusion does not preserve proof genealogy "
                "path(s): "
                + ", ".join(
                    self._genealogy_label(genealogy)
                    for genealogy in missing_genealogies
                )
                + ". Every independent path must remain available; silent "
                "genealogy collapse is forbidden.",
                premise_ids,
                conclusion.proposition_id,
            )
        if any(premise.grounding_ancestry is not None for premise in premises):
            if conclusion.grounding_ancestry is None:
                return self._block(
                    GuardrailReasonCode.PROVENANCE_NOT_PRESERVABLE,
                    "Grounding ancestry exists on a premise but is absent from "
                    "the proposed conclusion.",
                    premise_ids,
                    conclusion.proposition_id,
                )
            if not self._ancestry_contains(
                conclusion.grounding_ancestry,
                tuple(
                    premise.grounding_ancestry
                    for premise in premises
                    if premise.grounding_ancestry is not None
                ),
            ):
                missing_ancestry = self._missing_ancestry(
                    conclusion.grounding_ancestry,
                    tuple(
                        premise.grounding_ancestry
                        for premise in premises
                        if premise.grounding_ancestry is not None
                    ),
                )
                return self._block(
                    GuardrailReasonCode.PROVENANCE_NOT_PRESERVABLE,
                    "The proposed conclusion does not preserve the complete "
                    "grounding ancestry: "
                    + (
                        "; ".join(
                            f"{field}={','.join(values)}"
                            for field, values in missing_ancestry
                        )
                        or "the exact parent ancestry scope"
                    )
                    + ".",
                    premise_ids,
                    conclusion.proposition_id,
                )
        receipt = proposal.conclusion_receipt
        if receipt is None:
            return self._block(
                GuardrailReasonCode.RECEIPT_REFERENCE_MISSING,
                "No conclusion receipt was supplied for audit verification.",
                premise_ids,
                conclusion.proposition_id,
            )
        if (
            receipt.status != "DERIVED_M"
            or receipt.operation_name != rule.rule_id
            or receipt.authoritative_source_file != rule.authority_source
            or str(rule.authority_range_hash) not in receipt.authoritative_clause
            or not set(proposal.premise_receipt_ids).issubset(
                receipt.input_receipt_ids
            )
            or receipt.resulting_difference_or_consequence
            != conclusion.proposition_id
        ):
            return self._block(
                GuardrailReasonCode.RECEIPT_MISMATCH,
                "The conclusion receipt does not exactly identify the frozen rule, "
                "DERIVED_M status, and premise inputs.",
                premise_ids,
                conclusion.proposition_id,
            )
        return self._allow(
            "All declared authority, premise, conclusion, origin, scope, receipt, "
            "genealogy, ancestry, provenance, applicability, constructor, and "
            "witness checks passed without inference.",
            authority_reference=(
                f"{rule.authority_source}:{rule.authority_range}:"
                f"{rule.authority_range_hash}"
            ),
            premise_ids=premise_ids,
            conclusion_id=conclusion.proposition_id,
        )

    @staticmethod
    def _as_proposed(item: PropositionLike) -> ProposedProposition:
        if isinstance(item, ProposedProposition):
            return item
        if isinstance(item, MechanicalProposition):
            return ProposedProposition.from_proposition(item)
        raise TypeError("A premise or conclusion is not a proposition record.")

    @staticmethod
    def _schema_type(schema: str) -> PropositionType:
        prefix = "MECHANICAL_PROPOSITION:"
        if not schema.startswith(prefix):
            raise ValueError(f"Unsupported premise schema {schema!r}.")
        return PropositionType(schema[len(prefix) :])

    @staticmethod
    def _conclusion_type(rule: Any) -> PropositionType:
        schema = rule.conclusion_schema.split(";", 1)[0]
        return MGuardrail._schema_type(schema)

    def _ancestry_revoked(self, ancestry: GroundingAncestry | None) -> bool:
        if ancestry is None:
            return False
        return bool(
            set(ancestry.trust_root_ids)
            & set(self.grounding_registry.revoked_trust_root_ids)
            or set(ancestry.contract_references)
            & set(self.grounding_registry.revoked_contract_references)
            or set(ancestry.assertion_ids)
            & set(self.grounding_registry.revoked_assertion_ids)
            or set(ancestry.acquisition_channel_ids)
            & set(self.grounding_registry.revoked_channel_ids)
        )

    @staticmethod
    def _genealogy_label(genealogy: Any) -> str:
        identity = getattr(genealogy, "genealogy_id", None)
        return str(identity if identity is not None else genealogy)

    @staticmethod
    def _missing_ancestry(
        conclusion: GroundingAncestry,
        parents: tuple[GroundingAncestry, ...],
    ) -> tuple[tuple[str, tuple[str, ...]], ...]:
        fields = (
            "trust_root_ids",
            "contract_references",
            "assertion_ids",
            "acquisition_channel_ids",
            "trace_ids",
            "validation_ids",
        )
        missing = []
        for field in fields:
            values = tuple(
                sorted(
                    {
                        value
                        for parent in parents
                        for value in getattr(parent, field)
                        if value not in getattr(conclusion, field)
                    }
                )
            )
            if values:
                missing.append((field, values))
        if any(
            parent.mechanical_scope != conclusion.mechanical_scope
            for parent in parents
        ):
            missing.append(("mechanical_scope", ("exact-parent-scope",)))
        return tuple(missing)

    @staticmethod
    def _ancestry_contains(
        conclusion: GroundingAncestry,
        parents: tuple[GroundingAncestry, ...],
    ) -> bool:
        fields = (
            "trust_root_ids",
            "contract_references",
            "assertion_ids",
            "acquisition_channel_ids",
            "trace_ids",
            "validation_ids",
        )
        return all(
            all(
                set(getattr(parent, field)).issubset(
                    set(getattr(conclusion, field))
                )
                for parent in parents
            )
            for field in fields
        ) and all(
            parent.mechanical_scope == conclusion.mechanical_scope
            for parent in parents
        )

    @staticmethod
    def _allow(
        exact_reason: str,
        *,
        authority_reference: str,
        premise_ids: tuple[str, ...],
        conclusion_id: str,
    ) -> GuardrailDecision:
        return GuardrailDecision(
            "ALLOW",
            GuardrailReasonCode.VERIFICATION_PASSED,
            exact_reason,
            evidence=(
                "No automatic premise discovery performed.",
                "No scope completion or proof-path selection performed.",
            ),
            authority_reference=authority_reference,
            premise_ids=premise_ids,
            conclusion_id=conclusion_id,
        )

    @staticmethod
    def _block(
        reason_code: GuardrailReasonCode,
        exact_reason: str,
        premise_ids: tuple[str, ...] = (),
        conclusion_id: str = "",
    ) -> GuardrailDecision:
        return GuardrailDecision(
            "BLOCK",
            reason_code,
            exact_reason,
            premise_ids=premise_ids,
            conclusion_id=conclusion_id,
        )

    @staticmethod
    def _unresolved(
        reason_code: GuardrailReasonCode,
        exact_reason: str,
        premise_ids: tuple[str, ...] = (),
        conclusion_id: str = "",
    ) -> GuardrailDecision:
        return GuardrailDecision(
            "UNRESOLVED",
            reason_code,
            exact_reason,
            premise_ids=premise_ids,
            conclusion_id=conclusion_id,
        )

    @staticmethod
    def _reopen(
        reason_code: GuardrailReasonCode,
        exact_reason: str,
        premise_ids: tuple[str, ...] = (),
        conclusion_id: str = "",
    ) -> GuardrailDecision:
        return GuardrailDecision(
            "REOPEN",
            reason_code,
            exact_reason,
            premise_ids=premise_ids,
            conclusion_id=conclusion_id,
        )