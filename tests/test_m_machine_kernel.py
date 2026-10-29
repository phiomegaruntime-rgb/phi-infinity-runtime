import hashlib
from dataclasses import FrozenInstanceError
from pathlib import Path

import numpy as np
import pytest

from m_machine import (
    AUTHORITATIVE_CURRENT_FILES,
    EXPECTED_MOTHER_MECHANICS_SHA256,
    DerivationReceipt,
    ExecutionResult,
    HumanTranslationSpace,
    MExecutionAccess,
    MExecutionMachine,
    OperationRegistry,
    RawAccessibleConfiguration,
    ReopenRequest,
    TranslationBlockedError,
    de_name,
    translate_after_derivation,
    verify_authoritative_boot,
)
from src.boundary import BoundaryEffectReceipt
from src.core import PhiSubstrateEngine


def raw_access(*, label="one", native_access=None):
    return RawAccessibleConfiguration(
        raw_values=([1.0, 2.0], [3.0, 4.0]),
        ordering=("first", "second"),
        provenance=("measurement", "measurement"),
        access_provenance=("sensor-a",),
        genealogy=("g0",),
        resolution_sampling=("full",),
        externally_imposed_constraints=("finite",),
        m_execution_access=native_access,
    ), HumanTranslationSpace(
        labels=(label,),
        categories=("domain-category",),
        domain_descriptions=("description",),
    )


def test_boot_checks_all_current_files_and_frozen_hash():
    verification = verify_authoritative_boot()
    assert verification.authoritative_files == AUTHORITATIVE_CURRENT_FILES
    assert verification.mother_mechanics_sha256 == (
        EXPECTED_MOTHER_MECHANICS_SHA256
    )
    digest = hashlib.sha256(
        Path("docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md").read_bytes()
    ).hexdigest()
    assert digest == EXPECTED_MOTHER_MECHANICS_SHA256


def test_denaming_preserves_raw_access_and_quarantines_human_material():
    access_a, human_a = raw_access(label="alpha")
    access_b, human_b = raw_access(label="beta")
    denamed_a = de_name(access_a, human_a)
    denamed_b = de_name(access_b, human_b)

    assert denamed_a.raw_access == denamed_b.raw_access
    assert denamed_a.raw_access.raw_values == access_a.raw_values
    assert denamed_a.raw_access.ordering == ("first", "second")
    assert denamed_a.human_translation.labels == ("alpha",)
    assert denamed_b.human_translation.labels == ("beta",)
    assert denamed_a.receipt.status == "DERIVED_M"


def test_human_labels_cannot_change_m_derivation():
    engine_a = PhiSubstrateEngine(n_nodes=2, seed=9)
    engine_b = PhiSubstrateEngine(n_nodes=2, seed=9)
    native_a = MExecutionAccess(engine=engine_a, cluster_indices=(0, 1))
    native_b = MExecutionAccess(engine=engine_b, cluster_indices=(0, 1))
    access_a, human_a = raw_access(label="alpha", native_access=native_a)
    access_b, human_b = raw_access(label="omega", native_access=native_b)

    result_a = MExecutionMachine().execute(de_name(access_a, human_a))
    result_b = MExecutionMachine().execute(de_name(access_b, human_b))

    assert result_a.status == "CONTINUATION"
    assert result_b.status == "CONTINUATION"
    assert result_a.value["transformation"] == result_b.value["transformation"]
    assert result_a.value["membrane"] == result_b.value["membrane"]


def test_raw_access_without_available_m_representation_is_unresolved():
    access, human = raw_access()
    result = MExecutionMachine().execute(de_name(access, human))

    assert result.status == "UNRESOLVED"
    assert result.value is None
    assert result.frontier == "difference/dependency reconstruction"
    assert result.reopen_request is not None
    assert result.reopen_request.dimensions == (
        "scale",
        "field",
        "boundary",
        "genealogy",
        "access",
    )
    assert all(
        receipt.status in {"DERIVED_M", "UNRESOLVED"}
        for receipt in result.receipts
    )


