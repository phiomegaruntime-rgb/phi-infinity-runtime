import hashlib
from dataclasses import fields, replace
from pathlib import Path

import pytest

from m_machine import (
    AMENDMENT_08_SOURCE,
    EXPECTED_AMENDMENT_08_SHA256,
    FIRST_MECHANICAL_RULE_ID,
    NON_IDENTITY_RULE_REGISTRATION_FRONTIER,
    ConstructorPolicy,
    GroundingAssertion,
    MExecutionMachine,
    PairwiseGroundingAssertion,
    ProofKernel,
    PropositionOrigin,
    PropositionType,
    TrustRoot,
    WitnessStatus,
    compile_authoritative_clause_registry,
    default_grounding_registry,
    default_mechanical_rule_registry,
    default_proposition_type_registry,
    verify_authoritative_boot,
)


ROOT = Path(__file__).resolve().parents[1]
CHANNEL = "EXPLICIT_ACQUISITION_CHANNEL"
PAIR_SCOPE = (
    ("access_snapshot", "phase36-access"),
    ("mechanical_configuration", "phase36-config"),
    ("field_context", "phase36-field"),
    ("scale", "phase36-scale"),
    ("genealogy", "phase36-genealogy"),
    ("execution_lineage", "phase36-lineage"),
    ("pair_scope", "phase36-pair"),
)


def _trace(base, registry, index, *, trace_id=None):
    contract = base.contracts[0]
    trace_id = trace_id or f"phase36-trace-{index}"
    scope = (
        ("access_snapshot", "phase36-access"),
        ("acquisition_instance", f"phase36-acquisition-{index}"),
        ("acquisition_channel", CHANNEL),
        ("acquisition_trace", trace_id),
    )
    root = TrustRoot(
        trust_root_id=f"phase36-trace-root-{index}",
        contract_id=contract.contract_id,
        contract_version=contract.version,
        contract_semantic_hash=contract.semantic_hash,
        trusted_scope=scope,
        permitted_channels=(CHANNEL,),
        authority_identity="EXPLICIT_TEST_CONFIGURATION",
    )
    base = base.register_trust_root(root, externally_authorized=True)
    assertion = GroundingAssertion.create(
        assertion_id=f"phase36-trace-assertion-{index}",
        contract_id=contract.contract_id,
        contract_version=contract.version,
        contract_semantic_hash=contract.semantic_hash,
        claimed_trust_root_id=root.trust_root_id,
        acquisition_instance_id=f"phase36-acquisition-{index}",
        acquisition_channel_id=CHANNEL,
        trace_id=trace_id,
        mechanical_scope=scope,
        provenance=("EXPLICIT_TEST_ACQUISITION",),
    )
    base = base.record_assertion(assertion)
    validation = base.validate_assertion(assertion, registry)
    assert validation.valid
    return base.accept_validation(validation), validation.proposition


def _two_traces():
    registry = default_proposition_type_registry(ROOT)
    base = default_grounding_registry(ROOT)
    base, first = _trace(base, registry, 1)
    base, second = _trace(base, registry, 2)
    return base, registry, first, second


def _pair_setup(*, reverse=False, pair_scope=PAIR_SCOPE):
    base, registry, first, second = _two_traces()
    contract = base.contracts[1]
    root = TrustRoot(
        trust_root_id="phase36-pair-root",
        contract_id=contract.contract_id,
        contract_version=contract.version,
        contract_semantic_hash=contract.semantic_hash,
        trusted_scope=pair_scope,
        permitted_channels=(),
        authority_identity="EXPLICIT_TEST_PAIR_CONFIGURATION",
    )
    base = base.register_trust_root(root, externally_authorized=True)
    propositions = (second, first) if reverse else (first, second)
    traces = ("phase36-trace-2", "phase36-trace-1") if reverse else (
        "phase36-trace-1",
        "phase36-trace-2",
    )
    assertion = PairwiseGroundingAssertion.create(
        assertion_id="phase36-pair-assertion-reversed" if reverse else (
            "phase36-pair-assertion"
        ),
        contract_id=contract.contract_id,
        contract_version=contract.version,
        contract_semantic_hash=contract.semantic_hash,
        claimed_trust_root_id=root.trust_root_id,
        parent_proposition_ids=tuple(
            item.proposition_id for item in propositions
        ),
        parent_trace_ids=traces,
        mechanical_scope=pair_scope,
        provenance=("EXPLICIT_TEST_PAIR_NON_IDENTITY",),
    )
    base = base.record_pairwise_assertion(assertion)
    validation = base.validate_pairwise_assertion(assertion, registry)
    return base, registry, first, second, assertion, validation


