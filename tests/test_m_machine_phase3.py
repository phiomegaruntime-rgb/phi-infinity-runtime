import hashlib

import pytest

from m_machine import (
    AuthoritativeClauseRegistry,
    DerivationReceipt,
    ExecutionResult,
    MExecutionMachine,
    MOnlyScheduler,
    MRule,
    OperationResult,
    RawAccessibleConfiguration,
    compile_authoritative_clause_registry,
)


def anonymous_raw_access():
    return RawAccessibleConfiguration(
        raw_values=((1, 2), (3, 5)),
        ordering=(0, 1),
        provenance=("p0", "p1"),
        access_provenance=("a0",),
        genealogy=("g0",),
        resolution_sampling=("r0",),
        externally_imposed_constraints=("c0",),
    )


def receipt(operation_name, status="DERIVED_M"):
    return DerivationReceipt.create(
        operation_name=operation_name,
        authoritative_source_file=(
            "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md"
        ),
        authoritative_clause="lines 72-105",
        input_receipt_ids=(),
        accessible_evidence=("anonymous evidence",),
        operation_performed="anonymous operation",
        resulting_difference_or_consequence="anonymous consequence",
        status=status,
    )


def test_clause_registry_compiles_exact_authoritative_ranges():
    registry = compile_authoritative_clause_registry()

    assert isinstance(registry, AuthoritativeClauseRegistry)
    assert len(registry.entries) >= 16
    assert registry.status("m.first_divergence") == "SPEC_GAP"
    assert registry.status("m.temporal_quantitative_closure") == "SPEC_GAP"
    for clause in registry.entries:
        source_hash = hashlib.sha256(
            clause.exact_source_text.encode("utf-8")
        ).hexdigest()
        assert source_hash == clause.exact_source_text_hash
        assert clause.source_text_reference.endswith(
            f"{clause.line_start}-{clause.line_end}"
        )
        assert clause.authoritative_source_file
        assert clause.prerequisites is not None


def test_clause_registry_is_immutable():
    registry = compile_authoritative_clause_registry()
    with pytest.raises(AttributeError):
        registry.entries = ()
    with pytest.raises(AttributeError):
        registry.entries[0].clause_id = "changed"


def test_raw_execute_stops_at_first_partial_m_frontier():
    result = MExecutionMachine().execute(anonymous_raw_access())

    assert result.status == "UNRESOLVED"
    assert result.frontier == "difference/dependency reconstruction"
    assert result.reopen_request is not None
    assert result.reopen_request.required_dimensions == ("access",)
    assert result.reopen_request.dimensions == ("access",)
    assert result.reopen_request.missing_prerequisite == (
        "M-derived difference/dependency representation"
    )
    assert result.reopen_request.replacement_value is None
    assert result.reopen_request.receipt_chain == tuple(
        receipt.receipt_id for receipt in result.receipts
    )


def test_scheduler_does_not_choose_between_unresolved_alternatives():
    called = []

    def should_not_run(receipts, context):
        called.append("unexpected")
        return OperationResult(
            operation_name="alternative",
            value=object(),
            receipt=receipt("alternative"),
        )

    scheduler = MOnlyScheduler()
    outcome = scheduler.run(
        initial_receipts=(receipt("seed"),),
        rules=(
            MRule(
                rule_id="alternative-a",
                operation_name="alternative-a",
                required_operations=("missing-a",),
                handler=should_not_run,
            ),
            MRule(
                rule_id="alternative-b",
                operation_name="alternative-b",
                required_operations=("missing-b",),
                handler=should_not_run,
            ),
        ),
        context=None,
    )

    assert outcome.status == "UNRESOLVED"
    assert outcome.frontier == "scheduler prerequisite frontier"
    assert called == []
    assert tuple(r.operation_name for r in outcome.receipts) == ("seed",)


def test_scheduler_executes_all_eligible_rules_without_ranking_them():
    called = []

    def make_rule(name):
        def handler(receipts, context):
            called.append(name)
            return OperationResult(
                operation_name=name,
                value=name,
                receipt=receipt(name),
            )

        return handler

    outcome = MOnlyScheduler().run(
        initial_receipts=(receipt("seed"),),
        rules=(
            MRule("rule-a", "a", ("seed",), make_rule("a")),
            MRule("rule-b", "b", ("seed",), make_rule("b")),
        ),
        context=None,
    )

    assert outcome.status == "CONTINUATION"
    assert called == ["a", "b"]
    assert outcome.value_map() == {"a": "a", "b": "b"}


