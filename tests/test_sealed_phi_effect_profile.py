"""Closed-profile effect tests: built-in mechanics, no user callback hooks."""

import numpy as np
import pytest

from src.boundary import BoundaryEffectReceipt, step_with_boundary
from src.core import PhiSubstrateEngine
from src.effect_authorization import SynchronizedSupport
from src.gating import FirstDivergenceException, MultiAccessGating
from src.versioned_support import VersionedQuorumGate, VersionedSupport


def sealed(seed=4):
    engine = PhiSubstrateEngine(n_nodes=8, seed=seed)
    source = VersionedSupport({'observed': True})
    gate = VersionedQuorumGate(source, ('observed',))
    engine.attach_gate(gate, source, sealed=True)
    return engine, source, gate


def baseline(engine):
    return engine.pos.copy(), engine.S.copy(), engine.R.copy(), engine.mu, engine.eta


def same(engine, before):
    for current, saved in zip((engine.pos, engine.S, engine.R), before[:3]):
        assert current.tobytes() == saved.tobytes()
    assert (engine.mu, engine.eta) == before[3:]


@pytest.mark.parametrize('seed', range(12))
def test_sealed_native_has_exact_ungated_numerical_parity(seed):
    control = PhiSubstrateEngine(n_nodes=8, seed=seed)
    engine, _, gate = sealed(seed)
    for factor in (0.7, 1.0, 1.8):
        out1 = control.step(mechanical_progress=factor)
        out2 = engine.step(mechanical_progress=factor)
        same(engine, baseline(control))
        assert out1.keys() == out2.keys()
        for k, value in out1.items():
            if isinstance(value, np.ndarray):
                assert value.tobytes() == out2[k].tobytes()
            else:
                assert value == out2[k]
    assert not gate.execution_locked


def test_sealed_boundary_has_exact_ungated_parity():
    control = PhiSubstrateEngine(n_nodes=8, seed=6)
    engine, _, _ = sealed(seed=6)
    receipt = BoundaryEffectReceipt.resolved_zero(engine.N)
    for _ in range(4):
        out1 = step_with_boundary(control, receipt)
        out2 = step_with_boundary(engine, receipt)
        same(engine, baseline(control))
        assert out1.keys() == out2.keys()
        for k, value in out1.items():
            if isinstance(value, np.ndarray):
                assert value.tobytes() == out2[k].tobytes()
            else:
                assert value == out2[k]


def test_arbitrary_predicate_cannot_attach_to_sealed_profile():
    engine = PhiSubstrateEngine(n_nodes=7)
    source = SynchronizedSupport({'present': True})
    gate = MultiAccessGating(lambda _: True)
    with pytest.raises(TypeError, match='exact built-in'):
        engine.attach_gate(gate, source, sealed=True)
    assert '_phi_effect_binding' not in vars(engine)


def test_subclass_code_cannot_attach_to_sealed_profile():
    class Evil(PhiSubstrateEngine):
        def _step_phi_mechanics(self):
            raise AssertionError('must not execute')

    engine = Evil(n_nodes=5)
    source = VersionedSupport({'observed': True})
    gate = VersionedQuorumGate(source, ('observed',))
    with pytest.raises(TypeError, match='exact built-in'):
        engine.attach_gate(gate, source, sealed=True)
    assert '_phi_effect_binding' not in vars(engine)


def test_sealed_rejects_implicit_float_callback_before_effect():
    class BadFloat:
        def __float__(self):
            raise AssertionError('Must never call user-defined numeric hooks')

    engine, _, gate = sealed()
    before = baseline(engine)
    with pytest.raises(FirstDivergenceException, match='Sealed effect argument refusal'):
        engine.step(mechanical_progress=BadFloat())
    assert gate.execution_locked
    same(engine, before)


def test_sealed_rejects_receipt_array_callback_and_rolls_back():
    class BadArray:
        def __array__(self, dtype=None):
            raise AssertionError('Must never call user-defined array hooks')

    engine, _, gate = sealed()
    before = baseline(engine)
    invalid = BoundaryEffectReceipt(
        flow_e=BadArray(), flow_r=np.zeros(engine.N),
        geometry=np.zeros((engine.N, 2)),
        coupling_mass=np.zeros(engine.N))
    with pytest.raises(FirstDivergenceException, match='Sealed effect argument refusal'):
        step_with_boundary(engine, invalid)
    assert gate.execution_locked
    same(engine, before)


def test_sealed_refuses_unexpected_instance_hooks_added_after_attachment():
    engine, _, gate = sealed()
    before = baseline(engine)
    engine._step_phi_mechanics = lambda: (_ for _ in ()).throw(AssertionError('ran'))
    with pytest.raises(FirstDivergenceException, match='Sealed effect argument refusal'):
        engine.step()
    assert gate.execution_locked
    same(engine, before)


def test_sealed_receipt_is_private_copy_during_true_effect():
    """An observer that inspects the caller receipt sees no in-place writes."""
    engine, _, gate = sealed()
    receipt = BoundaryEffectReceipt.resolved_zero(engine.N)
    original = [item.tobytes() for item in (
        receipt.flow_e, receipt.flow_r, receipt.geometry, receipt.coupling_mass)]
    out = step_with_boundary(engine, receipt)
    assert out['representation_status']
    for item, prior in zip((receipt.flow_e, receipt.flow_r,
                            receipt.geometry, receipt.coupling_mass), original):
        assert item.tobytes() == prior
    assert not gate.execution_locked


def test_sealed_recovery_after_withdrawal():
    engine, source, gate = sealed()
    last = baseline(engine)
    source.publish({'observed': False})
    with pytest.raises(FirstDivergenceException):
        engine.step()
    same(engine, last)
    assert gate.execution_locked
    source.publish({'observed': True})
    gate.trigger_reopen()
    assert engine.step()


@pytest.mark.parametrize('change', [
    lambda e: setattr(e, 'N', '8'),
    lambda e: setattr(e, 'sigma', object()),
    lambda e: setattr(e, 'S', np.empty((8, 3), dtype=object)),
    lambda e: setattr(e, 'R', np.ones(2)),
    lambda e: setattr(e, 'pos', np.ones((8, 2), dtype=np.int64)),
])
def test_sealed_preflight_refuses_non_numeric_or_nonconforming_state(change):
    engine, _, gate = sealed()
    initial = baseline(engine)
    change(engine)
    with pytest.raises(FirstDivergenceException, match='Sealed effect argument refusal'):
        engine.step()
    assert gate.execution_locked
    # Preflight refuses without further changes, not an implicit repair of the
    # caller's already-mutated engine prior to the attempted transaction.
    assert engine.mu == initial[3] and engine.eta == initial[4]