def test_amendment_08_boot_hash_and_non_mechanical_clause_roles():
    path = ROOT / AMENDMENT_08_SOURCE
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        EXPECTED_AMENDMENT_08_SHA256
    )
    assert AMENDMENT_08_SOURCE in verify_authoritative_boot(ROOT).authoritative_files
    clauses = compile_authoritative_clause_registry(ROOT)
    roles = {
        clauses.get(name).execution_role
        for name in (
            "pairwise_grounding.semantics",
            "pairwise_grounding.contract",
            "pairwise_grounding.firewalls",
            "pairwise_grounding.kernel_support",
            "pairwise_grounding.frontier",
        )
    }
    assert "FUNDAMENTAL_CAUSAL_MECHANICS" not in roles
    assert "MECHANICAL_INFERENCE_RULE" not in roles


def test_phase36_default_state_is_zero_trust_and_non_generative():
    base = default_grounding_registry(ROOT)
    registry = default_proposition_type_registry(ROOT)
    assert base.grounding_contract_count == 2
    assert base.trusted_root_count == 0
    assert base.grounding_assertion_count == 0
    assert base.pairwise_assertion_count == 0
    assert base.grounded_premise_count == 0
    assert base.pairwise_grounded_premise_count == 0
    assert registry.type_count == 6
    assert registry.get(
        PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES
    ).constructor_policy == ConstructorPolicy.TRUSTED_GROUNDING_ONLY
    assert default_mechanical_rule_registry(ROOT).mechanical_rule_count == 1


def test_pair_type_has_only_trusted_constructor_and_no_difference_fields():
    registry = default_proposition_type_registry(ROOT)
    with pytest.raises(PermissionError):
        registry.create_instance(
            PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES,
            human_label="distinct",
        )
    names = {item.name for item in fields(PairwiseGroundingAssertion)}
    assert {
        "payload",
        "hash",
        "timestamp",
        "source_identity",
        "source_difference",
        "probability",
        "confidence",
        "difference",
    }.isdisjoint(names)


def test_valid_pairwise_assertion_preserves_parents_roots_scope_and_origin():
    base, _, first, second, _, validation = _pair_setup()
    assert validation.valid
    proposition = validation.proposition
    accepted = base.accept_pairwise_validation(validation)
    assert accepted.pairwise_grounded_premise_count == 1
    assert proposition.predicate_type == (
        PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES
    )
    assert proposition.origin == PropositionOrigin.GROUNDED_EXTERNAL
    assert proposition.witness_status == WitnessStatus.WITNESS_FREE
    assert proposition.mechanical_scope == PAIR_SCOPE
    assert proposition.subject_receipt_ids == tuple(
        sorted(first.subject_receipt_ids + second.subject_receipt_ids)
    )
    assert validation.ancestry.trust_root_ids == (
        "phase36-pair-root",
        "phase36-trace-root-1",
        "phase36-trace-root-2",
    )


def test_pair_identity_is_symmetric_but_assertion_history_remains_distinct():
    _, _, _, _, first_assertion, first_validation = _pair_setup()
    _, _, _, _, reverse_assertion, reverse_validation = _pair_setup(reverse=True)
    assert first_validation.valid and reverse_validation.valid
    assert (
        first_validation.proposition.proposition_id
        == reverse_validation.proposition.proposition_id
    )
    assert first_assertion.assertion_id != reverse_assertion.assertion_id
    assert (
        first_validation.validation_id != reverse_validation.validation_id
    )


def test_alternative_pairwise_genealogies_share_one_identity_without_collapse():
    base, registry, _, _, first_assertion, first_validation = _pair_setup()
    pair_contract = base.contracts[1]
    alternate_root = TrustRoot(
        trust_root_id="phase36-pair-root-alternate",
        contract_id=pair_contract.contract_id,
        contract_version=pair_contract.version,
        contract_semantic_hash=pair_contract.semantic_hash,
        trusted_scope=PAIR_SCOPE,
        permitted_channels=(),
        authority_identity="EXPLICIT_TEST_PAIR_CONFIGURATION",
    )
    base = base.register_trust_root(
        alternate_root, externally_authorized=True
    )
    alternate_assertion = PairwiseGroundingAssertion.create(
        assertion_id="phase36-pair-assertion-alternate",
        contract_id=pair_contract.contract_id,
        contract_version=pair_contract.version,
        contract_semantic_hash=pair_contract.semantic_hash,
        claimed_trust_root_id=alternate_root.trust_root_id,
        parent_proposition_ids=first_assertion.parent_proposition_ids,
        parent_trace_ids=first_assertion.parent_trace_ids,
        mechanical_scope=PAIR_SCOPE,
        provenance=("EXPLICIT_TEST_ALTERNATE_PAIR_PATH",),
    )
    base = base.record_pairwise_assertion(alternate_assertion)
    alternate_validation = base.validate_pairwise_assertion(
        alternate_assertion, registry
    )
    assert alternate_validation.valid
    assert (
        alternate_validation.proposition.proposition_id
        == first_validation.proposition.proposition_id
    )
    accepted = base.accept_pairwise_validation(first_validation)
    accepted = accepted.accept_pairwise_validation(alternate_validation)
    assert accepted.pairwise_grounded_premise_count == 1
    assert accepted.pairwise_grounded_genealogy_count == 2
    genealogies = accepted.pairwise_genealogies_for(
        first_validation.proposition.proposition_id
    )
    assert tuple(item.genealogy_id for item in genealogies) == (
        first_validation.validation_id,
        alternate_validation.validation_id,
    )
    assert {
        root
        for item in genealogies
        for root in item.ancestry.trust_root_ids
        if root.startswith("phase36-pair-root")
    } == {"phase36-pair-root", "phase36-pair-root-alternate"}

    revoked = accepted.revoke_trust_root("phase36-pair-root")
    applicability = tuple(
        revoked.genealogy_applicability(item) for item in genealogies
    )
    assert [item.currently_applicable for item in applicability] == [
        False,
        True,
    ]


