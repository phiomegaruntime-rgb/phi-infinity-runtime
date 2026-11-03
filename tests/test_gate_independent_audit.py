"""Independent frozen gate audit. NO production modifications required.

The engine-effect counterexample intentionally records absent integration; it
is not misreported as a bypass of an already-connected authorization guard.
"""
import numpy as np
import pytest
from src.core import PhiSubstrateEngine
from src.gating import FirstDivergenceException, MultiAccessGating


def capture(engine):
    return (engine.pos.copy(), engine.S.copy(), engine.R.copy(), engine.mu, engine.eta)


def assert_unchanged(engine, before):
    for actual, prev in zip((engine.pos, engine.S, engine.R), before[:3]):
        np.testing.assert_array_equal(actual, prev)
    assert (engine.mu, engine.eta) == before[3:]


def test_frozen_five_state_transition_contract():
    support = {'present': True}
    gate = MultiAccessGating(lambda evidence: evidence['present'])
    def check(k):
        return gate.check_trajectory({'present': support['present']}, k)

    assert check(0) is None
    assert not gate.execution_locked
    support['present'] = False
    with pytest.raises(FirstDivergenceException, match=r'k\*=1'):
        check(1)
    assert gate.execution_locked
    support['present'] = True
    with pytest.raises(FirstDivergenceException, match='locked'):
        check(2)
    assert gate.execution_locked
    support['present'] = False
    gate.trigger_reopen()
    with pytest.raises(FirstDivergenceException, match=r'k\*=3'):
        check(3)
    assert gate.execution_locked
    support['present'] = True
    gate.trigger_reopen()
    assert check(4) is None
    assert not gate.execution_locked


def test_isolated_refusal_does_not_touch_unrelated_engine_state():
    engine = PhiSubstrateEngine(n_nodes=7, seed=17)
    before = capture(engine)
    gate = MultiAccessGating(lambda evidence: evidence['ok'])
    with pytest.raises(FirstDivergenceException):
        gate.check_trajectory({'ok': False}, 9)
    assert gate.execution_locked
    assert_unchanged(engine, before)


def test_expected_frozen_integration_gap_real_engine_step_changes_after_withdrawal():
    engine = PhiSubstrateEngine(n_nodes=7, seed=17)
    before = capture(engine)
    support = {'present': True}
    gate = MultiAccessGating(lambda evidence: evidence['present'])
    gate.check_trajectory({'present': support['present']}, 0)
    support['present'] = False
    result = engine.step()  # Real PHI effect path; NO call site checks this gate.
    assert isinstance(result, dict)
    assert any(not np.array_equal(x, y) for x,y in zip((engine.pos, engine.S, engine.R), before[:3]))
    assert not gate.execution_locked


def test_frozen_gate_has_no_authentication_of_caller_supplied_metrics():
    gate = MultiAccessGating(lambda evidence: evidence['available'])
    assert gate.check_trajectory({'available': True}, 0) is None
    # This assertion demonstrates the caller owns the evidence, not a verified source.
    assert not gate.execution_locked
