from pathlib import Path
from unittest.mock import patch

from m_machine import (
    AMENDMENT_03_SOURCE,
    AccessLocalHandle,
    AccessPackage,
    AccessRecord,
    AccessibleUnder_a,
    Binds_a,
    Connects_a,
    HumanTranslationSpace,
    LocalReferentMap,
    MExecutionMachine,
    Origin_a,
    OriginProvenance,
    RawAccessibleConfiguration,
    RelationQualifiedAccess,
    RelationWitness,
    compile_authoritative_clause_registry,
    de_name,
    de_name_access_package,
    verify_authoritative_boot,
)


def _complete_package(
    *,
    access_instance: str = "access-a",
    origin: str = "SUPPLIED_AS_ACCESS_STRUCTURE",
):
    first = AccessRecord({"value": 7})
    second = AccessRecord({"value": 11})
    first_handle = AccessLocalHandle("opaque-1")
    second_handle = AccessLocalHandle("opaque-2")
    witness = RelationWitness(
        witness_id="witness-1",
        endpoint_1=first_handle,
        endpoint_2=second_handle,
    )
    package = AccessPackage(
        access_instance=access_instance,
        manifestations=(first, second),
        local_referent_map=LocalReferentMap(
            ((first_handle, first), (second_handle, second))
        ),
        supplied_witnesses=(witness,),
        provenance=(OriginProvenance(witness.witness_id, origin),),
    )
    return package, first, second, first_handle, second_handle, witness


def test_exact_local_handle_resolution_binds_only_the_supplied_record():
    package, first, second, first_handle, _, _ = _complete_package()

    assert Binds_a(package, first_handle, first).status == "BOUND"
    assert Binds_a(package, first_handle, second).status == "NOT_BOUND"


def test_absent_local_handle_is_unresolved_without_fallback():
    package, first, _, _, _, _ = _complete_package()

    result = Binds_a(package, AccessLocalHandle("absent"), first)

    assert result.status == "UNRESOLVED"
    assert result.value is False


def test_ambiguous_local_handle_is_unresolved():
    first = AccessRecord("same")
    second = AccessRecord("same")
    handle = AccessLocalHandle("duplicate")
    package = AccessPackage(
        access_instance="ambiguous",
        manifestations=(first, second),
        local_referent_map=LocalReferentMap(
            ((handle, first), (handle, second))
        ),
    )

    assert Binds_a(package, handle, first).status == "UNRESOLVED"


def test_semantic_label_cannot_substitute_for_exact_binding():
    package, first, _, _, _, _ = _complete_package()
    semantic_match = AccessRecord("opaque-1")

    result = Binds_a(
        package,
        AccessLocalHandle(str(first.value)),
        semantic_match,
    )

    assert result.status == "UNRESOLVED"


def test_binding_does_not_inspect_numerical_or_value_structure():
    class NoComparison:
        def __eq__(self, other):
            raise AssertionError("record values must not be compared")

    value = NoComparison()
    record = AccessRecord(value)
    handle = AccessLocalHandle("r")
    package = AccessPackage(
        access_instance="identity-only",
        manifestations=(record,),
        local_referent_map=LocalReferentMap(((handle, record),)),
    )

    assert Binds_a(package, handle, record).status == "BOUND"


def test_witness_outside_package_is_not_accessible():
    package, _, _, first_handle, second_handle, _ = _complete_package()
    outsider = RelationWitness("outsider", first_handle, second_handle)

    assert AccessibleUnder_a(package, outsider).status == "NOT_ACCESSIBLE"


def test_directly_contained_witness_is_accessible():
    package, _, _, _, _, witness = _complete_package()

    assert AccessibleUnder_a(package, witness).status == "ACCESSIBLE"


def test_exactly_referenced_witness_is_accessible():
    package, first, second, first_handle, second_handle, witness = (
        _complete_package()
    )
    referenced_package = AccessPackage(
        access_instance="referenced",
        manifestations=(first, second),
        local_referent_map=LocalReferentMap(
            ((first_handle, first), (second_handle, second))
        ),
        witness_referent_map=((AccessLocalHandle("w-ref"), witness),),
        provenance=(
            OriginProvenance(
                witness.witness_id,
                "SUPPLIED_AS_ACCESS_STRUCTURE",
            ),
        ),
    )

    assert (
        AccessibleUnder_a(referenced_package, witness).status
        == "ACCESSIBLE"
    )


def test_missing_origin_is_explicitly_unresolved():
    package, first, second, first_handle, second_handle, witness = (
        _complete_package()
    )
    without_origin = AccessPackage(
        access_instance=package.access_instance,
        manifestations=(first, second),
        local_referent_map=LocalReferentMap(
            ((first_handle, first), (second_handle, second))
        ),
        supplied_witnesses=(witness,),
    )

    assert Origin_a(without_origin, witness).status == "ORIGIN_UNRESOLVED"
    assert Connects_a(without_origin, witness, first, second).status == (
        "UNRESOLVED"
    )


def test_supplied_witness_qualifies_as_direct_access_relation():
    package, first, second, _, _, witness = _complete_package()

    result = Connects_a(package, witness, first, second)

    assert result.status == "CONNECTED"
    assert result.value is True


def test_derived_after_access_origin_is_not_a_direct_access_relation():
    package, first, second, _, _, witness = _complete_package(
        origin="DERIVED_AFTER_ACCESS"
    )

    result = Connects_a(package, witness, first, second)

    assert result.status == "NOT_CONNECTED"
    assert result.value is False


