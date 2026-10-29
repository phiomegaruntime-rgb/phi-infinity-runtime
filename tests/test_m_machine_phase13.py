from pathlib import Path
from unittest.mock import patch

from m_machine import (
    ACCESS_DISCRIMINABILITY_RECEIPT_STATUS,
    AMENDMENT_04_SOURCE,
    AccessLocalHandle,
    AccessPackage,
    AccessRecord,
    BasisAccess,
    BasisLocalDiscriminabilitySet,
    BasisOrigin,
    BasisRecord,
    DirectOutcomeRelation,
    LocalReferentMap,
    MExecutionMachine,
    OriginProvenance,
    OutcomeBasisBinding,
    OutcomeClassMap,
    OutcomeRecord,
    RelationWitness,
    ResolutionClass,
    compile_authoritative_clause_registry,
    evaluate_basis_local,
    verify_authoritative_boot,
)


def _case(
    *,
    access_instance="access-a",
    basis_token="basis",
    basis_origin="SUPPLIED_AS_ACCESS_BASIS",
    class_relation=None,
    direct_relation=None,
    first_raw=1,
    second_raw=2,
):
    first = AccessRecord(first_raw)
    second = AccessRecord(second_raw)
    first_handle = AccessLocalHandle("first")
    second_handle = AccessLocalHandle("second")
    witness = RelationWitness("witness", first_handle, second_handle)
    basis = BasisRecord(basis_token)
    first_outcome = OutcomeRecord("outcome-first", first_raw)
    second_outcome = OutcomeRecord("outcome-second", second_raw)
    first_class = ResolutionClass("class-first")
    second_class = ResolutionClass("class-second")
    class_maps = ()
    if class_relation == "same":
        class_maps = (
            OutcomeClassMap(
                basis,
                ((first_outcome, first_class), (second_outcome, first_class)),
            ),
        )
    elif class_relation == "different":
        class_maps = (
            OutcomeClassMap(
                basis,
                ((first_outcome, first_class), (second_outcome, second_class)),
            ),
        )
    elif class_relation == "missing":
        class_maps = (
            OutcomeClassMap(basis, ((first_outcome, first_class),)),
        )
    elif class_relation == "ambiguous":
        class_maps = (
            OutcomeClassMap(
                basis,
                (
                    (first_outcome, first_class),
                    (first_outcome, second_class),
                    (second_outcome, first_class),
                ),
            ),
        )
    direct_relations = ()
    if direct_relation is not None:
        direct_relations = (
            DirectOutcomeRelation(
                basis,
                first_outcome,
                second_outcome,
                direct_relation,
            ),
        )
    origins = (
        ()
        if basis_origin is None
        else (BasisOrigin(basis, basis_origin),)
    )
    basis_access = BasisAccess(
        bases=(basis,),
        origins=origins,
        outcomes=(first_outcome, second_outcome),
        bindings=(
            OutcomeBasisBinding(basis, first, first_outcome),
            OutcomeBasisBinding(basis, second, second_outcome),
        ),
        class_maps=class_maps,
        direct_relations=direct_relations,
    )
    package = AccessPackage(
        access_instance=access_instance,
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
        basis_access=basis_access,
    )
    return {
        "package": package,
        "first": first,
        "second": second,
        "witness": witness,
        "basis": basis,
        "first_outcome": first_outcome,
        "second_outcome": second_outcome,
        "first_class": first_class,
        "second_class": second_class,
        "basis_access": basis_access,
    }


def _evaluate(case):
    return evaluate_basis_local(
        case["package"],
        case["witness"],
        case["first"],
        case["second"],
        case["basis"],
    )


def test_supplied_basis_origin_qualifies():
    case = _case(class_relation="different")

    assert _evaluate(case).status == "DISCRIMINABLE_UNDER_BASIS"


def test_post_hoc_basis_does_not_qualify():
    case = _case(
        basis_origin="DERIVED_AFTER_ACCESS",
        class_relation="different",
    )

    assert _evaluate(case).status == "UNRESOLVED"


def test_missing_basis_origin_is_unresolved():
    case = _case(basis_origin=None, class_relation="different")

    assert _evaluate(case).status == "UNRESOLVED"


def test_exact_supplied_class_membership_resolves():
    case = _case(class_relation="different")
    class_map = case["basis_access"].class_maps[0]

    assert class_map.resolve(case["first_outcome"]) == (
        case["first_class"],
    )


def test_missing_class_membership_is_unresolved():
    case = _case(class_relation="missing")

    assert _evaluate(case).status == "UNRESOLVED"


def test_ambiguous_class_membership_is_unresolved():
    case = _case(class_relation="ambiguous")

    assert _evaluate(case).status == "UNRESOLVED"


def test_same_class_is_not_discriminated_under_basis_only():
    case = _case(class_relation="same")
    result = _evaluate(case)

    assert result.status == "NOT_DISCRIMINATED_UNDER_BASIS"
    assert result.relation == "NOT_SEPARATELY_RESOLVED"


