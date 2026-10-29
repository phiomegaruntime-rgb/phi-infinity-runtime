from dataclasses import FrozenInstanceError, fields, replace
import hashlib
from pathlib import Path

import pytest

from m_machine import (
    AMENDMENT_06_SOURCE,
    EXPECTED_AMENDMENT_06_SHA256,
    RAW_MECHANICAL_BOOTSTRAP_FRONTIER,
    AccessLocalHandle,
    AccessPackage,
    AccessRecord,
    BasisAccess,
    BasisOrigin,
    BasisRecord,
    ConstructorPolicy,
    DirectOutcomeRelation,
    FrozenPropositionTypeRegistry,
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
    WitnessStatus,
    compile_authoritative_clause_registry,
    default_proposition_type_registry,
    verify_authoritative_boot,
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
        access_instance="phase25-access",
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


def test_amendment_06_boot_hash_and_clause_role_are_frozen():
    verification = verify_authoritative_boot()
    assert AMENDMENT_06_SOURCE in verification.authoritative_files
    assert hashlib.sha256((ROOT / AMENDMENT_06_SOURCE).read_bytes()).hexdigest() == (
        EXPECTED_AMENDMENT_06_SHA256
    )
    clauses = tuple(
        clause
        for clause in compile_authoritative_clause_registry().entries
        if clause.authoritative_source_file == AMENDMENT_06_SOURCE
    )
    assert len(clauses) == 7
    assert all(
        clause.execution_role == "MECHANICAL_PROPOSITION_SEMANTICS"
        for clause in clauses
    )


def test_required_types_exist_uninhabited_without_instances_or_falsehood():
    registry = default_proposition_type_registry(ROOT)
    assert registry.type_count == 6
    assert set(registry.uninhabited_types) == set(PropositionType)
    assert PropositionStatus.UNINHABITED.value != "FALSE"
    assert not hasattr(registry, "instances")


def test_type_registration_is_non_generative_and_immutable():
    registry = default_proposition_type_registry(ROOT)
    spec = registry.get(PropositionType.REAL_DIFFERENCE_EXISTS)
    assert spec.constructor_policy == (
        ConstructorPolicy.NO_CONSTRUCTOR_CURRENTLY_AUTHORIZED
    )
    assert "DERIVED_M" not in repr(registry)
    with pytest.raises(FrozenInstanceError):
        spec.constructor_policy = ConstructorPolicy.MECHANICAL_RULE_ONLY


@pytest.mark.parametrize(
    "attempt",
    [
        {"basis_result": "DISCRIMINABLE_UNDER_BASIS"},
        {"raw_values": (1, 2)},
        {"class_handles": ("a", "b")},
        {"access_records": ("x", "y")},
        {"genealogies": ("g1", "g2")},
        {"human_label": "real difference"},
        {"semantic_comparison": "different"},
        {"distance": 1.0},
        {"statistical_significance": 0.01},
        {"correlation": 1.0},
        {"prediction_difference": True},
    ],
)
def test_prohibited_raw_or_access_inputs_cannot_create_real_difference(attempt):
    registry = default_proposition_type_registry(ROOT)
    with pytest.raises(PermissionError, match="Caller-supplied"):
        registry.create_instance(
            PropositionType.REAL_DIFFERENCE_EXISTS,
            **attempt,
        )


def test_no_generic_mechanical_fact_constructor_or_direct_record_creation():
    registry = default_proposition_type_registry(ROOT)
    assert not hasattr(registry, "make_mechanical_fact")
    with pytest.raises(PermissionError, match="authorized constructor"):
        MechanicalProposition(
            proposition_id="invented",
            predicate_type=PropositionType.REAL_DIFFERENCE_EXISTS,
            mechanical_scope=(("access_snapshot", "a"),),
            subject_receipt_ids=(),
            proposition_status=PropositionStatus.ASSERTED,
            witness_status=WitnessStatus.WITNESS_FREE,
            parent_receipt_ids=(),
            proof_genealogies=(),
        )


def test_consequence_existence_is_existential_and_witness_free():
    spec = default_proposition_type_registry(ROOT).get(
        PropositionType.REAL_CONSEQUENCE_EXISTS
    )
    assert spec.existential
    assert not spec.witness_bearing
    assert spec.constructor_policy == ConstructorPolicy.MECHANICAL_RULE_ONLY
    assert "without identifying a witness" in spec.semantic_statement


def test_existence_proved_and_witness_constructed_are_distinct_types():
    registry = default_proposition_type_registry(ROOT)
    existence = registry.get(PropositionType.MECHANICAL_EXISTENCE_PROVED)
    witness = registry.get(PropositionType.MECHANICAL_WITNESS_CONSTRUCTED)
    assert existence.type_id != witness.type_id
    assert existence.existential and not existence.witness_bearing
    assert witness.witness_bearing and not witness.existential


def test_no_skolemization_fields_or_automatic_witness_metadata_exist():
    names = {item.name for item in fields(MechanicalProposition)}
    assert "witness_id" not in names
    assert "witness_count" not in names
    assert "magnitude" not in names
    assert "direction" not in names
    assert "location" not in names
    assert "timing" not in names
    assert "hidden_node" not in names


def test_exact_scope_controls_proposition_identity_without_globalization():
    registry = default_proposition_type_registry(ROOT)
    c1 = (("access_snapshot", "a1"), ("scale", "s"))
    c2 = (("access_snapshot", "a2"), ("scale", "s"))
    first = registry.proposition_identity(
        PropositionType.REAL_DIFFERENCE_EXISTS, c1, ("receipt",)
    )
    same = registry.proposition_identity(
        PropositionType.REAL_DIFFERENCE_EXISTS, c1, ("receipt",)
    )
    other_access = registry.proposition_identity(
        PropositionType.REAL_DIFFERENCE_EXISTS, c2, ("receipt",)
    )
    other_basis_subject = registry.proposition_identity(
        PropositionType.REAL_DIFFERENCE_EXISTS, c1, ("other",)
    )
    assert first == same
    assert first != other_access
    assert first != other_basis_subject


def test_scope_allows_only_declared_fields_and_does_not_force_all_fields():
    registry = default_proposition_type_registry(ROOT)
    scope = (("mechanical_configuration", "c"),)
    assert registry.validate_scope(
        PropositionType.REAL_DIFFERENCE_EXISTS, scope
    ) == scope
    with pytest.raises(ValueError, match="unauthorized fields"):
        registry.validate_scope(
            PropositionType.REAL_DIFFERENCE_EXISTS,
            (("human_category", "different"),),
        )


def test_constructor_policies_reject_unauthorized_creation_paths():
    registry = default_proposition_type_registry(ROOT)
    with pytest.raises(PermissionError, match="No constructor"):
        registry.enforce_constructor_policy(
            PropositionType.REAL_DIFFERENCE_EXISTS,
            constructor_kind="MECHANICAL_RULE",
            raw_scope=True,
            authorized_rule=True,
        )
    with pytest.raises(PermissionError, match="registered mechanical rule"):
        registry.enforce_constructor_policy(
            PropositionType.REAL_CONSEQUENCE_EXISTS,
            constructor_kind="CALLER_OTHER",
            raw_scope=True,
        )


def test_falsification_and_native_policies_cannot_cross_their_scope():
    base = default_proposition_type_registry(ROOT)
    source = base.get(PropositionType.REAL_CONSEQUENCE_EXISTS)
    falsification = replace(
        source,
        constructor_policy=ConstructorPolicy.FALSIFICATION_RULE_ONLY,
    )
    native = replace(
        source,
        type_id=PropositionType.MECHANICAL_WITNESS_CONSTRUCTED,
        existential=False,
        witness_bearing=True,
        constructor_policy=ConstructorPolicy.NATIVE_REPRESENTED_SCOPE_ONLY,
    )
    falsification_registry = FrozenPropositionTypeRegistry(
        (falsification,), ROOT
    )
    native_registry = FrozenPropositionTypeRegistry((native,), ROOT)
    with pytest.raises(PermissionError, match="falsification"):
        falsification_registry.enforce_constructor_policy(
            falsification.type_id,
            constructor_kind="MECHANICAL_RULE",
            raw_scope=False,
            authorized_rule=True,
        )
    with pytest.raises(PermissionError, match="cannot enter raw"):
        native_registry.enforce_constructor_policy(
            native.type_id,
            constructor_kind="NATIVE_REPRESENTED",
            raw_scope=True,
            authorized_rule=True,
        )


def test_proof_kernel_recognizes_known_types_and_rejects_unknown_types():
    kernel = ProofKernel(
        proposition_types=default_proposition_type_registry(ROOT),
        repository_root=ROOT,
    )
    assert kernel.validate_proposition_type(
        PropositionType.REAL_DIFFERENCE_EXISTS
    ).type_id == PropositionType.REAL_DIFFERENCE_EXISTS
    with pytest.raises(KeyError, match="Unknown mechanical proposition"):
        kernel.validate_proposition_type("HUMAN_DECLARED_DIFFERENCE")


def test_proof_kernel_preserves_registry_and_scope_without_instances():
    kernel = ProofKernel(
        proposition_types=default_proposition_type_registry(ROOT),
        repository_root=ROOT,
    )
    scope = (("access_snapshot", "a"),)
    result = kernel.close(
        receipts=(),
        scope=scope,
        authority_range="Amendment 05",
        authority_range_hash="0" * 64,
    )
    assert result.state.proposition_type_registry is kernel.proposition_types
    assert kernel.validate_proposition_scope(
        PropositionType.REAL_CONSEQUENCE_EXISTS, scope
    ) == scope
    assert result.new_propositions == ()
    assert result.new_derived_m_count == 0


def test_raw_execution_keeps_types_available_but_creates_no_propositions():
    machine = MExecutionMachine()
    result = machine.execute(_package())
    assert machine.proposition_types.type_count == 6
    assert machine.raw_rule_registry.mechanical_rule_count == 1
    assert machine.raw_fireable_positive_mechanical_rule_count == 0
    assert result.status == "UNRESOLVED"
    assert result.frontier == RAW_MECHANICAL_BOOTSTRAP_FRONTIER
    assert result.reopen_request is None
    assert result.value.results[0].status == "DISCRIMINABLE_UNDER_BASIS"
    assert all(
        "REAL_DIFFERENCE_EXISTS" not in receipt.operation_name
        and "REAL_CONSEQUENCE_EXISTS" not in receipt.operation_name
        for receipt in result.receipts
    )
    proof_receipts = tuple(
        receipt
        for receipt in result.receipts
        if receipt.operation_name == "proof_kernel.proof_closure"
    )
    assert len(proof_receipts) == 1
    assert proof_receipts[0].status == "UNRESOLVED"
