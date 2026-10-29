from dataclasses import replace
from pathlib import Path

from m_machine import (
    DerivationProposal,
    DerivationReceipt,
    GroundingAncestry,
    GuardrailReasonCode,
    MGuardrail,
    PropositionOrigin,
    PropositionStatus,
    PropositionType,
    ProposedProposition,
    WitnessStatus,
    default_mechanical_rule_registry,
    default_proposition_type_registry,
)


ROOT = Path(__file__).resolve().parents[1]
SCOPE = (
    ("access_snapshot", "guardrail-access"),
    ("mechanical_configuration", "guardrail-config"),
    ("field_context", "guardrail-field"),
    ("scale", "guardrail-scale"),
    ("genealogy", "guardrail-genealogy"),
    ("execution_lineage", "guardrail-lineage"),
)


def _valid_proposal():
    types = default_proposition_type_registry(ROOT)
    rule = default_mechanical_rule_registry(ROOT).mechanical_rules[0]
    parent_receipt = DerivationReceipt.create(
        operation_name="prior.derived.premise",
        authoritative_source_file="docs/THE_11_FUNDAMENTAL_LAWS.md",
        authoritative_clause="frozen parent premise",
        operation_performed="Preserved an already-derived premise.",
        resulting_difference_or_consequence="parent",
        status="DERIVED_M",
    )
    premise = ProposedProposition(
        proposition_id=parent_receipt.receipt_id,
        predicate_type=PropositionType.REAL_DIFFERENCE_EXISTS,
        mechanical_scope=SCOPE,
        subject_receipt_ids=(parent_receipt.receipt_id,),
        proposition_status=PropositionStatus.MECHANICAL_EXISTENCE_PROVED,
        witness_status=WitnessStatus.WITNESS_FREE,
        proof_genealogies=("parent-genealogy",),
        origin=PropositionOrigin.DERIVED_M,
    )
    conclusion_id = types.proposition_identity(
        PropositionType.REAL_CONSEQUENCE_EXISTS,
        SCOPE,
        (parent_receipt.receipt_id,),
    )
    conclusion = ProposedProposition(
        proposition_id=conclusion_id,
        predicate_type=PropositionType.REAL_CONSEQUENCE_EXISTS,
        mechanical_scope=SCOPE,
        subject_receipt_ids=(parent_receipt.receipt_id,),
        proposition_status=PropositionStatus.MECHANICAL_EXISTENCE_PROVED,
        witness_status=WitnessStatus.WITNESS_FREE,
        parent_receipt_ids=(parent_receipt.receipt_id,),
        proof_genealogies=("parent-genealogy", "r1-genealogy"),
        origin=PropositionOrigin.DERIVED_M,
    )
    conclusion_receipt = DerivationReceipt.create(
        operation_name=rule.rule_id,
        authoritative_source_file=rule.authority_source,
        authoritative_clause=f"hash={rule.authority_range_hash}",
        input_receipt_ids=(parent_receipt.receipt_id,),
        operation_performed="Applied the frozen rule.",
        resulting_difference_or_consequence=conclusion_id,
        status="DERIVED_M",
    )
    return DerivationProposal(
        rule_id=rule.rule_id,
        rule_version=rule.version,
        rule_semantic_hash=rule.semantic_specification_hash,
        implementation_id=rule.implementation_id,
        implementation_hash=rule.implementation_hash,
        authority_source=rule.authority_source,
        authority_range=rule.authority_range,
        authority_range_hash=rule.authority_range_hash,
        premises=(premise,),
        conclusion=conclusion,
        premise_receipt_ids=(parent_receipt.receipt_id,),
        supporting_receipts=(parent_receipt,),
        conclusion_receipt=conclusion_receipt,
    )


def _verify(proposal):
    return MGuardrail(
        proposition_types=default_proposition_type_registry(ROOT),
        rule_registry=default_mechanical_rule_registry(ROOT),
    ).verify(proposal)


def test_valid_proposal_is_allowed_without_execution_or_inference():
    result = _verify(_valid_proposal())
    assert result.decision == "ALLOW"
    assert result.reason_code == GuardrailReasonCode.VERIFICATION_PASSED
    assert "No automatic premise discovery" in result.evidence[0]


def test_wrong_authority_is_blocked():
    result = _verify(
        replace(_valid_proposal(), authority_range_hash="0" * 64)
    )
    assert result.decision == "BLOCK"
    assert result.reason_code == GuardrailReasonCode.AUTHORITY_MISMATCH


def test_absent_premise_is_unresolved():
    result = _verify(replace(_valid_proposal(), premises=()))
    assert result.decision == "UNRESOLVED"
    assert result.reason_code == GuardrailReasonCode.PREMISE_ABSENT


def test_missing_access_information_reopens_without_guessing():
    result = _verify(
        replace(_valid_proposal(), missing_access_dimensions=("field_context",))
    )
    assert result.decision == "REOPEN"
    assert result.reason_code == GuardrailReasonCode.INFORMATION_ACCESS_MISSING