def test_different_classes_are_discriminable_under_basis_only():
    case = _case(class_relation="different")
    result = _evaluate(case)

    assert result.status == "DISCRIMINABLE_UNDER_BASIS"
    assert result.relation == "SEPARATELY_RESOLVED"


def test_same_class_does_not_emit_ontological_identity():
    result = _evaluate(_case(class_relation="same"))

    assert not hasattr(result, "ontological_identity")
    assert not hasattr(result, "same_manifestation")
    assert not hasattr(result, "delta")


def test_different_classes_do_not_emit_dependency_or_causation():
    result = _evaluate(_case(class_relation="different"))

    assert not hasattr(result, "dependency")
    assert not hasattr(result, "causation")
    assert not hasattr(result, "mechanical_relevance")


def test_different_raw_numbers_without_supplied_relation_are_unresolved():
    case = _case(first_raw=1.0, second_raw=999.0)

    assert _evaluate(case).status == "UNRESOLVED"


def test_equal_raw_numbers_with_different_classes_preserve_distinction():
    case = _case(
        first_raw=5.0,
        second_raw=5.0,
        class_relation="different",
    )

    assert _evaluate(case).status == "DISCRIMINABLE_UNDER_BASIS"


def test_different_raw_numbers_with_same_class_preserve_non_discrimination():
    case = _case(
        first_raw=-100.0,
        second_raw=100.0,
        class_relation="same",
    )

    assert _evaluate(case).status == "NOT_DISCRIMINATED_UNDER_BASIS"


def test_direct_separately_resolved_relation_needs_no_class_map():
    case = _case(direct_relation="SEPARATELY_RESOLVED")

    assert _evaluate(case).status == "DISCRIMINABLE_UNDER_BASIS"


def test_direct_not_separately_resolved_relation_needs_no_class_map():
    case = _case(direct_relation="NOT_SEPARATELY_RESOLVED")

    assert _evaluate(case).status == "NOT_DISCRIMINATED_UNDER_BASIS"


def test_conflicting_class_and_direct_relation_is_unresolved():
    case = _case(
        class_relation="different",
        direct_relation="NOT_SEPARATELY_RESOLVED",
    )

    assert _evaluate(case).status == "UNRESOLVED"


def test_unresolved_direct_relation_is_preserved_as_unresolved():
    case = _case(direct_relation="OUTCOME_RELATION_UNRESOLVED")

    assert _evaluate(case).status == "UNRESOLVED"


def test_same_class_token_text_across_bases_has_no_shared_identity():
    first_class = ResolutionClass("same-text")
    second_class = ResolutionClass("same-text")

    assert first_class is not second_class
    assert first_class != second_class


def test_same_basis_token_text_across_accesses_has_no_shared_identity():
    first_case = _case(
        access_instance="first-access",
        basis_token="same-text",
        class_relation="different",
    )
    second_case = _case(
        access_instance="second-access",
        basis_token="same-text",
        class_relation="different",
    )

    foreign_result = evaluate_basis_local(
        first_case["package"],
        first_case["witness"],
        first_case["first"],
        first_case["second"],
        second_case["basis"],
    )
    assert foreign_result.status == "UNRESOLVED"


def test_human_looking_labels_cannot_override_same_class():
    case = _case(
        first_raw="semantically-left",
        second_raw="semantically-right",
        class_relation="same",
    )

    assert _evaluate(case).status == "NOT_DISCRIMINATED_UNDER_BASIS"


def _two_basis_package():
    base = _case(class_relation="different")
    first = base["first"]
    second = base["second"]
    witness = base["witness"]
    first_basis = base["basis"]
    first_outcome = base["first_outcome"]
    second_outcome = base["second_outcome"]
    first_map = base["basis_access"].class_maps[0]

    second_basis = BasisRecord("basis-two")
    second_first_outcome = OutcomeRecord("b2-first", 100)
    second_second_outcome = OutcomeRecord("b2-second", -100)
    shared_class = ResolutionClass("shared")
    second_map = OutcomeClassMap(
        second_basis,
        (
            (second_first_outcome, shared_class),
            (second_second_outcome, shared_class),
        ),
    )
    basis_access = BasisAccess(
        bases=(first_basis, second_basis),
        origins=(
            BasisOrigin(first_basis, "SUPPLIED_AS_ACCESS_BASIS"),
            BasisOrigin(second_basis, "SUPPLIED_AS_ACCESS_BASIS"),
        ),
        outcomes=(
            first_outcome,
            second_outcome,
            second_first_outcome,
            second_second_outcome,
        ),
        bindings=(
            OutcomeBasisBinding(first_basis, first, first_outcome),
            OutcomeBasisBinding(first_basis, second, second_outcome),
            OutcomeBasisBinding(second_basis, first, second_first_outcome),
            OutcomeBasisBinding(second_basis, second, second_second_outcome),
        ),
        class_maps=(first_map, second_map),
    )
    package = AccessPackage(
        access_instance="two-bases",
        manifestations=(first, second),
        local_referent_map=base["package"].local_referent_map,
        supplied_witnesses=(witness,),
        provenance=base["package"].provenance,
        basis_access=basis_access,
    )
    return package, first_basis, second_basis


