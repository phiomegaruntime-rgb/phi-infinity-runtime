"""The single frozen positive mechanical theorem authorized by Phase 27."""

from __future__ import annotations

from dataclasses import dataclass
import inspect
from pathlib import Path

from .mechanical_propositions import (
    FrozenPropositionTypeRegistry,
    MechanicalProposition,
    PropositionStatus,
    PropositionType,
    WitnessStatus,
    _MECHANICAL_RULE_CONSTRUCTOR_TOKEN,
    _construct_from_authorized_mechanical_rule,
    default_proposition_type_registry,
)
from .proof_kernel import (
    FrozenRuleRegistry,
    InferenceRule,
    ProofGenealogy,
    RuleClass,
    semantic_hash,
)
from .receipts import DerivationReceipt


FIRST_MECHANICAL_RULE_ID = (
    "M_RULE_REAL_DIFFERENCE_IMPLIES_CONSEQUENCE_EXISTENCE_V1"
)
FUNDAMENTAL_LAWS_SOURCE = "docs/THE_11_FUNDAMENTAL_LAWS.md"
FIRST_MECHANICAL_RULE_AUTHORITY_RANGE = (59, 61)
FIRST_MECHANICAL_RULE_AUTHORITY_HASH = (
    "fb2f81e891ce6a91e24e3384c6be753eae5e0990eddd748c86755143bfc1bd23"
)
FIRST_MECHANICAL_RULE_SEMANTIC_SPECIFICATION = (
    "For one exact mechanical proposition of type REAL_DIFFERENCE_EXISTS, "
    "under its exact authorized scope and receipt genealogy, derive one "
    "witness-free REAL_CONSEQUENCE_EXISTS proposition in the exact inherited "
    "scope. Preserve the qualifying premise receipt, proof genealogy, rule "
    "identity, rule version, authority, and witness-free status. Do not "
    "construct a difference witness, consequence witness, continuation object, "
    "or intermediate Dependency, Exchange, Transformation, Propagation, or "
    "Continuation proposition."
)
FIRST_MECHANICAL_RULE_SEMANTIC_HASH = (
    "911598ed25b8d750342eb670194c240a1d8b0a330b947d8c0b813ccc7a7d6cdf"
)
FIRST_MECHANICAL_RULE_IMPLEMENTATION_ID = (
    "m_machine.mechanical_rules:"
    "apply_real_difference_implies_consequence_existence"
)
FIRST_MECHANICAL_RULE_IMPLEMENTATION_HASH = (
    "9b161fcf6af4479009298fadba51dcf8e0e2c436f5acf95bce26aad035147e8f"
)
FIRST_MECHANICAL_RULE_AUTHORIZATION_AUDIT_ID = (
    "PHASE_26_FIRST_THEOREM_RULE_REGISTRATION_AUDIT"
)
FIRST_MECHANICAL_RULE_FALSIFICATION_BOUNDARY = (
    "Contradiction is relevant only after an exact authorized "
    "REAL_DIFFERENCE_EXISTS premise and this theorem application when a "
    "separately authorized future proposition is formally incompatible with "
    "the existence of any real consequence under the same scope. Absence of "
    "an observed consequence is not falsification."
)


@dataclass(frozen=True, slots=True)
class MechanicalRuleExecution:
    rule_id: str
    applied: bool
    proposition: MechanicalProposition | None
    receipt: DerivationReceipt | None
    genealogy: ProofGenealogy | None
    reason: str


