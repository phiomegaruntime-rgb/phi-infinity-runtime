import hashlib
from dataclasses import fields, replace
from pathlib import Path

import pytest

from m_machine import (
    AMENDMENT_07_SOURCE,
    EXPECTED_AMENDMENT_07_SHA256,
    FIRST_MECHANICAL_RULE_ID,
    POST_GROUNDING_MECHANICAL_RECONSTRUCTION_FRONTIER,
    RAW_MECHANICAL_BOOTSTRAP_FRONTIER,
    AccessLocalHandle,
    AccessPackage,
    AccessRecord,
    BasisAccess,
    BasisOrigin,
    BasisRecord,
    ConstructorPolicy,
    DirectOutcomeRelation,
    GroundedProofGenealogy,
    GroundingAncestry,
    GroundingAssertion,
    LocalReferentMap,
    MExecutionMachine,
    OriginProvenance,
    OutcomeBasisBinding,
    OutcomeRecord,
    PropositionOrigin,
    PropositionType,
    ReplayState,
    RelationWitness,
    TrustRoot,
    WitnessStatus,
    compile_authoritative_clause_registry,
    default_grounding_registry,
    default_mechanical_rule_registry,
    default_proposition_type_registry,
)


ROOT = Path(__file__).resolve().parents[1]
CHANNEL = "EXPLICIT_ACQUISITION_CHANNEL"
SCOPE = (
    ("access_snapshot", "phase32-access"),
    ("acquisition_instance", "phase32-acquisition"),
    ("acquisition_channel", CHANNEL),
    ("acquisition_trace", "phase32-trace"),
)


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
        access_instance="phase32-access",
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


def _root(base=None, *, root_id="phase32-root", scope=SCOPE):
    base = base or default_grounding_registry(ROOT)
    contract = base.contracts[0]
    return TrustRoot(
        trust_root_id=root_id,
        contract_id=contract.contract_id,
        contract_version=contract.version,
        contract_semantic_hash=contract.semantic_hash,
        trusted_scope=scope,
        permitted_channels=(CHANNEL,),
        authority_identity="EXPLICIT_TEST_CONFIGURATION",
    )


def _assertion(
    base=None,
    *,
    assertion_id="phase32-assertion",
    root_id="phase32-root",
    scope=SCOPE,
    channel=CHANNEL,
    replay_state=ReplayState.FRESH,
    currently_applicable=True,
):
    base = base or default_grounding_registry(ROOT)
    contract = base.contracts[0]
    return GroundingAssertion.create(
        assertion_id=assertion_id,
        contract_id=contract.contract_id,
        contract_version=contract.version,
        contract_semantic_hash=contract.semantic_hash,
        claimed_trust_root_id=root_id,
        acquisition_instance_id="phase32-acquisition",
        acquisition_channel_id=channel,
        trace_id=f"trace-{assertion_id}",
        mechanical_scope=scope,
        provenance=("explicit test acquisition assertion",),
        replay_state=replay_state,
        currently_applicable=currently_applicable,
    )


def _trusted_base(root_id="phase32-root"):
    base = default_grounding_registry(ROOT)
    return base.register_trust_root(
        _root(base, root_id=root_id),
        externally_authorized=True,
    )


def _validate(base, assertion):
    recorded = base.record_assertion(assertion)
    validation = recorded.validate_assertion(
        assertion,
        default_proposition_type_registry(ROOT),
    )
    return recorded, validation


def test_amendment_07_exact_hash_and_noncausal_clause_roles():
    path = ROOT / AMENDMENT_07_SOURCE
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        EXPECTED_AMENDMENT_07_SHA256
    )
    clauses = compile_authoritative_clause_registry(ROOT)
    grounding = tuple(
        item for item in clauses.entries if item.clause_id.startswith("grounding.")
    )
    assert grounding
    assert {
        item.execution_role for item in grounding
    } == {
        "TRUSTED_GROUNDING_SEMANTICS",
        "EXTERNAL_EPISTEMIC_ACQUISITION_INTERFACE",
        "NON_GENERATIVE_GROUNDING_SUBSTRATE",
    }
    assert all(
        item.execution_role != "FUNDAMENTAL_CAUSAL_MECHANICS"
        for item in grounding
    )


def test_contract_exists_with_zero_default_trust_assertions_and_premises():
    base = default_grounding_registry(ROOT)
    assert base.grounding_contract_count == 2
    assert base.trusted_root_count == 0
    assert base.grounding_assertion_count == 0
    assert base.grounded_premise_count == 0


