"""A derived, non-generative M rule for continuity structure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import inspect
from pathlib import Path
from typing import Literal

from .boot import verify_authoritative_boot
from .receipts import DerivationReceipt


CONTINUITY_RULE_SOURCE = (
    "docs/m_machine/CONTINUITY_STRUCTURE_RULE_V1.md"
)
CONTINUITY_RULE_AUTHORITY_RANGE = (1, 55)
CONTINUITY_RULE_AUTHORITY_HASH = (
    "ce1de1b4738b0ef50d3cd78b542fc35196fec055d85cf0acf49ef13af6f547cf"
)
CONTINUITY_RULE_ID = "M_RULE_CONTINUITY_STRUCTURE_V1"
CONTINUITY_RULE_VERSION = "1"
CONTINUITY_RULE_SEMANTIC_SPECIFICATION = (
    "Given an explicitly supplied and receipt-bearing mechanical genealogy "
    "relation with complete discriminating access, classify one continuation "
    "class as CONTINUOUS_TRANSFORMATION, no continuation as "
    "CONTINUITY_CEASED, multiple non-reducible continuation classes as "
    "BRANCHED_OR_NON_UNIQUE_IDENTITY, and one continuation class with multiple "
    "antecedent continuities as FUSED_OR_COMPOSITE_CONTINUITY. If the access "
    "does not discriminate uniqueness, absence, or multiplicity, return only "
    "UNRESOLVED. Never use matter percentage, resemblance, form, function, "
    "human naming, labels, payloads, timestamps, plausibility, scores, or "
    "arbitrary thresholds; never repair malformed evidence."
)
CONTINUITY_RULE_SEMANTIC_HASH = (
    "f7b41ac3687f2826d13e50d85a00077242fa35a870a48804ae37516546b3a267"
)
CONTINUITY_RULE_IMPLEMENTATION_ID = (
    "m_machine.continuity_structure:"
    "apply_continuity_structure_rule"
)
CONTINUITY_RULE_IMPLEMENTATION_HASH = (
    "b2fdbac5564b6a301b83fc6e48e1e6412e3667b36cc9a121b28b5098cf413e06"
)
CONTINUITY_RULE_AUTHORIZATION_AUDIT_ID = (
    "DERIVED_CONTINUITY_STRUCTURE_RULE_REGISTRATION_AUDIT"
)
CONTINUITY_RULE_FALSIFICATION_BOUNDARY = (
    "With complete discriminating access, a change from one exact continuation "
    "class to none, multiple non-reducible classes, or one class with multiple "
    "antecedent continuities must change the classification accordingly. "
    "Removing that discriminating access must return UNRESOLVED. Absence of "
    "discriminating access is not evidence of cessation."
)


def semantic_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class AccessDiscrimination(str, Enum):
    COMPLETE = "COMPLETE_DISCRIMINATED"
    INSUFFICIENT = "INSUFFICIENT"


class ContinuityOutcome(str, Enum):
    CONTINUOUS_TRANSFORMATION = "CONTINUOUS_TRANSFORMATION"
    CONTINUITY_CEASED = "CONTINUITY_CEASED"
    BRANCHED_OR_NON_UNIQUE_IDENTITY = (
        "BRANCHED_OR_NON_UNIQUE_IDENTITY"
    )
    FUSED_OR_COMPOSITE_CONTINUITY = "FUSED_OR_COMPOSITE_CONTINUITY"
    UNRESOLVED = "UNRESOLVED"


ContinuityDecision = Literal["ALLOW", "UNRESOLVED", "BLOCK"]


@dataclass(frozen=True, slots=True)
class ContinuationPath:
    """An explicitly supplied mechanical genealogy edge."""

    continuation_id: str
    predecessor_genealogy_id: str
    successor_configuration_id: str
    continuation_class_id: str


@dataclass(frozen=True, slots=True)
class ContinuityEvidence:
    """The complete relation package supplied to the rule."""

    prior_genealogy_ids: tuple[str, ...]
    continuation_paths: tuple[ContinuationPath, ...]
    access_discrimination: AccessDiscrimination
    evidence_receipt_ids: tuple[str, ...]
    provenance: tuple[str, ...]
    ancestry: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "prior_genealogy_ids", tuple(self.prior_genealogy_ids)
        )
        object.__setattr__(
            self, "continuation_paths", tuple(self.continuation_paths)
        )
        object.__setattr__(
            self,
            "access_discrimination",
            AccessDiscrimination(self.access_discrimination),
        )
        object.__setattr__(
            self, "evidence_receipt_ids", tuple(self.evidence_receipt_ids)
        )
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "ancestry", tuple(self.ancestry))


@dataclass(frozen=True, slots=True)
class ContinuityGenealogy:
    prior_genealogy_ids: tuple[str, ...]
    continuation_ids: tuple[str, ...]
    continuation_class_ids: tuple[str, ...]
    parent_receipt_ids: tuple[str, ...]
    rule_id: str
    rule_hash: str


@dataclass(frozen=True, slots=True)
class ContinuityEvaluation:
    decision: ContinuityDecision
    outcome: ContinuityOutcome | None
    reason: str
    genealogy: ContinuityGenealogy | None
    receipt: DerivationReceipt


@dataclass(frozen=True, slots=True)
class ContinuityStructureRule:
    rule_id: str
    version: str
    authority_source: str
    authority_range: tuple[int, int]
    authority_range_hash: str
    semantic_specification: str
    semantic_specification_hash: str
    implementation_id: str
    implementation_hash: str
    authorization_audit_id: str
    falsification_boundary: str


@dataclass(frozen=True, slots=True)
class ContinuityRuleRegistry:
    rule: ContinuityStructureRule
    repository_root: Path

    @property
    def rule_count(self) -> int:
        return 1


def verify_continuity_rule_authority(
    repository_root: str | Path = Path("."),
) -> str:
    root = Path(repository_root).resolve()
    verify_authoritative_boot(root)
    path = root / CONTINUITY_RULE_SOURCE
    if not path.is_file():
        raise ValueError(
            f"Continuity rule authority source is missing: "
            f"{CONTINUITY_RULE_SOURCE}"
        )
    lines = path.read_bytes().splitlines(keepends=True)
    start, end = CONTINUITY_RULE_AUTHORITY_RANGE
    selected = lines[start - 1 : end]
    if len(selected) != end - start + 1:
        raise ValueError("Continuity rule authority range is incomplete.")
    actual = hashlib.sha256(b"".join(selected)).hexdigest()
    if actual != CONTINUITY_RULE_AUTHORITY_HASH:
        raise ValueError("Continuity rule authority hash mismatch.")
    return actual


def _rule_authority_clause(rule: ContinuityStructureRule) -> str:
    return (
        f"lines {rule.authority_range[0]}-{rule.authority_range[1]}; "
        f"source_sha256={rule.authority_range_hash}; "
        f"rule_sha256={rule.semantic_specification_hash}"
    )


def _unique_nonempty(values: tuple[str, ...]) -> bool:
    return bool(values) and all(values) and len(values) == len(set(values))


def _invalid_evidence(evidence: object) -> str | None:
    if not isinstance(evidence, ContinuityEvidence):
        return "Continuity evidence must be explicit and typed."
    if not _unique_nonempty(evidence.prior_genealogy_ids):
        return "Prior genealogy identities are missing or not unique."
    if not _unique_nonempty(evidence.evidence_receipt_ids):
        return "The continuity evidence receipt chain is missing or not unique."
    if not _unique_nonempty(evidence.provenance):
        return "Continuity provenance is missing or not preservable."
    if not _unique_nonempty(evidence.ancestry):
        return "Continuity ancestry is missing or not preservable."
    continuation_ids = tuple(
        path.continuation_id for path in evidence.continuation_paths
    )
    if len(continuation_ids) != len(set(continuation_ids)):
        return "Continuation identities must be unique."
    for path in evidence.continuation_paths:
        if not all(
            (
                path.continuation_id,
                path.predecessor_genealogy_id,
                path.successor_configuration_id,
                path.continuation_class_id,
            )
        ):
            return "Continuation path fields must be complete."
        if path.predecessor_genealogy_id not in evidence.prior_genealogy_ids:
            return "A continuation path references an unknown prior genealogy."
    return None


def _make_receipt(
    *,
    rule: ContinuityStructureRule,
    evidence: ContinuityEvidence,
    decision: ContinuityDecision,
    outcome: ContinuityOutcome | None,
    operation: str,
) -> DerivationReceipt:
    result = outcome.value if outcome is not None else decision
    continuation_path_ids = tuple(
        path.continuation_id for path in evidence.continuation_paths
    )
    return DerivationReceipt.create(
        operation_name=rule.rule_id,
        authoritative_source_file=rule.authority_source,
        authoritative_clause=_rule_authority_clause(rule),
        input_receipt_ids=evidence.evidence_receipt_ids,
        accessible_evidence=(
            f"access_discrimination={evidence.access_discrimination.value}",
            f"prior_genealogies={evidence.prior_genealogy_ids}",
            f"continuation_paths={continuation_path_ids}",
            f"provenance={evidence.provenance}",
            f"ancestry={evidence.ancestry}",
        ),
        operation_performed=operation,
        resulting_difference_or_consequence=result,
        status=(
            "DERIVED_M"
            if decision == "ALLOW"
            else "UNRESOLVED"
            if decision == "UNRESOLVED"
            else "BLOCKED_EXTERNAL"
        ),
        implementation_source="m_machine/continuity_structure.py",
        clause_id=rule.rule_id,
    )


def _evaluation(
    *,
    rule: ContinuityStructureRule,
    evidence: ContinuityEvidence,
    decision: ContinuityDecision,
    outcome: ContinuityOutcome | None,
    reason: str,
    genealogy: ContinuityGenealogy | None = None,
) -> ContinuityEvaluation:
    return ContinuityEvaluation(
        decision=decision,
        outcome=outcome,
        reason=reason,
        genealogy=genealogy,
        receipt=_make_receipt(
            rule=rule,
            evidence=evidence,
            decision=decision,
            outcome=outcome,
            operation=reason,
        ),
    )


def apply_continuity_structure_rule(
    evidence: ContinuityEvidence,
    *,
    rule: ContinuityStructureRule,
) -> ContinuityEvaluation:
    """Apply only the exact supplied genealogy relation."""

    invalid_reason = _invalid_evidence(evidence)
    if invalid_reason is not None:
        return _evaluation(
            rule=rule,
            evidence=evidence
            if isinstance(evidence, ContinuityEvidence)
            else ContinuityEvidence(
                prior_genealogy_ids=(),
                continuation_paths=(),
                access_discrimination=AccessDiscrimination.INSUFFICIENT,
                evidence_receipt_ids=(),
                provenance=(),
                ancestry=(),
            ),
            decision="BLOCK",
            outcome=None,
            reason=invalid_reason,
        )
    if evidence.access_discrimination == AccessDiscrimination.INSUFFICIENT:
        return _evaluation(
            rule=rule,
            evidence=evidence,
            decision="UNRESOLVED",
            outcome=ContinuityOutcome.UNRESOLVED,
            reason=(
                "Available access does not discriminate uniqueness, absence, "
                "or multiplicity of continuation."
            ),
        )

    paths = evidence.continuation_paths
    class_ids = tuple(dict.fromkeys(path.continuation_class_id for path in paths))
    path_ids = tuple(path.continuation_id for path in paths)
    antecedents = tuple(
        dict.fromkeys(path.predecessor_genealogy_id for path in paths)
    )
    if not class_ids:
        outcome = ContinuityOutcome.CONTINUITY_CEASED
        reason = (
            "Complete discriminating access establishes no continuation of "
            "the prior genealogy."
        )
    elif len(class_ids) > 1:
        outcome = ContinuityOutcome.BRANCHED_OR_NON_UNIQUE_IDENTITY
        reason = (
            "Complete discriminating access establishes multiple "
            "non-reducible continuation classes."
        )
    elif len(antecedents) > 1:
        outcome = ContinuityOutcome.FUSED_OR_COMPOSITE_CONTINUITY
        reason = (
            "Multiple antecedent continuities explicitly converge on one "
            "continuation class."
        )
    else:
        outcome = ContinuityOutcome.CONTINUOUS_TRANSFORMATION
        reason = (
            "Exactly one mechanically discriminated continuation class "
            "connects the prior and successor configurations."
        )
    genealogy = ContinuityGenealogy(
        prior_genealogy_ids=evidence.prior_genealogy_ids,
        continuation_ids=path_ids,
        continuation_class_ids=class_ids,
        parent_receipt_ids=evidence.evidence_receipt_ids,
        rule_id=rule.rule_id,
        rule_hash=rule.semantic_specification_hash,
    )
    return _evaluation(
        rule=rule,
        evidence=evidence,
        decision="ALLOW",
        outcome=outcome,
        reason=reason,
        genealogy=genealogy,
    )


def default_continuity_rule_registry(
    repository_root: str | Path = Path("."),
) -> ContinuityRuleRegistry:
    root = Path(repository_root).resolve()
    verify_continuity_rule_authority(root)
    if semantic_hash(CONTINUITY_RULE_SEMANTIC_SPECIFICATION) != (
        CONTINUITY_RULE_SEMANTIC_HASH
    ):
        raise ValueError("Continuity rule semantic specification hash mismatch.")
    implementation_hash = semantic_hash(
        inspect.getsource(apply_continuity_structure_rule)
    )
    if implementation_hash != CONTINUITY_RULE_IMPLEMENTATION_HASH:
        raise ValueError("Continuity rule implementation hash mismatch.")
    rule = ContinuityStructureRule(
        rule_id=CONTINUITY_RULE_ID,
        version=CONTINUITY_RULE_VERSION,
        authority_source=CONTINUITY_RULE_SOURCE,
        authority_range=CONTINUITY_RULE_AUTHORITY_RANGE,
        authority_range_hash=CONTINUITY_RULE_AUTHORITY_HASH,
        semantic_specification=CONTINUITY_RULE_SEMANTIC_SPECIFICATION,
        semantic_specification_hash=CONTINUITY_RULE_SEMANTIC_HASH,
        implementation_id=CONTINUITY_RULE_IMPLEMENTATION_ID,
        implementation_hash=CONTINUITY_RULE_IMPLEMENTATION_HASH,
        authorization_audit_id=CONTINUITY_RULE_AUTHORIZATION_AUDIT_ID,
        falsification_boundary=CONTINUITY_RULE_FALSIFICATION_BOUNDARY,
    )
    return ContinuityRuleRegistry(rule=rule, repository_root=root)


def evaluate_continuity_structure(
    evidence: ContinuityEvidence,
    *,
    repository_root: str | Path = Path("."),
) -> ContinuityEvaluation:
    registry = default_continuity_rule_registry(repository_root)
    return apply_continuity_structure_rule(
        evidence,
        rule=registry.rule,
    )