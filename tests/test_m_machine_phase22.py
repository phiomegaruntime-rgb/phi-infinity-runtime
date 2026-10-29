import hashlib
import inspect
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from m_machine import (
    AMENDMENT_05_SOURCE,
    EXPECTED_AMENDMENT_05_SHA256,
    RAW_MECHANICAL_BOOTSTRAP_FRONTIER,
    AccessLocalHandle,
    AccessPackage,
    AccessRecord,
    BasisAccess,
    BasisOrigin,
    BasisRecord,
    DerivationReceipt,
    DirectOutcomeRelation,
    FrozenRuleRegistry,
    InferenceRule,
    LocalReferentMap,
    MExecutionMachine,
    OriginProvenance,
    OutcomeBasisBinding,
    OutcomeRecord,
    ProofConflict,
    ProofGenealogy,
    ProofKernel,
    ProofState,
    RelationWitness,
    RuleClass,
    compile_authoritative_clause_registry,
    semantic_hash,
    verify_authoritative_boot,
)


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_RANGE = (33, 52)


def _range_hash(
    source: str = AMENDMENT_05_SOURCE,
    line_range: tuple[int, int] = AUTHORITY_RANGE,
) -> str:
    lines = (ROOT / source).read_bytes().splitlines(keepends=True)
    start, end = line_range
    return hashlib.sha256(b"".join(lines[start - 1 : end])).hexdigest()


def _rule(
    *,
    rule_id: str = "test.access.rule",
    rule_class: RuleClass = RuleClass.ACCESS_REPRESENTATION_RULE,
    premise_schema: tuple[str, ...] = ("ACCESS_INTEGRITY",),
    scope_constraints: tuple[str, ...] = ("access",),
    conclusion_schema: str = "exact test conclusion",
    semantic_specification: str = "Exact test-only frozen semantics.",
    authority_range_hash: str | None = None,
    implementation_id: str = "",
    implementation_hash: str = "",
    version: str = "1",
    authorized: bool = False,
) -> InferenceRule:
    return InferenceRule(
        rule_id=rule_id,
        rule_class=rule_class,
        authority_source=AMENDMENT_05_SOURCE,
        authority_range=AUTHORITY_RANGE,
        authority_range_hash=authority_range_hash or _range_hash(),
        semantic_specification=semantic_specification,
        semantic_specification_hash=semantic_hash(semantic_specification),
        premise_schema=premise_schema,
        scope_constraints=scope_constraints,
        conclusion_schema=conclusion_schema,
        unresolved_behavior="UNRESOLVED",
        implementation_id=implementation_id,
        implementation_hash=implementation_hash,
        version=version,
        separately_audited_authorization=authorized,
    )


def _receipt(
    *,
    operation: str = "access.input",
    status: str = "ACCESS_INTEGRITY",
    parents: tuple[str, ...] = (),
) -> DerivationReceipt:
    return DerivationReceipt.create(
        operation_name=operation,
        authoritative_source_file=AMENDMENT_05_SOURCE,
        authoritative_clause="test authority",
        input_receipt_ids=parents,
        accessible_evidence=("anonymous evidence",),
        operation_performed="test operation",
        resulting_difference_or_consequence="test result",
        status=status,
        implementation_source="tests/test_m_machine_phase22.py",
        clause_id="test",
    )


def _implementation_stub():
    return "already frozen test implementation"


