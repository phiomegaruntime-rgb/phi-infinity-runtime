import hashlib
import inspect
from dataclasses import fields
from pathlib import Path

import pytest

from m_machine import (
    FIRST_MECHANICAL_RULE_AUTHORITY_HASH,
    FIRST_MECHANICAL_RULE_AUTHORITY_RANGE,
    FIRST_MECHANICAL_RULE_ID,
    FIRST_MECHANICAL_RULE_IMPLEMENTATION_HASH,
    FIRST_MECHANICAL_RULE_IMPLEMENTATION_ID,
    FIRST_MECHANICAL_RULE_SEMANTIC_HASH,
    FIRST_MECHANICAL_RULE_SEMANTIC_SPECIFICATION,
    FUNDAMENTAL_LAWS_SOURCE,
    RAW_MECHANICAL_BOOTSTRAP_FRONTIER,
    AccessLocalHandle,
    AccessPackage,
    AccessRecord,
    BasisAccess,
    BasisOrigin,
    BasisRecord,
    ConstructorPolicy,
    DirectOutcomeRelation,
    LocalReferentMap,
    MExecutionMachine,
    MechanicalProposition,
    OriginProvenance,
    OutcomeBasisBinding,
    OutcomeRecord,
    ProofKernel,
    PropositionStatus,
    PropositionType,
    RelationWitness,
    RuleClass,
    WitnessStatus,
    apply_real_difference_implies_consequence_existence,
    default_mechanical_rule_registry,
    default_proposition_type_registry,
)


ROOT = Path(__file__).resolve().parents[1]


def _package() -> AccessPackage:
    first = AccessRecord("first")
    second = AccessRecord("second")
    first_handle = AccessLocalHandle("first-handle")
    second_handle = AccessLocalHandle("second-handle")
    witness = RelationWitness("witness", first_handle, second_handle)
    basis = BasisRecord("basis")
    first_outcome = OutcomeRecord("first-outcome")
    second_outcome = OutcomeRecord("second-outcome")
    return AccessPackage(
        access_instance="phase27-access",
        manifestations=(first, second),
        local_referent_map=LocalReferentMap(
            ((first_handle, first), (second_handle, second))
        ),
        supplied_witnesses=(witness,),
        provenance=(
            OriginProvenance(
                witness.witness_id,
                "SUPPLIED_AS_ACCESS_STRUCTURE",
            ),
        ),
        basis_access=BasisAccess(
            bases=(basis,),
            origins=(BasisOrigin(basis, "SUPPLIED_AS_ACCESS_BASIS"),),
            outcomes=(first_outcome, second_outcome),
            bindings=(
                OutcomeBasisBinding(basis, first, first_outcome),
                OutcomeBasisBinding(basis, second, second_outcome),
            ),
            direct_relations=(
                DirectOutcomeRelation(
                    basis,
                    first_outcome,
                    second_outcome,
                    "SEPARATELY_RESOLVED",
                ),
            ),
        ),
    )


def test_exactly_one_frozen_positive_mechanical_rule_is_registered():
    registry = default_mechanical_rule_registry(ROOT)
    assert registry.mechanical_rule_count == 1
    assert len(registry.rules) == 1
    rule = registry.mechanical_rules[0]
    assert rule.rule_id == FIRST_MECHANICAL_RULE_ID
    assert rule.version == "1"
    assert rule.rule_class == RuleClass.MECHANICAL_INFERENCE_RULE
    assert rule.raw_bootstrap == "NO"
    assert rule.authorization_audit_id == (
        "PHASE_26_FIRST_THEOREM_RULE_REGISTRATION_AUDIT"
    )


def test_rule_authority_range_and_hash_are_exact():
    rule = default_mechanical_rule_registry(ROOT).mechanical_rules[0]
    assert rule.authority_source == FUNDAMENTAL_LAWS_SOURCE
    assert rule.authority_range == FIRST_MECHANICAL_RULE_AUTHORITY_RANGE == (
        59,
        61,
    )
    assert rule.authority_range_hash == FIRST_MECHANICAL_RULE_AUTHORITY_HASH
    lines = (ROOT / FUNDAMENTAL_LAWS_SOURCE).read_bytes().splitlines(
        keepends=True
    )
    assert hashlib.sha256(b"".join(lines[58:61])).hexdigest() == (
        FIRST_MECHANICAL_RULE_AUTHORITY_HASH
    )


def test_rule_semantic_and_implementation_hashes_are_frozen_separately():
    rule = default_mechanical_rule_registry(ROOT).mechanical_rules[0]
    assert hashlib.sha256(
        FIRST_MECHANICAL_RULE_SEMANTIC_SPECIFICATION.encode()
    ).hexdigest() == FIRST_MECHANICAL_RULE_SEMANTIC_HASH
    assert rule.semantic_specification_hash == (
        FIRST_MECHANICAL_RULE_SEMANTIC_HASH
    )
    assert rule.implementation_id == FIRST_MECHANICAL_RULE_IMPLEMENTATION_ID
    assert hashlib.sha256(
        inspect.getsource(
            apply_real_difference_implies_consequence_existence
        ).encode()
    ).hexdigest() == FIRST_MECHANICAL_RULE_IMPLEMENTATION_HASH
    assert rule.implementation_hash == FIRST_MECHANICAL_RULE_IMPLEMENTATION_HASH
    assert rule.authority_range_hash != rule.semantic_specification_hash
    assert rule.semantic_specification_hash != rule.implementation_hash