def test_contract_presence_does_not_register_trust_or_construct_propositions():
    base = default_grounding_registry(ROOT)
    registry = default_proposition_type_registry(ROOT)
    assert registry.type_count == 6
    assert base.trust_roots == ()
    assert base.grounded_premises == ()


def test_trust_root_requires_explicit_external_registration():
    base = default_grounding_registry(ROOT)
    with pytest.raises(PermissionError, match="external authorization"):
        base.register_trust_root(_root(base))
    accepted = base.register_trust_root(
        _root(base),
        externally_authorized=True,
    )
    assert accepted.trusted_root_count == 1
    assert base.trusted_root_count == 0


def test_assertion_cannot_self_register_a_trust_root():
    base = default_grounding_registry(ROOT)
    assertion = _assertion(base)
    recorded, validation = _validate(base, assertion)
    assert recorded.trusted_root_count == 0
    assert not validation.valid
    assert validation.proposition is None
    assert recorded.grounded_premise_count == 0


@pytest.mark.parametrize(
    "mutation",
    [
        {"contract_id": "wrong-contract"},
        {"contract_version": "wrong-version"},
        {"contract_semantic_hash": "0" * 64},
        {"claimed_trust_root_id": "wrong-root"},
        {"acquisition_channel_id": "wrong-channel"},
        {
            "mechanical_scope": (
                ("access_snapshot", "other"),
                ("acquisition_instance", "phase32-acquisition"),
                ("acquisition_channel", CHANNEL),
                ("acquisition_trace", "phase32-trace"),
            )
        },
    ],
)
def test_wrong_contract_root_channel_or_scope_creates_no_premise(mutation):
    base = _trusted_base()
    seed = _assertion(base)
    data = {
        "assertion_id": seed.assertion_id,
        "contract_id": seed.contract_id,
        "contract_version": seed.contract_version,
        "contract_semantic_hash": seed.contract_semantic_hash,
        "claimed_trust_root_id": seed.claimed_trust_root_id,
        "acquisition_instance_id": seed.acquisition_instance_id,
        "acquisition_channel_id": seed.acquisition_channel_id,
        "trace_id": seed.trace_id,
        "mechanical_scope": seed.mechanical_scope,
        "provenance": seed.provenance,
        "replay_state": seed.replay_state,
        "historically_valid": seed.historically_valid,
        "currently_applicable": seed.currently_applicable,
    }
    data.update(mutation)
    assertion = GroundingAssertion.create(**data)
    recorded, validation = _validate(base, assertion)
    assert not validation.valid
    assert validation.proposition is None
    assert recorded.accept_validation(validation).grounded_premise_count == 0


def test_valid_assertion_is_non_generatively_validated():
    base = _trusted_base()
    assertion = _assertion(base)
    recorded, validation = _validate(base, assertion)
    assert validation.valid
    assert validation.receipt.status == "GROUNDED_EXTERNAL"
    assert "physical truth" not in validation.reason.lower()
    accepted = recorded.accept_validation(validation)
    assert accepted.grounded_premise_count == 1


def test_semantic_labels_probability_and_confidence_are_not_inputs():
    assertion_fields = {item.name for item in fields(GroundingAssertion)}
    contract_fields = {item.name for item in fields(type(default_grounding_registry(ROOT).contracts[0]))}
    for forbidden in (
        "grounded",
        "human_label",
        "probability",
        "confidence",
        "majority",
        "source_identity",
        "source_difference",
    ):
        assert forbidden not in assertion_fields
        assert forbidden not in contract_fields


def test_signature_or_matching_content_alone_cannot_ground():
    base = default_grounding_registry(ROOT)
    assertion = _assertion(base)
    recorded, validation = _validate(base, assertion)
    assert assertion.integrity_hash == assertion.expected_integrity_hash
    assert not validation.valid
    assert recorded.grounded_premises == ()


def test_trace_type_origin_policy_and_witness_firewall():
    registry = default_proposition_type_registry(ROOT)
    spec = registry.get(PropositionType.REAL_ACQUISITION_TRACE_EXISTS)
    assert spec.constructor_policy == ConstructorPolicy.TRUSTED_GROUNDING_ONLY
    base = _trusted_base()
    recorded, validation = _validate(base, _assertion(base))
    proposition = validation.proposition
    assert proposition.predicate_type == (
        PropositionType.REAL_ACQUISITION_TRACE_EXISTS
    )
    assert proposition.origin == PropositionOrigin.GROUNDED_EXTERNAL
    assert proposition.witness_status == WitnessStatus.WITNESS_FREE
    assert proposition.proof_genealogies == ()
    assert recorded.accept_validation(validation).grounded_premise_count == 1