def test_multiple_basis_local_results_are_preserved_separately():
    package, first_basis, second_basis = _two_basis_package()

    result = MExecutionMachine().execute(package)

    assert isinstance(result.value, BasisLocalDiscriminabilitySet)
    assert tuple(item.basis for item in result.value.results) == (
        first_basis,
        second_basis,
    )
    assert tuple(item.status for item in result.value.results) == (
        "DISCRIMINABLE_UNDER_BASIS",
        "NOT_DISCRIMINATED_UNDER_BASIS",
    )


def test_multiple_basis_results_have_no_vote_or_aggregate():
    package, _, _ = _two_basis_package()
    value = MExecutionMachine().execute(package).value

    assert not hasattr(value, "winner")
    assert not hasattr(value, "majority")
    assert not hasattr(value, "aggregate")
    assert not hasattr(value, "global_discriminable")


def test_no_numerical_epsilon_or_tolerance_path_is_reachable():
    case = _case(first_raw=0.0, second_raw=0.000000001)
    result = _evaluate(case)

    assert result.status == "UNRESOLVED"
    assert "epsilon" not in result.receipt.operation_name
    assert "tolerance" not in result.receipt.operation_name


def test_executor_emits_no_global_discriminable_delta_or_dependency():
    package, _, _ = _two_basis_package()
    result = MExecutionMachine().execute(package)

    assert result.status == "UNRESOLVED"
    assert not hasattr(result.value, "discriminable_a")
    assert not hasattr(result.value, "delta")
    assert not hasattr(result.value, "dependency")
    assert all("delta" not in item.operation_name.lower() for item in result.receipts)
    assert all(
        "dependency" not in item.operation_name.lower()
        for item in result.receipts
    )


def test_executor_preserves_basis_results_then_reaches_mechanical_rule_frontier():
    package, _, _ = _two_basis_package()
    result = MExecutionMachine().execute(package)

    assert result.frontier == "RAW_MECHANICAL_BOOTSTRAP_FRONTIER"
    assert result.reopen_request is None
    assert result.continuation_allowed is False


def test_basis_path_does_not_invoke_external_registry_operation():
    package, _, _ = _two_basis_package()
    machine = MExecutionMachine()

    with patch.object(
        machine.registry,
        "invoke",
        side_effect=AssertionError("external bridge reached"),
    ) as invoke:
        result = machine.execute(package)

    invoke.assert_not_called()
    assert result.frontier == "RAW_MECHANICAL_BOOTSTRAP_FRONTIER"


def test_basis_receipts_are_non_generative_and_amendment_scoped():
    result = _evaluate(_case(class_relation="different"))

    assert result.receipt.status == ACCESS_DISCRIMINABILITY_RECEIPT_STATUS
    assert result.receipt.authoritative_source_file == AMENDMENT_04_SOURCE
    assert result.receipt.implementation_source == (
        "m_machine/discriminability.py"
    )


def test_amendment_04_registry_entries_are_exact_access_representation():
    root = Path(__file__).resolve().parents[1]
    registry = compile_authoritative_clause_registry(root)
    text = (root / AMENDMENT_04_SOURCE).read_bytes().splitlines(
        keepends=True
    )
    clauses = tuple(
        clause
        for clause in registry.entries
        if clause.authoritative_source_file == AMENDMENT_04_SOURCE
    )

    assert len(clauses) == 8
    assert all(clause.execution_role == "ACCESS_REPRESENTATION" for clause in clauses)
    for clause in clauses:
        expected = b"".join(
            text[clause.line_start - 1 : clause.line_end]
        ).decode("utf-8")
        assert clause.exact_source_text == expected
        assert len(clause.exact_source_text_hash) == 64


def test_frozen_mother_and_amendment_03_hashes_remain_unchanged():
    verification = verify_authoritative_boot()
    amendment_03 = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / (
            "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_03_"
            "ACCESS_REPRESENTATION_AND_RELATIONAL_INTEGRITY.md"
        )
    )
    import hashlib

    assert verification.mother_mechanics_sha256 == (
        "0cea8129245b212c04fa776bdc1b718fabf50998a9635e1e06716504fc410f7b"
    )
    assert hashlib.sha256(amendment_03.read_bytes()).hexdigest() == (
        "34b4db2c11a3a1588eb0a23ac10ac26639eb56ac7f4add6405e35d9ad967ef0a"
    )