def _anonymous_package() -> AccessPackage:
    first = AccessRecord("first")
    second = AccessRecord("second")
    first_handle = AccessLocalHandle("first-handle")
    second_handle = AccessLocalHandle("second-handle")
    witness = RelationWitness(
        "witness",
        first_handle,
        second_handle,
    )
    basis = BasisRecord("basis")
    first_outcome = OutcomeRecord("first-outcome")
    second_outcome = OutcomeRecord("second-outcome")
    return AccessPackage(
        access_instance="anonymous-access",
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


def test_amendment_05_is_boot_verified_and_non_generative():
    verification = verify_authoritative_boot()
    assert AMENDMENT_05_SOURCE in verification.authoritative_files
    assert hashlib.sha256((ROOT / AMENDMENT_05_SOURCE).read_bytes()).hexdigest() == (
        EXPECTED_AMENDMENT_05_SHA256
    )
    clauses = tuple(
        clause
        for clause in compile_authoritative_clause_registry().entries
        if clause.authoritative_source_file == AMENDMENT_05_SOURCE
    )
    assert len(clauses) == 6
    assert all(clause.execution_role == "OPERATIONAL_SEMANTICS" for clause in clauses)


@pytest.mark.parametrize(
    "rule_class",
    [
        RuleClass.ACCESS_REPRESENTATION_RULE,
        RuleClass.EXECUTION_CONTROL_RULE,
    ],
)
def test_non_mechanical_rule_classes_cannot_emit_derived_m(rule_class):
    rule = _rule(rule_class=rule_class)
    registry = FrozenRuleRegistry(repository_root=ROOT).register(rule)
    premise = _receipt()
    conclusion = _receipt(
        operation="forbidden",
        status="DERIVED_M",
        parents=(premise.receipt_id,),
    )
    with pytest.raises(ValueError, match="cannot emit DERIVED_M"):
        ProofKernel(registry).accept_application(
            rule.rule_id,
            (premise,),
            conclusion,
            premise_scope=(("access", "a"),),
            conclusion_scope=(("access", "a"),),
        )


def test_unregistered_mechanical_rule_cannot_execute():
    with pytest.raises(KeyError, match="not uniquely registered"):
        ProofKernel(FrozenRuleRegistry(repository_root=ROOT)).accept_application(
            "missing.mechanical.rule",
            (),
            _receipt(status="DERIVED_M"),
            premise_scope=(),
            conclusion_scope=(),
        )


def test_incomplete_mechanical_metadata_and_semantic_hash_are_rejected():
    incomplete = _rule(
        rule_class=RuleClass.MECHANICAL_INFERENCE_RULE,
        implementation_id="",
        implementation_hash="",
        authorized=False,
    )
    with pytest.raises(ValueError, match="separate audit authorization"):
        FrozenRuleRegistry((incomplete,), ROOT)
    with pytest.raises(ValueError, match="Semantic specification hash mismatch"):
        replace(incomplete, semantic_specification_hash="0" * 64)


def test_authority_and_implementation_hash_mismatches_are_rejected():
    bad_authority = _rule(authority_range_hash="0" * 64)
    with pytest.raises(ValueError, match="authority range hash mismatch"):
        FrozenRuleRegistry((bad_authority,), ROOT)

    source = inspect.getsource(_implementation_stub)
    mechanical = _rule(
        rule_id="test.mechanical.rule",
        rule_class=RuleClass.MECHANICAL_INFERENCE_RULE,
        implementation_id="test implementation",
        implementation_hash=semantic_hash(source),
        authorized=True,
    )
    with pytest.raises(ValueError, match="implementation hash mismatch"):
        FrozenRuleRegistry(repository_root=ROOT).register(
            replace(mechanical, implementation_hash="0" * 64),
            _implementation_stub,
        )


def test_callback_cannot_supply_missing_mechanical_semantics():
    with pytest.raises(ValueError, match="metadata is incomplete"):
        _rule(
            rule_class=RuleClass.MECHANICAL_INFERENCE_RULE,
            semantic_specification="",
            authorized=True,
        )


def test_frozen_raw_registry_has_exactly_one_non_bootstrap_mechanical_rule():
    machine = MExecutionMachine()
    assert machine.raw_rule_registry.mechanical_rule_count == 1
    assert machine.raw_fireable_positive_mechanical_rule_count == 0


def test_exact_typed_premise_matching_rejects_semantic_similarity():
    rule = _rule()
    access_receipt = _receipt(status="ACCESS_INTEGRITY")
    similar_label = _receipt(
        operation="access integrity",
        status="ACCESS_DISCRIMINABILITY",
    )
    assert ProofKernel.exact_premise_match(rule, (access_receipt,)) == (
        access_receipt,
    )
    assert ProofKernel.exact_premise_match(rule, (similar_label,)) is None
    assert ProofKernel.exact_premise_match(
        rule,
        (access_receipt,),
        required_receipt_ids=("not-present",),
    ) is None


def test_scope_transfer_requires_exact_authorized_relation():
    c1 = (("access", "a"), ("basis", "b1"))
    c2 = (("access", "a"), ("basis", "b2"))
    assert ProofKernel.scope_authorized(c1, c1)
    assert not ProofKernel.scope_authorized(c1, c2)
    assert ProofKernel.scope_authorized(c1, c2, ((c1, c2),))


def test_application_preserves_parent_and_rule_genealogy():
    rule = _rule()
    registry = FrozenRuleRegistry(repository_root=ROOT).register(rule)
    premise = _receipt()
    conclusion = _receipt(
        operation="access.output",
        status="ACCESS_INTEGRITY",
        parents=(premise.receipt_id,),
    )
    result = ProofKernel(registry).accept_application(
        rule.rule_id,
        (premise,),
        conclusion,
        premise_scope=(("access", "a"),),
        conclusion_scope=(("access", "a"),),
    )
    assert result.applied
    assert result.genealogy is not None
    assert result.genealogy.parent_receipt_ids == (premise.receipt_id,)
    assert result.genealogy.rule_id == rule.rule_id
    assert result.genealogy.rule_hash == rule.semantic_specification_hash


def test_duplicate_conclusion_preserves_all_proof_genealogies():
    receipt = _receipt()
    registry = FrozenRuleRegistry(repository_root=ROOT)
    state = ProofState((), registry)
    first = ProofGenealogy(receipt.receipt_id, ("p1",), "r1", "1" * 64)
    second = ProofGenealogy(receipt.receipt_id, ("p2",), "r2", "2" * 64)
    state = state.with_receipt(receipt, first).with_receipt(receipt, second)
    assert state.receipt_store == (receipt,)
    assert state.proof_genealogies == (first, second)


def test_history_is_immutable_and_rule_version_changes_identity():
    receipt = _receipt()
    state = ProofState(
        (("access", "a"),),
        FrozenRuleRegistry(repository_root=ROOT),
        (receipt,),
    )
    with pytest.raises(FrozenInstanceError):
        state.receipt_store = ()
    assert _rule(version="1").identity != _rule(version="2").identity


def test_exact_conflict_preserves_both_conclusions_and_marks_unresolved():
    first = _receipt(operation="q")
    second = _receipt(operation="q2")
    conflict = ProofConflict(
        target="q",
        scope=(("access", "a"),),
        conclusion_receipt_ids=(first.receipt_id, second.receipt_id),
        exact_reason="typed mutual exclusion",
    )
    state = ProofState(
        (("access", "a"),),
        FrozenRuleRegistry(repository_root=ROOT),
        receipt_store=(first, second),
        conflicts=(conflict,),
    )
    assert state.receipt_store == (first, second)
    assert state.conflicts == (conflict,)


def test_zero_rule_closure_is_stable_unresolved_without_reopen_or_divergence():
    initial = _receipt()
    kernel = ProofKernel(FrozenRuleRegistry(repository_root=ROOT))
    first = kernel.close(
        receipts=(initial,),
        scope=(("access", "a"),),
        authority_range="test",
        authority_range_hash=_range_hash(),
    )
    second = kernel.close(
        receipts=(initial,),
        scope=(("access", "a"),),
        authority_range="test",
        authority_range_hash=_range_hash(),
    )
    assert first.status == second.status == "UNRESOLVED"
    assert first.frontier == second.frontier
    assert first.new_derived_m_count == second.new_derived_m_count == 0
    assert first.state.reopen_requests == ()
    assert all(receipt.status != "FALSIFICATION_RESULT" for receipt in first.new_receipts)


def test_raw_end_to_end_preserves_access_and_reaches_bootstrap_frontier():
    result = MExecutionMachine().execute(_anonymous_package())
    assert result.status == "UNRESOLVED"
    assert result.frontier == RAW_MECHANICAL_BOOTSTRAP_FRONTIER
    assert result.reopen_request is None
    assert result.value.results[0].status == "DISCRIMINABLE_UNDER_BASIS"
    proof_receipts = tuple(
        receipt
        for receipt in result.receipts
        if receipt.operation_name == "proof_kernel.proof_closure"
    )
    assert len(proof_receipts) == 1
    assert proof_receipts[0].status == "UNRESOLVED"
    assert not hasattr(result.value, "dependency")
    assert not hasattr(result.value, "exchange")
    assert not hasattr(result.value, "continuation")
    assert all(
        receipt.status != "DERIVED_M"
        for receipt in proof_receipts
    )


def test_kernel_exposes_no_candidate_score_rank_or_probability_api():
    forbidden = {
        "candidate_graph",
        "score",
        "rank",
        "probability",
        "optimize",
    }
    assert forbidden.isdisjoint(dir(ProofKernel))