def test_premise_and_conclusion_schemas_are_exact_and_witness_free():
    rule = default_mechanical_rule_registry(ROOT).mechanical_rules[0]
    assert rule.premise_schema == (
        "MECHANICAL_PROPOSITION:REAL_DIFFERENCE_EXISTS",
    )
    assert rule.conclusion_schema == (
        "MECHANICAL_PROPOSITION:REAL_CONSEQUENCE_EXISTS;"
        "proposition_status=MECHANICAL_EXISTENCE_PROVED;"
        "witness_status=WITNESS_FREE"
    )
    assert "NO_SILENT_GLOBALIZATION" in rule.scope_constraints
    assert "PRESERVE_PARENT_GENEALOGY" in rule.scope_constraints
    assert (
        "Absence of an observed consequence is not falsification."
        in rule.falsification_boundary
    )


def test_rule_schema_contains_no_witness_or_intermediate_result():
    rule = default_mechanical_rule_registry(ROOT).mechanical_rules[0]
    schema = rule.conclusion_schema
    assert "WITNESS_FREE" in schema
    forbidden = (
        "difference_1",
        "consequence_1",
        "witness_id",
        "consequence_count",
        "magnitude",
        "direction",
        "location",
        "timing",
        "Dependency",
        "Exchange",
        "Transformation",
        "Propagation",
        "Continuation",
    )
    assert all(item not in schema for item in forbidden)


@pytest.mark.parametrize(
    "invalid_premise",
    [
        "DISCRIMINABLE_UNDER_BASIS",
        "Connects_a",
        (1, 2),
        ("access-a", "access-b"),
        ("basis-a", "basis-b"),
        {"human_metadata": "real difference"},
        {"semantic_class": "different"},
    ],
)
def test_access_numeric_human_and_semantic_inputs_cannot_fire_theorem(
    invalid_premise,
):
    result = apply_real_difference_implies_consequence_existence(
        invalid_premise,
        rule_registry=default_mechanical_rule_registry(ROOT),
        proposition_types=default_proposition_type_registry(ROOT),
    )
    assert not result.applied
    assert result.proposition is None
    assert result.receipt is None


def test_raw_scope_cannot_fire_theorem_or_construct_a_premise():
    registry = default_proposition_type_registry(ROOT)
    assert registry.get(
        PropositionType.REAL_DIFFERENCE_EXISTS
    ).constructor_policy == ConstructorPolicy.NO_CONSTRUCTOR_CURRENTLY_AUTHORIZED
    with pytest.raises(PermissionError):
        registry.create_instance(
            PropositionType.REAL_DIFFERENCE_EXISTS,
            human_metadata="real difference",
        )
    result = apply_real_difference_implies_consequence_existence(
        "no legitimate proposition",
        rule_registry=default_mechanical_rule_registry(ROOT),
        proposition_types=registry,
        raw_scope=True,
    )
    assert not result.applied
    assert result.receipt is None


def test_consequence_record_has_no_witness_payload_fields():
    names = {item.name for item in fields(MechanicalProposition)}
    assert "witness_id" not in names
    assert "consequence_count" not in names
    assert "magnitude" not in names
    assert "direction" not in names
    assert "location" not in names
    assert "timing" not in names
    assert PropositionStatus.MECHANICAL_EXISTENCE_PROVED.value == (
        "MECHANICAL_EXISTENCE_PROVED"
    )
    assert WitnessStatus.WITNESS_FREE.value == "WITNESS_FREE"


def test_registered_rule_without_raw_premise_reaches_bootstrap_frontier():
    registry = default_mechanical_rule_registry(ROOT)
    result = ProofKernel(
        registry,
        ROOT,
        default_proposition_type_registry(ROOT),
    ).close(
        receipts=(),
        scope=(("access_snapshot", "raw"),),
        authority_range="Amendment 05 proof closure",
        authority_range_hash="0" * 64,
    )
    assert registry.mechanical_rule_count == 1
    assert result.status == "UNRESOLVED"
    assert result.frontier == RAW_MECHANICAL_BOOTSTRAP_FRONTIER
    assert result.new_propositions == ()
    assert result.new_derived_m_count == 0
    assert result.state.reopen_requests == ()


def test_raw_end_to_end_preserves_discrimination_without_firing_theorem():
    machine = MExecutionMachine()
    result = machine.execute(_package())
    assert machine.raw_rule_registry.mechanical_rule_count == 1
    assert machine.raw_fireable_positive_mechanical_rule_count == 0
    assert result.value.results[0].status == "DISCRIMINABLE_UNDER_BASIS"
    assert result.status == "UNRESOLVED"
    assert result.frontier == RAW_MECHANICAL_BOOTSTRAP_FRONTIER
    assert result.reopen_request is None
    assert all(
        receipt.operation_name != FIRST_MECHANICAL_RULE_ID
        for receipt in result.receipts
    )
    proof_receipts = tuple(
        receipt
        for receipt in result.receipts
        if receipt.operation_name == "proof_kernel.proof_closure"
    )
    assert len(proof_receipts) == 1
    assert proof_receipts[0].status == "UNRESOLVED"
    assert all(receipt.status != "DERIVED_M" for receipt in proof_receipts)
    assert not hasattr(result.value, "dependency")
    assert not hasattr(result.value, "exchange")
    assert not hasattr(result.value, "continuation")


def test_phase32_amendment_07_does_not_register_a_second_rule():
    assert len(tuple((ROOT / "docs").glob("*AMENDMENT_07*"))) == 1
    registry = default_mechanical_rule_registry(ROOT)
    assert tuple(rule.rule_id for rule in registry.mechanical_rules) == (
        FIRST_MECHANICAL_RULE_ID,
    )