def test_unauthorized_scope_is_blocked():
    proposal = _valid_proposal()
    bad_scope = SCOPE + (("unauthorized", "value"),)
    result = _verify(
        replace(
            proposal,
            conclusion=replace(proposal.conclusion, mechanical_scope=bad_scope),
        )
    )
    assert result.decision == "BLOCK"
    assert result.reason_code in {
        GuardrailReasonCode.SCOPE_UNAUTHORIZED,
        GuardrailReasonCode.SCOPE_INCOMPATIBLE,
    }


def test_wrong_origin_is_blocked():
    proposal = _valid_proposal()
    result = _verify(
        replace(
            proposal,
            premises=(
                replace(
                    proposal.premises[0],
                    origin=PropositionOrigin.GROUNDED_EXTERNAL,
                ),
            ),
        )
    )
    assert result.decision == "BLOCK"
    assert result.reason_code == GuardrailReasonCode.ORIGIN_NOT_AUTHORIZED


def test_wrong_receipt_is_blocked():
    result = _verify(
        replace(_valid_proposal(), premise_receipt_ids=("wrong-receipt",))
    )
    assert result.decision == "BLOCK"
    assert result.reason_code == GuardrailReasonCode.RECEIPT_MISMATCH


def test_incomplete_ancestry_and_provenance_are_blocked():
    proposal = _valid_proposal()
    ancestry = GroundingAncestry(
        trust_root_ids=("G1",),
        contract_references=("contract:G1",),
        assertion_ids=("A1",),
        trace_ids=("T1",),
        validation_ids=("V1",),
        mechanical_scope=SCOPE,
    )
    result = _verify(
        replace(
            proposal,
            premises=(
                replace(proposal.premises[0], grounding_ancestry=ancestry),
            ),
        )
    )
    assert result.decision == "BLOCK"
    assert result.reason_code == GuardrailReasonCode.PROVENANCE_NOT_PRESERVABLE

def test_guardrail_identifies_the_exact_dropped_genealogy_path():
    proposal = _valid_proposal()
    result = _verify(
        replace(
            proposal,
            conclusion=replace(
                proposal.conclusion,
                proof_genealogies=("r1-genealogy",),
            ),
        )
    )
    assert result.decision == "BLOCK"
    assert result.reason_code == GuardrailReasonCode.PROVENANCE_NOT_PRESERVABLE
    assert "parent-genealogy" in result.exact_reason


def test_representation_shortcut_is_blocked():
    result = _verify(
        replace(_valid_proposal(), shortcut_claims=("payload",))
    )
    assert result.decision == "BLOCK"
    assert result.reason_code == GuardrailReasonCode.REPRESENTATION_SHORTCUT


def test_single_trace_without_required_pairwise_premise_is_unresolved():
    result = _verify(replace(_valid_proposal(), premises=()))
    assert result.decision == "UNRESOLVED"
    assert result.reason_code == GuardrailReasonCode.PREMISE_ABSENT


def test_source_level_claim_is_blocked():
    result = _verify(replace(_valid_proposal(), source_claim=True))
    assert result.decision == "BLOCK"
    assert result.reason_code == GuardrailReasonCode.SOURCE_CLAIM_UNAUTHORIZED


def test_pair_scope_in_real_difference_conclusion_is_blocked_explicitly():
    proposal = _valid_proposal()
    pair_scope = SCOPE + (("pair_scope", "pair-1"),)
    result = _verify(
        replace(
            proposal,
            conclusion=replace(
                proposal.conclusion,
                predicate_type=PropositionType.REAL_DIFFERENCE_EXISTS,
                mechanical_scope=pair_scope,
                proposition_id="pair-scope-conclusion",
            ),
        )
    )
    assert result.decision == "BLOCK"
    assert result.reason_code == GuardrailReasonCode.SCOPE_INCOMPATIBLE


def test_revoked_genealogy_is_blocked():
    proposal = _valid_proposal()
    ancestry = GroundingAncestry(
        trust_root_ids=("G1",),
        contract_references=("contract:G1",),
        assertion_ids=("A1",),
        trace_ids=("T1",),
        validation_ids=("V1",),
        mechanical_scope=SCOPE,
    )
    guardrail = MGuardrail(
        proposition_types=default_proposition_type_registry(ROOT),
        rule_registry=default_mechanical_rule_registry(ROOT),
    )
    guardrail.grounding_registry = replace(
        guardrail.grounding_registry,
        revoked_trust_root_ids=("G1",),
    )
    result = guardrail.verify(
        replace(
            proposal,
            premises=(
                replace(
                    proposal.premises[0],
                    grounding_ancestry=ancestry,
                ),
            ),
        )
    )
    assert result.decision == "BLOCK"
    assert result.reason_code == GuardrailReasonCode.GENEALOGY_REVOKED
