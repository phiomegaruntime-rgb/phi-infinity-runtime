from __future__ import annotations

from threading import Event, Thread
import time

import numpy as np
import pytest

from operational_m.governed_numeric_step import (
    CallerSupportAuthority,
    FreshVerificationRequired,
    GovernedPhiStepper,
    OptInRequired,
    ReopenRequired,
    SupportUnavailable,
)
from src.core import PhiSubstrateEngine


SUPPORT_ID = "caller-support:phi-substrate-step"


def make_engine() -> PhiSubstrateEngine:
    engine = PhiSubstrateEngine(n_nodes=2, seed=13)
    engine.pos = np.array([[-1.0, 0.0], [1.0, 0.0]], dtype=np.float64)
    engine.S = np.array([[2.0, 1.0, 0.5], [1.1, 2.0, 0.7]], dtype=np.float64)
    engine.R = np.array([0.1, 0.2], dtype=np.float64)
    return engine


def state(engine: PhiSubstrateEngine) -> tuple[np.ndarray, ...]:
    return tuple(value.copy() for value in (engine.pos, engine.S, engine.R))


def assert_state_equal(
    engine: PhiSubstrateEngine,
    expected: tuple[np.ndarray, ...],
) -> None:
    for actual, before in zip((engine.pos, engine.S, engine.R), expected):
        assert np.array_equal(actual, before)


def authority_with_support() -> CallerSupportAuthority:
    authority = CallerSupportAuthority(SUPPORT_ID)
    authority.publish_support(
        support_id=SUPPORT_ID,
        statement="Caller asserts that the configured step prerequisites hold.",
    )
    return authority


def test_opt_in_gate_advances_the_real_engine_and_reports_numeric_delta():
    engine = make_engine()
    authority = CallerSupportAuthority(SUPPORT_ID)
    stepper = GovernedPhiStepper(engine, authority, opt_in=True)
    before = state(engine)

    with pytest.raises(SupportUnavailable):
        stepper.step()
    assert_state_equal(engine, before)

    authority.publish_support(
        support_id=SUPPORT_ID,
        statement="Caller asserts that the configured step prerequisites hold.",
    )
    authority.verify()
    report = stepper.step()

    assert report.step_number == 1
    assert report.support_id == SUPPORT_ID
    assert report.state_before_sha256 != report.state_after_sha256
    assert any(
        not np.array_equal(old, new)
        for old, new in zip(before, (engine.pos, engine.S, engine.R))
    )
    assert report.metrics["representation_status"] == "REPRESENTED_TRANSFORMATION"


def test_gated_step_requires_opt_in_and_preserves_the_legacy_engine_entrypoint():
    with pytest.raises(OptInRequired):
        GovernedPhiStepper(make_engine(), CallerSupportAuthority(SUPPORT_ID))

    # Historical engine.step remains directly callable and ungated by design.
    engine = make_engine()
    before = state(engine)
    engine.step()
    assert any(
        not np.array_equal(old, new)
        for old, new in zip(before, (engine.pos, engine.S, engine.R))
    )


def test_withdraw_restore_reopen_and_fresh_verify_state_transitions():
    engine = make_engine()
    authority = authority_with_support()
    stepper = GovernedPhiStepper(engine, authority, opt_in=True)
    authority.verify()
    before = state(engine)

    authority.withdraw_support()
    with pytest.raises(SupportUnavailable):
        stepper.step()
    assert_state_equal(engine, before)

    authority.publish_support(
        support_id=SUPPORT_ID,
        statement="Support restored by the configured caller authority.",
    )
    with pytest.raises(ReopenRequired):
        authority.verify()

    # Restore alone cannot authorize another numerical transition.
    with pytest.raises(ReopenRequired):
        stepper.step()
    assert_state_equal(engine, before)

    authority.reopen()
    with pytest.raises(FreshVerificationRequired):
        stepper.step()
    assert_state_equal(engine, before)

    authority.verify()
    stepper.step()
    assert any(
        not np.array_equal(old, new)
        for old, new in zip(before, (engine.pos, engine.S, engine.R))
    )


def test_reopen_is_rejected_while_support_is_absent():
    authority = authority_with_support()
    authority.withdraw_support()
    with pytest.raises(SupportUnavailable):
        authority.reopen()


def test_transformation_error_on_candidate_does_not_partially_update_engine(
    monkeypatch: pytest.MonkeyPatch,
):
    engine = make_engine()
    authority = authority_with_support()
    stepper = GovernedPhiStepper(engine, authority, opt_in=True)
    authority.verify()
    before = state(engine)

    def mutate_candidate_then_fail(candidate: PhiSubstrateEngine):
        candidate.pos[0, 0] += 1000.0
        candidate.S[0, 0] += 1000.0
        candidate.R[0] += 1000.0
        raise RuntimeError("injected transformation failure")

    monkeypatch.setattr(
        PhiSubstrateEngine,
        "_step_phi_mechanics",
        mutate_candidate_then_fail,
    )
    with pytest.raises(RuntimeError, match="injected transformation failure"):
        stepper.step()
    assert_state_equal(engine, before)


def test_concurrent_withdrawal_serializes_after_an_in_flight_governed_step(
    monkeypatch: pytest.MonkeyPatch,
):
    engine = make_engine()
    authority = authority_with_support()
    stepper = GovernedPhiStepper(engine, authority, opt_in=True)
    authority.verify()
    entered_transform = Event()
    release_transform = Event()
    withdrawal_done = Event()
    original = PhiSubstrateEngine._step_phi_mechanics

    def pause_then_run(candidate: PhiSubstrateEngine):
        entered_transform.set()
        assert release_transform.wait(timeout=3)
        return original(candidate)

    monkeypatch.setattr(
        PhiSubstrateEngine,
        "_step_phi_mechanics",
        pause_then_run,
    )
    step_errors: list[BaseException] = []

    def run_step() -> None:
        try:
            stepper.step()
        except BaseException as exc:  # surfaced in the main test thread
            step_errors.append(exc)

    step_thread = Thread(target=run_step)
    step_thread.start()
    assert entered_transform.wait(timeout=3)

    withdraw_thread = Thread(
        target=lambda: (authority.withdraw_support(), withdrawal_done.set())
    )
    withdraw_thread.start()
    time.sleep(0.05)
    assert not withdrawal_done.is_set()

    release_transform.set()
    step_thread.join(timeout=3)
    withdraw_thread.join(timeout=3)
    assert not step_thread.is_alive()
    assert not withdraw_thread.is_alive()
    assert not step_errors
    assert withdrawal_done.is_set()
    assert authority.snapshot().support is None