def test_direct_caller_cannot_construct_trace_proposition():
    registry = default_proposition_type_registry(ROOT)
    with pytest.raises(PermissionError):
        registry.create_instance(
            PropositionType.REAL_ACQUISITION_TRACE_EXISTS,
            grounded=True,
        )
    with pytest.raises(PermissionError):
        registry.enforce_constructor_policy(
            PropositionType.REAL_ACQUISITION_TRACE_EXISTS,
            constructor_kind="CALLER",
            raw_scope=False,
        )


def test_grounding_constructs_only_exact_trace_proposition():
    base = _trusted_base()
    recorded, validation = _validate(base, _assertion(base))
    accepted = recorded.accept_validation(validation)
    assert tuple(
        item.predicate_type for item in accepted.grounded_premises
    ) == (PropositionType.REAL_ACQUISITION_TRACE_EXISTS,)
    assert all(
        item.predicate_type != PropositionType.REAL_DIFFERENCE_EXISTS
        for item in accepted.grounded_premises
    )
    assert all(
        item.predicate_type != PropositionType.REAL_CONSEQUENCE_EXISTS
        for item in accepted.grounded_premises
    )


def test_source_semantics_and_mother_mechanics_are_not_generated():
    base = _trusted_base()
    recorded, validation = _validate(base, _assertion(base))
    proposition = recorded.accept_validation(validation).grounded_premises[0]
    forbidden = {
        "source_identity",
        "source_event",
        "source_difference",
        "dependency",
        "exchange",
        "transformation",
        "propagation",
        "continuation",
        "cause",
    }
    assert forbidden.isdisjoint({item.name for item in fields(proposition)})


def test_real_difference_constructor_remains_unauthorized():
    registry = default_proposition_type_registry(ROOT)
    assert registry.get(
        PropositionType.REAL_DIFFERENCE_EXISTS
    ).constructor_policy == ConstructorPolicy.NO_CONSTRUCTOR_CURRENTLY_AUTHORIZED
    with pytest.raises(PermissionError):
        registry.enforce_constructor_policy(
            PropositionType.REAL_DIFFERENCE_EXISTS,
            constructor_kind="TRUSTED_GROUNDING",
            raw_scope=False,
            trusted_grounding_valid=True,
        )


def test_grounded_trace_cannot_satisfy_first_theorem_premise():
    machine = MExecutionMachine()
    base = _trusted_base()
    recorded, validation = _validate(base, _assertion(base))
    premise = recorded.accept_validation(validation).grounded_premises[0]
    rule = default_mechanical_rule_registry(ROOT).mechanical_rules[0]
    assert machine.proof_kernel.exact_proposition_premise_match(
        rule, (premise,)
    ) is None
    assert rule.rule_id == FIRST_MECHANICAL_RULE_ID


def test_grounded_premise_preserves_exact_ancestry():
    base = _trusted_base()
    assertion = _assertion(base)
    recorded, validation = _validate(base, assertion)
    proposition = recorded.accept_validation(validation).grounded_premises[0]
    ancestry = proposition.grounding_ancestry
    contract = base.contracts[0]
    assert ancestry.trust_root_ids == ("phase32-root",)
    assert ancestry.contract_references == (contract.reference,)
    assert ancestry.assertion_ids == (assertion.assertion_id,)
    assert ancestry.acquisition_channel_ids == (CHANNEL,)
    assert ancestry.trace_ids == (assertion.trace_id,)
    assert ancestry.mechanical_scope == SCOPE


def test_root_union_is_exact_deterministic_and_allows_root_free_propositions():
    first = GroundingAncestry(
        trust_root_ids=("G1",),
        contract_references=("C1",),
        assertion_ids=("A1",),
        mechanical_scope=SCOPE,
    )
    second = GroundingAncestry(
        trust_root_ids=("G2",),
        contract_references=("C2",),
        assertion_ids=("A2",),
        mechanical_scope=SCOPE,
    )
    union = GroundingAncestry.union(second, first)
    assert union.trust_root_ids == ("G1", "G2")
    assert union.contract_references == ("C1", "C2")
    assert GroundingAncestry.union().trust_root_ids == ()
    assert not hasattr(union, "dependency")


def test_replay_is_historical_but_not_current_and_creates_no_premise():
    base = _trusted_base()
    assertion = _assertion(base, replay_state=ReplayState.REPLAYED)
    recorded, validation = _validate(base, assertion)
    assert assertion.historically_valid
    assert not validation.valid
    assert "Replayed" in validation.reason
    assert recorded.grounding_assertion_count == 1
    assert recorded.grounded_premise_count == 0