def test_self_pair_missing_parent_wrong_contract_and_scope_are_rejected():
    base, registry, first, second = _two_traces()
    pair_contract = base.contracts[1]
    root = TrustRoot(
        "phase36-pair-root",
        pair_contract.contract_id,
        pair_contract.version,
        pair_contract.semantic_hash,
        PAIR_SCOPE,
        (),
        "EXPLICIT_TEST_PAIR_CONFIGURATION",
    )
    base = base.register_trust_root(root, externally_authorized=True)

    def validate(parent_ids, trace_ids, **changes):
        assertion = PairwiseGroundingAssertion.create(
            assertion_id=changes.get("assertion_id", "phase36-invalid-pair"),
            contract_id=changes.get("contract_id", pair_contract.contract_id),
            contract_version=pair_contract.version,
            contract_semantic_hash=changes.get(
                "contract_hash", pair_contract.semantic_hash
            ),
            claimed_trust_root_id=root.trust_root_id,
            parent_proposition_ids=parent_ids,
            parent_trace_ids=trace_ids,
            mechanical_scope=changes.get("scope", PAIR_SCOPE),
            provenance=("TEST_INVALID",),
        )
        recorded = base.record_pairwise_assertion(assertion)
        return recorded.validate_pairwise_assertion(assertion, registry)

    assert not validate(
        (first.proposition_id, first.proposition_id),
        ("phase36-trace-1", "phase36-trace-1"),
    ).valid
    assert not validate(
        (first.proposition_id, "missing"),
        ("phase36-trace-1", "missing"),
        assertion_id="phase36-missing-parent",
    ).valid
    assert not validate(
        (first.proposition_id, second.proposition_id),
        ("phase36-trace-1", "phase36-trace-2"),
        assertion_id="phase36-wrong-scope",
        scope=PAIR_SCOPE[:-1],
    ).valid
    assert not validate(
        (first.proposition_id, second.proposition_id),
        ("phase36-trace-1", "phase36-trace-2"),
        assertion_id="phase36-wrong-contract",
        contract_id=base.contracts[0].contract_id,
    ).valid


def test_trace_trust_does_not_authorize_pair_and_revocation_is_historical():
    base, registry, first, second = _two_traces()
    contract = base.contracts[1]
    assertion = PairwiseGroundingAssertion.create(
        assertion_id="phase36-no-pair-root",
        contract_id=contract.contract_id,
        contract_version=contract.version,
        contract_semantic_hash=contract.semantic_hash,
        claimed_trust_root_id="phase36-trace-root-1",
        parent_proposition_ids=(first.proposition_id, second.proposition_id),
        parent_trace_ids=("phase36-trace-1", "phase36-trace-2"),
        mechanical_scope=PAIR_SCOPE,
        provenance=("TEST_NO_PAIR_ROOT",),
    )
    base = base.record_pairwise_assertion(assertion)
    assert not base.validate_pairwise_assertion(assertion, registry).valid

    base, _, _, _, assertion, validation = _pair_setup()
    accepted = base.accept_pairwise_validation(validation)
    revoked = accepted.revoke_trust_root("phase36-pair-root")
    assert accepted.pairwise_grounded_premise_count == 1
    assert revoked.pairwise_grounded_premise_count == 1
    genealogy = type("G", (), {
        "ancestry": validation.ancestry,
        "historically_valid": True,
    })()
    assert not revoked.genealogy_applicability(genealogy).currently_applicable


def test_identical_payload_is_irrelevant_and_copy_replay_cannot_construct():
    base, registry = default_grounding_registry(ROOT), (
        default_proposition_type_registry(ROOT)
    )
    base, first = _trace(base, registry, 1, trace_id="same-payload-trace-1")
    base, second = _trace(base, registry, 2, trace_id="same-payload-trace-2")
    assert first.proposition_id != second.proposition_id
    assert base.pairwise_grounded_premise_count == 0
    assert not hasattr(first, "payload")
    assert not hasattr(second, "payload")
    assert not hasattr(base, "infer_pair_from_access_records")
    assert not hasattr(base, "infer_pair_from_replay")