def test_partial_operation_receipt_is_terminal_not_continuation():
    unresolved = receipt("partial", status="UNRESOLVED")

    def partial_handler(receipts, context):
        return OperationResult(
            operation_name="partial",
            value={"partial": True},
            receipt=unresolved,
        )

    outcome = MOnlyScheduler().run(
        initial_receipts=(receipt("seed"),),
        rules=(
            MRule(
                "partial-rule",
                "partial",
                ("seed",),
                partial_handler,
            ),
        ),
        context=None,
    )

    assert outcome.status == "UNRESOLVED"
    assert outcome.value_map() == {"partial": {"partial": True}}
    with pytest.raises(ValueError):
        ExecutionResult(
            status="CONTINUATION",
            value=outcome.value_map(),
            receipts=outcome.receipts,
        )


def test_first_divergence_remains_an_explicit_spec_gap():
    machine = MExecutionMachine()
    clause = machine.clauses.get("m.first_divergence")

    assert clause.operation_status == "SPEC_GAP"
    assert clause.implementation_reference is None
    blocked = machine.registry.invoke("external_acceptance_predicate")
    assert blocked.receipt.status == "BLOCKED_EXTERNAL"


def test_machine_rejects_injected_registry_bypass():
    from m_machine import OperationRegistry

    with pytest.raises(ValueError):
        MExecutionMachine(registry=OperationRegistry())


def test_native_path_is_scheduler_receipt_chain_with_exact_clause_links():
    from src.core import PhiSubstrateEngine
    from m_machine import MExecutionAccess, de_name

    access = RawAccessibleConfiguration(
        raw_values=((1, 2), (3, 5)),
        ordering=(0, 1),
        provenance=("p0", "p1"),
        access_provenance=("a0",),
        genealogy=("g0",),
        resolution_sampling=("r0",),
        m_execution_access=MExecutionAccess(
            engine=PhiSubstrateEngine(n_nodes=2, seed=12),
        ),
    )
    result = MExecutionMachine().execute(de_name(access))

    assert result.status == "CONTINUATION"
    assert [item.operation_name for item in result.receipts] == [
        "DeName",
        "native.compute_coupling",
        "native.step",
    ]
    assert all(item.status == "DERIVED_M" for item in result.receipts)
    assert result.receipts[1].clause_id == "m.dependencies"
    assert result.receipts[2].clause_id == "m.transformations"
    assert all(
        item.authoritative_source_file
        and "lines " in item.authoritative_clause
        for item in result.receipts
    )


def test_same_anonymous_access_has_identical_receipt_graph_for_labels():
    from m_machine import HumanTranslationSpace, MExecutionAccess, de_name
    from src.core import PhiSubstrateEngine

    def make_access():
        return RawAccessibleConfiguration(
            raw_values=((1, 2), (3, 5)),
            ordering=(0, 1),
            provenance=("p0", "p1"),
            access_provenance=("a0",),
            genealogy=("g0",),
            resolution_sampling=("r0",),
            m_execution_access=MExecutionAccess(
                engine=PhiSubstrateEngine(n_nodes=2, seed=12),
            ),
        )

    labels_a = HumanTranslationSpace(labels=("anonymous-a",))
    labels_b = HumanTranslationSpace(labels=("anonymous-b",))
    result_a = MExecutionMachine().execute(
        de_name(make_access(), labels_a)
    )
    result_b = MExecutionMachine().execute(
        de_name(make_access(), labels_b)
    )

    assert result_a.status == result_b.status == "CONTINUATION"
    assert tuple(r.receipt_id for r in result_a.receipts) == tuple(
        r.receipt_id for r in result_b.receipts
    )


def test_boot_hash_remains_mandatory_for_clause_compilation():
    machine = MExecutionMachine()
    assert machine.boot.mother_mechanics_sha256 == (
        "0cea8129245b212c04fa776bdc1b718fabf50998a9635e1e06716504fc410f7b"
    )