def test_unresolved_boundary_does_not_mutate_engine_or_continue():
    engine = PhiSubstrateEngine(n_nodes=2, seed=4)
    before_pos = engine.pos.copy()
    before_state = engine.S.copy()
    access, human = raw_access(
        native_access=MExecutionAccess(
            engine=engine,
            boundary_receipt=BoundaryEffectReceipt.unresolved(2),
        )
    )

    result = MExecutionMachine().execute(de_name(access, human))

    assert result.status == "UNRESOLVED"
    assert result.reopen_request is not None
    assert result.reopen_request.dimensions == ("boundary", "access")
    np.testing.assert_array_equal(engine.pos, before_pos)
    np.testing.assert_array_equal(engine.S, before_state)


def test_operation_without_m_receipt_cannot_enter_continuation():
    registry = OperationRegistry()

    def no_receipt_handler():
        return object()

    registry.register_m_only("bad.operation", no_receipt_handler)
    outcome = registry.invoke("bad.operation")

    assert outcome.receipt.status == "BLOCKED_EXTERNAL"
    with pytest.raises(ValueError):
        ExecutionResult(
            status="CONTINUATION",
            value=object(),
            receipts=(outcome.receipt,),
        )


def test_external_generators_are_registered_as_blocked_and_not_called():
    machine = MExecutionMachine()
    for name in (
        "scipy.optimize",
        "interpolation",
        "regression",
        "machine_learning",
        "legacy.field_bridge.reconstruct_phi_candidates",
        "external_acceptance_predicate",
    ):
        outcome = machine.registry.invoke(name)
        assert outcome.value is None
        assert outcome.receipt.status == "BLOCKED_EXTERNAL"


def test_translation_before_derivation_is_blocked():
    unresolved = ExecutionResult(
        status="UNRESOLVED",
        value=None,
        receipts=(),
    )

    with pytest.raises(TranslationBlockedError):
        translate_after_derivation(unresolved, lambda value: value)


def test_translation_opens_only_after_complete_m_derivation():
    engine = PhiSubstrateEngine(n_nodes=2, seed=5)
    access, human = raw_access(
        label="not-used-by-mechanics",
        native_access=MExecutionAccess(engine=engine),
    )
    result = MExecutionMachine().execute(de_name(access, human))

    assert result.status == "CONTINUATION"
    assert translate_after_derivation(
        result,
        lambda value: value["transformation"]["mean_energy"],
    ) == result.value["transformation"]["mean_energy"]


def test_translation_space_is_immutable_and_separate():
    human = HumanTranslationSpace(
        labels=("name",),
        categories=("category",),
    )
    with pytest.raises(FrozenInstanceError):
        human.labels = ("changed",)


def test_translation_space_cannot_be_used_as_m_input():
    with pytest.raises(TypeError):
        MExecutionMachine().execute(
            HumanTranslationSpace(labels=("human-only",))
        )


def test_legacy_inverse_bridge_is_not_called_by_m_executor(monkeypatch):
    from src.field_bridge import FieldBridge

    def fail_if_called(*args, **kwargs):
        raise AssertionError("legacy inverse bridge was called")

    monkeypatch.setattr(
        FieldBridge,
        "reconstruct_phi_candidates",
        fail_if_called,
    )
    access, human = raw_access()

    result = MExecutionMachine().execute(de_name(access, human))

    assert result.status == "UNRESOLVED"


def test_receipts_are_immutable_and_have_required_fields():
    receipt = DerivationReceipt.create(
        operation_name="test.operation",
        authoritative_source_file="docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
        authoritative_clause="lines 72-105",
        operation_performed="test",
        resulting_difference_or_consequence="test result",
        status="DERIVED_M",
    )

    assert receipt.receipt_id
    assert receipt.input_receipt_ids == ()
    assert receipt.accessible_evidence == ()
    with pytest.raises(FrozenInstanceError):
        receipt.status = "UNRESOLVED"


def test_reopen_request_requires_a_dimension():
    with pytest.raises(ValueError):
        ReopenRequest()