def test_pairwise_path_stops_at_frontier_without_difference_or_derived_m():
    base, _, _, _, assertion, validation = _pair_setup()
    accepted = base.accept_pairwise_validation(validation)
    state = MExecutionMachine().execute_pairwise_grounded(
        assertion, grounding_base=accepted
    )
    assert state.validation.valid
    assert state.proof_result.frontier == (
        NON_IDENTITY_RULE_REGISTRATION_FRONTIER
    )
    assert state.proof_result.status == "UNRESOLVED"
    assert state.proof_result.new_derived_m_count == 0
    assert all(
        item.predicate_type
        != PropositionType.REAL_DIFFERENCE_EXISTS
        for item in state.proof_result.state.proposition_store
    )
    assert all(
        receipt.operation_name != FIRST_MECHANICAL_RULE_ID
        for receipt in state.proof_result.state.receipt_store
    )
    assert state.proof_result.state.reopen_requests == ()


def test_proof_kernel_preserves_alternative_pairwise_genealogies():
    base, registry, _, _, first_assertion, first_validation = _pair_setup()
    pair_contract = base.contracts[1]
    alternate_root = TrustRoot(
        trust_root_id="phase36-kernel-pair-root-alternate",
        contract_id=pair_contract.contract_id,
        contract_version=pair_contract.version,
        contract_semantic_hash=pair_contract.semantic_hash,
        trusted_scope=PAIR_SCOPE,
        permitted_channels=(),
        authority_identity="EXPLICIT_TEST_PAIR_CONFIGURATION",
    )
    base = base.register_trust_root(
        alternate_root, externally_authorized=True
    )
    alternate_assertion = PairwiseGroundingAssertion.create(
        assertion_id="phase36-kernel-pair-assertion-alternate",
        contract_id=pair_contract.contract_id,
        contract_version=pair_contract.version,
        contract_semantic_hash=pair_contract.semantic_hash,
        claimed_trust_root_id=alternate_root.trust_root_id,
        parent_proposition_ids=first_assertion.parent_proposition_ids,
        parent_trace_ids=first_assertion.parent_trace_ids,
        mechanical_scope=PAIR_SCOPE,
        provenance=("EXPLICIT_TEST_ALTERNATE_PAIR_PATH",),
    )
    base = base.record_pairwise_assertion(alternate_assertion)
    alternate_validation = base.validate_pairwise_assertion(
        alternate_assertion, registry
    )
    proof_result = ProofKernel(
        default_mechanical_rule_registry(ROOT),
        ROOT,
    ).close(
        receipts=(),
        scope=PAIR_SCOPE,
        authority_range="Amendment 08 pairwise execution frontier",
        authority_range_hash="phase36-test-frontier",
        grounding_validations=(first_validation, alternate_validation),
    )
    assert proof_result.state.proposition_store == (
        first_validation.proposition,
    )
    assert tuple(
        item.genealogy_id
        for item in proof_result.state.grounding_genealogies
    ) == (
        first_validation.validation_id,
        alternate_validation.validation_id,
    )
    assert proof_result.new_propositions == (
        first_validation.proposition,
    )


def test_generic_exact_matching_and_ancestry_composition_are_non_generative():
    _, _, first, second, _, validation = _pair_setup()
    pair = validation.proposition
    assert ProofKernel.exact_proposition_match(
        pair,
        required_type=(
            PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES
        ),
        allowed_origins=(PropositionOrigin.GROUNDED_EXTERNAL,),
        exact_scope=PAIR_SCOPE,
        required_subject_receipt_ids=pair.subject_receipt_ids,
    )
    assert not ProofKernel.exact_proposition_match(
        pair,
        required_type=PropositionType.REAL_DIFFERENCE_EXISTS,
        allowed_origins=(PropositionOrigin.GROUNDED_EXTERNAL,),
        exact_scope=PAIR_SCOPE,
    )
    assert not ProofKernel.exact_proposition_match(
        pair,
        required_type=pair.predicate_type,
        allowed_origins=(PropositionOrigin.DERIVED_M,),
        exact_scope=PAIR_SCOPE,
    )
    composed = ProofKernel.compose_grounding_ancestry(
        (first, second), exact_scope=PAIR_SCOPE
    )
    assert composed.trust_root_ids == (
        "phase36-trace-root-1",
        "phase36-trace-root-2",
    )
    assert ProofKernel.compose_grounding_ancestry(
        (), exact_scope=PAIR_SCOPE
    ).trust_root_ids == ()