@pytest.mark.parametrize("kind", ["root", "contract", "assertion", "channel"])
def test_revocation_preserves_history_and_invalidates_current_genealogy(kind):
    base = _trusted_base()
    assertion = _assertion(base)
    recorded, validation = _validate(base, assertion)
    accepted = recorded.accept_validation(validation)
    ancestry = validation.ancestry
    genealogy = GroundedProofGenealogy(
        "genealogy", validation.proposition.proposition_id, ancestry
    )
    contract = base.contracts[0]
    revoked = {
        "root": lambda: accepted.revoke_trust_root("phase32-root"),
        "contract": lambda: accepted.revoke_contract(contract.reference),
        "assertion": lambda: accepted.revoke_assertion(assertion.assertion_id),
        "channel": lambda: accepted.revoke_channel(CHANNEL),
    }[kind]()
    applicability = revoked.genealogy_applicability(genealogy)
    assert applicability.historically_valid
    assert not applicability.currently_applicable
    assert revoked.grounding_assertion_count == 1
    assert revoked.grounded_premise_count == 1


def test_selective_invalidation_is_genealogy_specific():
    base = _trusted_base("G1")
    base = base.register_trust_root(
        _root(base, root_id="G2"),
        externally_authorized=True,
    )
    g1 = GroundedProofGenealogy(
        "proof-a",
        "same-proposition",
        GroundingAncestry(trust_root_ids=("G1",), mechanical_scope=SCOPE),
    )
    g2 = GroundedProofGenealogy(
        "proof-b",
        "same-proposition",
        GroundingAncestry(trust_root_ids=("G2",), mechanical_scope=SCOPE),
    )
    revoked = base.revoke_trust_root("G1")
    assert not revoked.genealogy_applicability(g1).currently_applicable
    assert revoked.genealogy_applicability(g2).currently_applicable
    assert g1.proposition_id == g2.proposition_id


def test_multiple_grounded_assertions_are_preserved_without_voting():
    base = _trusted_base("G1")
    base = base.register_trust_root(
        _root(base, root_id="G2"),
        externally_authorized=True,
    )
    first = _assertion(base, assertion_id="A1", root_id="G1")
    second = _assertion(base, assertion_id="A2", root_id="G2")
    for assertion in (first, second):
        base, validation = _validate(base, assertion)
        base = base.accept_validation(validation)
    assert base.grounded_premise_count == 2
    assert base.trusted_root_count == 2
    assert not hasattr(base, "winning_root")
    assert not hasattr(base, "majority")


def test_default_raw_end_to_end_remains_unchanged():
    machine = MExecutionMachine()
    result = machine.execute(_package())
    assert machine.raw_rule_registry.mechanical_rule_count == 1
    assert machine.grounding_base.trusted_root_count == 0
    assert machine.grounding_base.grounding_assertion_count == 0
    assert machine.grounding_base.grounded_premise_count == 0
    assert result.status == "UNRESOLVED"
    assert result.frontier == RAW_MECHANICAL_BOOTSTRAP_FRONTIER
    assert not any(item.status == "GROUNDED_EXTERNAL" for item in result.receipts)
    assert not any(item.status == "DERIVED_M" for item in result.receipts if item.operation_name == FIRST_MECHANICAL_RULE_ID)


def test_explicit_grounded_end_to_end_stops_at_post_grounding_frontier():
    machine = MExecutionMachine()
    base = _trusted_base()
    assertion = _assertion(base)
    result = machine.execute_grounded(
        _package(),
        assertion,
        grounding_base=base,
    )
    state = result.value
    assert result.status == "UNRESOLVED"
    assert result.frontier == POST_GROUNDING_MECHANICAL_RECONSTRUCTION_FRONTIER
    assert result.reopen_request is None
    assert state.validation.valid
    assert state.grounding_base.grounded_premise_count == 1
    assert len(state.proof_result.new_propositions) == 1
    assert state.proof_result.new_derived_m_count == 0
    assert not any(
        item.operation_name == FIRST_MECHANICAL_RULE_ID
        for item in result.receipts
    )
    assert not any(
        item.predicate_type == PropositionType.REAL_DIFFERENCE_EXISTS
        for item in state.proof_result.state.proposition_store
    )


def test_invalid_explicit_grounding_stays_raw_and_creates_no_reopen():
    machine = MExecutionMachine()
    base = default_grounding_registry(ROOT)
    result = machine.execute_grounded(
        _package(),
        _assertion(base),
        grounding_base=base,
    )
    assert result.status == "UNRESOLVED"
    assert result.frontier == RAW_MECHANICAL_BOOTSTRAP_FRONTIER
    assert result.reopen_request is None
    assert not result.value.validation.valid
    assert result.value.grounding_base.grounded_premise_count == 0