def test_identical_values_under_distinct_handles_do_not_collapse():
    shared_value = {"same": True}
    first = AccessRecord(shared_value)
    second = AccessRecord(shared_value)
    first_handle = AccessLocalHandle("first")
    second_handle = AccessLocalHandle("second")
    package = AccessPackage(
        access_instance="duplicates",
        manifestations=(first, second),
        local_referent_map=LocalReferentMap(
            ((first_handle, first), (second_handle, second))
        ),
    )

    assert Binds_a(package, first_handle, second).status == "NOT_BOUND"
    assert Binds_a(package, second_handle, first).status == "NOT_BOUND"


def test_same_handle_text_does_not_cross_access_instances():
    first_package, first, _, first_handle, _, _ = _complete_package(
        access_instance="first-access"
    )
    second_package, second_first, _, _, _, _ = _complete_package(
        access_instance="second-access"
    )

    assert Binds_a(first_package, first_handle, first).status == "BOUND"
    assert Binds_a(second_package, first_handle, first).status == "UNRESOLVED"
    assert Binds_a(second_package, first_handle, second_first).status == "BOUND"


def test_witness_identity_does_not_cross_access_instances():
    first_package, _, _, _, _, first_witness = _complete_package(
        access_instance="first-access"
    )
    second_package, _, _, _, _, second_witness = _complete_package(
        access_instance="second-access"
    )

    assert AccessibleUnder_a(first_package, first_witness).value is True
    assert AccessibleUnder_a(second_package, first_witness).value is False
    assert AccessibleUnder_a(second_package, second_witness).value is True


def test_translation_quarantine_cannot_mutate_access_binding():
    package, first, _, first_handle, _, _ = _complete_package()
    before = Binds_a(package, first_handle, first)
    raw = RawAccessibleConfiguration(raw_values=(1, 2))

    de_name(
        raw,
        HumanTranslationSpace(
            labels=("opaque-1", "semantic replacement"),
        ),
    )

    denamed_package = de_name_access_package(package)
    after = Binds_a(denamed_package.value, first_handle, first)

    assert before.status == after.status == "BOUND"
    assert denamed_package.value is package


def test_executor_stops_at_discriminability_without_delta_or_continuation():
    package, _, _, _, _, witness = _complete_package()

    result = MExecutionMachine().execute(package)

    assert result.status == "UNRESOLVED"
    assert result.frontier == "DISCRIMINABILITY_FRONTIER"
    assert isinstance(result.value, RelationQualifiedAccess)
    assert result.value.connected_witnesses == (witness,)
    assert result.reopen_request is not None
    assert result.reopen_request.access is True
    assert all("difference" not in item.operation_name for item in result.receipts)
    assert not hasattr(result.value, "delta")
    assert not hasattr(result.value, "dependencies")
    assert not hasattr(result.value, "exchanges")
    assert not hasattr(result.value, "causation")
    assert not hasattr(result.value, "relevance")


def test_access_package_path_never_invokes_an_external_bridge():
    package, _, _, _, _, _ = _complete_package()
    machine = MExecutionMachine()
    machine.registry.register_external("access.forbidden_external")

    with patch.object(
        machine.registry,
        "invoke",
        side_effect=AssertionError("external bridge reached"),
    ) as invoke:
        result = machine.execute(package)

    invoke.assert_not_called()
    assert all(receipt.status != "BLOCKED_EXTERNAL" for receipt in result.receipts)


def test_access_integrity_receipts_are_typed_and_amendment_scoped():
    package, first, second, _, _, witness = _complete_package()

    results = (
        AccessibleUnder_a(package, witness),
        Binds_a(package, witness.endpoint_1, first),
        Origin_a(package, witness),
        Connects_a(package, witness, first, second),
    )

    for result in results:
        assert result.receipt.status == "ACCESS_INTEGRITY"
        assert result.receipt.authoritative_source_file == AMENDMENT_03_SOURCE
        assert result.receipt.implementation_source == (
            "m_machine/access_integrity.py"
        )


def test_amendment_03_clauses_have_exact_ranges_hashes_and_access_role():
    root = Path(__file__).resolve().parents[1]
    registry = compile_authoritative_clause_registry(root)
    amendment_text = (root / AMENDMENT_03_SOURCE).read_text(encoding="utf-8")

    clauses = tuple(
        clause
        for clause in registry.entries
        if clause.authoritative_source_file == AMENDMENT_03_SOURCE
    )
    assert len(clauses) == 7
    assert all(clause.execution_role == "ACCESS_REPRESENTATION" for clause in clauses)
    assert all(len(clause.exact_source_text_hash) == 64 for clause in clauses)
    for clause in clauses:
        expected = "".join(
            amendment_text.splitlines(keepends=True)[
                clause.line_start - 1 : clause.line_end
            ]
        )
        assert clause.exact_source_text == expected
    assert registry.get("access.discriminability_frontier").operation_status == (
        "SPEC_GAP"
    )


def test_frozen_mother_hash_and_legacy_raw_frontier_remain_unchanged():
    verification = verify_authoritative_boot()
    raw_result = MExecutionMachine().execute(
        RawAccessibleConfiguration(raw_values=(1, 2, 3))
    )

    assert verification.mother_mechanics_sha256 == (
        "0cea8129245b212c04fa776bdc1b718fabf50998a9635e1e06716504fc410f7b"
    )
    assert raw_result.status == "UNRESOLVED"
    assert raw_result.frontier == "difference/dependency reconstruction"