def apply_real_difference_implies_consequence_existence(
    premise: MechanicalProposition,
    *,
    rule_registry: FrozenRuleRegistry,
    proposition_types: FrozenPropositionTypeRegistry,
    raw_scope: bool = False,
) -> MechanicalRuleExecution:
    """Execute only the frozen witness-free existential theorem."""

    rule = rule_registry.get(FIRST_MECHANICAL_RULE_ID)
    if raw_scope:
        return MechanicalRuleExecution(
            rule.rule_id,
            False,
            None,
            None,
            None,
            "Raw scope has no authorized REAL_DIFFERENCE_EXISTS constructor.",
        )
    if (
        not isinstance(premise, MechanicalProposition)
        or premise.predicate_type
        != PropositionType.REAL_DIFFERENCE_EXISTS
    ):
        return MechanicalRuleExecution(
            rule.rule_id,
            False,
            None,
            None,
            None,
            "Exact REAL_DIFFERENCE_EXISTS mechanical premise is absent.",
        )
    proposition_types.validate_scope(
        PropositionType.REAL_DIFFERENCE_EXISTS,
        premise.mechanical_scope,
    )
    consequence_id = proposition_types.proposition_identity(
        PropositionType.REAL_CONSEQUENCE_EXISTS,
        premise.mechanical_scope,
        (premise.proposition_id,),
    )
    genealogy = ProofGenealogy(
        conclusion_identity=consequence_id,
        parent_receipt_ids=(premise.proposition_id,),
        rule_id=rule.rule_id,
        rule_hash=rule.semantic_specification_hash,
    )
    proposition = _construct_from_authorized_mechanical_rule(
        registry=proposition_types,
        predicate_type=PropositionType.REAL_CONSEQUENCE_EXISTS,
        mechanical_scope=premise.mechanical_scope,
        subject_receipt_ids=(premise.proposition_id,),
        proposition_status=PropositionStatus.MECHANICAL_EXISTENCE_PROVED,
        witness_status=WitnessStatus.WITNESS_FREE,
        parent_receipt_ids=(premise.proposition_id,),
        proof_genealogies=premise.proof_genealogies + (genealogy,),
        authorization_token=_MECHANICAL_RULE_CONSTRUCTOR_TOKEN,
    )
    receipt = DerivationReceipt.create(
        operation_name=rule.rule_id,
        authoritative_source_file=rule.authority_source,
        authoritative_clause=(
            f"lines {rule.authority_range[0]}-{rule.authority_range[1]}; "
            f"source_sha256={rule.authority_range_hash}; "
            f"rule_sha256={rule.semantic_specification_hash}"
        ),
        input_receipt_ids=(premise.proposition_id,),
        accessible_evidence=(
            "exact authorized REAL_DIFFERENCE_EXISTS proposition",
            "exact inherited mechanical scope",
            "witness-free conclusion schema",
        ),
        operation_performed=(
            "Applied the frozen real-difference existence theorem."
        ),
        resulting_difference_or_consequence=proposition.proposition_id,
        status="DERIVED_M",
        implementation_source="m_machine/mechanical_rules.py",
        clause_id=rule.rule_id,
    )
    return MechanicalRuleExecution(
        rule.rule_id,
        True,
        proposition,
        receipt,
        genealogy,
        "Exact frozen theorem applied.",
    )


def default_mechanical_rule_registry(
    repository_root: Path | str = Path("."),
) -> FrozenRuleRegistry:
    if semantic_hash(FIRST_MECHANICAL_RULE_SEMANTIC_SPECIFICATION) != (
        FIRST_MECHANICAL_RULE_SEMANTIC_HASH
    ):
        raise ValueError("Frozen theorem semantic specification hash mismatch.")
    actual_implementation_hash = semantic_hash(
        inspect.getsource(
            apply_real_difference_implies_consequence_existence
        )
    )
    if actual_implementation_hash != FIRST_MECHANICAL_RULE_IMPLEMENTATION_HASH:
        raise ValueError("Frozen theorem implementation hash mismatch.")
    rule = InferenceRule(
        rule_id=FIRST_MECHANICAL_RULE_ID,
        rule_class=RuleClass.MECHANICAL_INFERENCE_RULE,
        authority_source=FUNDAMENTAL_LAWS_SOURCE,
        authority_range=FIRST_MECHANICAL_RULE_AUTHORITY_RANGE,
        authority_range_hash=FIRST_MECHANICAL_RULE_AUTHORITY_HASH,
        semantic_specification=FIRST_MECHANICAL_RULE_SEMANTIC_SPECIFICATION,
        semantic_specification_hash=FIRST_MECHANICAL_RULE_SEMANTIC_HASH,
        premise_schema=(
            "MECHANICAL_PROPOSITION:REAL_DIFFERENCE_EXISTS",
        ),
        scope_constraints=(
            "EXACT_INHERITED_SCOPE",
            "NO_SILENT_GLOBALIZATION",
            "NO_CROSS_ACCESS_TRANSFER",
            "NO_CROSS_BASIS_TRANSFER",
            "NO_CROSS_SCALE_TRANSFER",
            "PRESERVE_PARENT_GENEALOGY",
        ),
        conclusion_schema=(
            "MECHANICAL_PROPOSITION:REAL_CONSEQUENCE_EXISTS;"
            "proposition_status=MECHANICAL_EXISTENCE_PROVED;"
            "witness_status=WITNESS_FREE"
        ),
        unresolved_behavior=(
            "If no exact authorized REAL_DIFFERENCE_EXISTS proposition is "
            "present, do not fire and emit no conclusion, negative fact, "
            "REOPEN, or FirstDivergence."
        ),
        implementation_id=FIRST_MECHANICAL_RULE_IMPLEMENTATION_ID,
        implementation_hash=FIRST_MECHANICAL_RULE_IMPLEMENTATION_HASH,
        version="1",
        separately_audited_authorization=True,
        authorization_audit_id=(
            FIRST_MECHANICAL_RULE_AUTHORIZATION_AUDIT_ID
        ),
        raw_bootstrap="NO",
        falsification_boundary=(
            FIRST_MECHANICAL_RULE_FALSIFICATION_BOUNDARY
        ),
    )
    return FrozenRuleRegistry(
        repository_root=repository_root
    ).register(
        rule,
        implementation=apply_real_difference_implies_consequence_existence,
    )
