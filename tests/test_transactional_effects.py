"""Adversarial tests for actual PHI native and boundary effects (not mocks)."""
import threading
import copy

import numpy as np
import pytest

from src.boundary import BoundaryEffectReceipt, step_with_boundary
from src.core import PhiSubstrateEngine
from src.effect_authorization import SynchronizedSupport
from src.gating import FirstDivergenceException, MultiAccessGating


def capture(engine):
    return {k: copy.deepcopy(v) for k, v in vars(engine).items()
            if k != '_phi_effect_binding'}


def assert_equal_nested(current, expected):
    if isinstance(expected, np.ndarray):
        assert current.shape == expected.shape
        assert current.dtype == expected.dtype
        assert current.tobytes() == expected.tobytes()
    elif isinstance(expected, dict):
        assert list(current) == list(expected)
        for key in expected:
            assert_equal_nested(current[key], expected[key])
    elif isinstance(expected, (list, tuple)):
        assert len(current) == len(expected)
        for a, b in zip(current, expected):
            assert_equal_nested(a, b)
    else:
        assert current == expected


def assert_same(engine, original):
    assert set(vars(engine)) - {'_phi_effect_binding'} == set(original)
    for key, val in original.items():
        assert_equal_nested(vars(engine)[key], val)


def attach(engine, callback):
    gate = MultiAccessGating(callback)
    support = SynchronizedSupport({'present': True})
    engine.attach_gate(gate, support)
    return gate, support


@pytest.mark.parametrize('return_value', [True, False])
def test_predicate_changes_all_engine_owned_state_and_refuses(return_value):
    engine = PhiSubstrateEngine(n_nodes=7, seed=13)
    original = capture(engine)
    pos_alias = engine.pos
    S_alias = engine.S

    def predicate(_):
        engine.pos[0, 0] += 7
        engine.S[0, 1] = -99
        engine.R = np.ones_like(engine.R)
        engine.eta = 88.0
        engine.unapproved = 'injected'
        return return_value

    gate, _ = attach(engine, predicate)
    with pytest.raises(FirstDivergenceException):
        engine.step()
    assert gate.execution_locked
    assert_same(engine, original)
    assert engine.pos is pos_alias
    assert engine.S is S_alias


def test_predicate_mutates_nested_subclass_state_and_rolls_back_aliases():
    class Extended(PhiSubstrateEngine):
        def __init__(self):
            super().__init__(n_nodes=6)
            self.notes = [{'count': [1, 2]}]
            self.matrix = {'cell': np.array([2., 3.])}

    engine = Extended()
    notes_alias = engine.notes
    nested_alias = engine.notes[0]['count']
    cell_alias = engine.matrix['cell']
    baseline = capture(engine)

    def predicate(_):
        nested_alias.append(17)
        engine.matrix['cell'][0] = 777
        engine.notes = []
        return True

    gate, _ = attach(engine, predicate)
    with pytest.raises(FirstDivergenceException, match='modified engine state'):
        engine.step()
    assert gate.execution_locked
    assert_same(engine, baseline)
    assert engine.notes is notes_alias
    assert engine.notes[0]['count'] is nested_alias
    assert nested_alias == [1, 2]
    assert engine.matrix['cell'] is cell_alias
    np.testing.assert_array_equal(cell_alias, np.array([2., 3.]))


def test_predicate_mutation_then_exception_rolls_back_and_locks():
    engine = PhiSubstrateEngine(n_nodes=8, seed=34)
    baseline = capture(engine)

    def predicate(_):
        engine.pos[:] = 0.0
        raise ValueError('injected predicate failure')

    gate, _ = attach(engine, predicate)
    with pytest.raises(FirstDivergenceException) as thrown:
        engine.step()
    assert isinstance(thrown.value.__cause__, ValueError)
    assert gate.execution_locked
    assert_same(engine, baseline)


@pytest.mark.parametrize('which', ['native', 'boundary'])
def test_actual_mechanics_exception_restores_all_state(which):
    class FaultAfterWork(PhiSubstrateEngine):
        def _step_phi_mechanics(self):
            super()._step_phi_mechanics()  # genuine PHI equations already ran
            self.R += 71
            self.gamma = -7
            self.temp_field = 'must not survive'
            raise ArithmeticError('injected after real numeric effect')

        def compute_coupling(self):
            computed = super().compute_coupling()
            if which == 'boundary':
                self.S += 2
                self.temp_field = 'must not survive'
                raise ArithmeticError('injected after real coupling effect')
            return computed

    engine = FaultAfterWork(n_nodes=7, seed=15)
    baseline = capture(engine)
    state_aliases = (engine.pos, engine.S, engine.R)
    gate, _ = attach(engine, lambda e: e['present'])
    with pytest.raises(ArithmeticError, match='injected'):
        if which == 'native':
            engine.step(mechanical_progress=1.8)
        else:
            step_with_boundary(engine, BoundaryEffectReceipt.resolved_zero(engine.N))
    assert gate.execution_locked
    assert_same(engine, baseline)
    assert engine.pos is state_aliases[0]
    assert engine.S is state_aliases[1]
    assert engine.R is state_aliases[2]
    with pytest.raises(FirstDivergenceException, match='locked'):
        engine.step()
    assert_same(engine, baseline)


def test_predicate_edits_engine_binding_is_detected_and_restored():
    engine = PhiSubstrateEngine(n_nodes=5)
    original = capture(engine)

    def predicate(_):
        engine._phi_effect_binding = None
        return True

    gate, _ = attach(engine, predicate)
    binding = engine._phi_effect_binding
    with pytest.raises(FirstDivergenceException, match='modified engine state'):
        engine.step()
    assert gate.execution_locked
    assert engine._phi_effect_binding is binding
    assert_same(engine, original)


def test_unsupported_subclass_state_is_rejected_before_mechanics():
    class Unsupported(PhiSubstrateEngine):
        def __init__(self):
            super().__init__(n_nodes=4)
            self.external_lock = threading.Lock()

    engine = Unsupported()
    before = (engine.pos.copy(), engine.S.copy(), engine.R.copy())
    gate, _ = attach(engine, lambda e: e['present'])
    with pytest.raises(FirstDivergenceException, match='cannot be transacted safely'):
        engine.step()
    assert gate.execution_locked
    for now, earlier in zip((engine.pos, engine.S, engine.R), before):
        np.testing.assert_array_equal(now, earlier)


def test_valid_successful_subclass_state_updates_still_commit():
    class Incrementing(PhiSubstrateEngine):
        def __init__(self):
            super().__init__(n_nodes=7)
            self.counter = 0

        def _step_phi_mechanics(self):
            result = super()._step_phi_mechanics()
            self.counter += 1
            return result

    engine = Incrementing()
    gate, _ = attach(engine, lambda e: e['present'])
    original = engine.S.copy()
    engine.step()
    assert engine.counter == 1
    assert not np.array_equal(original, engine.S)
    assert not gate.execution_locked


def test_bad_progress_after_authorization_rolls_back_and_locks():
    engine = PhiSubstrateEngine(n_nodes=4)
    original = capture(engine)
    gate, _ = attach(engine, lambda e: e['present'])
    with pytest.raises(ValueError, match='finite'):
        engine.step(mechanical_progress=float('nan'))
    assert gate.execution_locked
    assert_same(engine, original)


def test_slot_state_rejected_before_predicate_is_invoked():
    class ExtraSlot(PhiSubstrateEngine):
        __slots__ = ('private_counter',)

        def __init__(self):
            super().__init__(n_nodes=5)
            self.private_counter = 10

    engine = ExtraSlot()
    invoked = []
    gate, _ = attach(engine, lambda _: invoked.append(True) or True)
    with pytest.raises(FirstDivergenceException, match='cannot be transacted'):
        engine.step()
    assert invoked == []
    assert engine.private_counter == 10
    assert gate.execution_locked


def test_predicate_rebinds_engine_class_then_is_refused_and_reverted():
    class Other(PhiSubstrateEngine):
        pass

    engine = PhiSubstrateEngine(n_nodes=5)
    original = capture(engine)

    def predicate(_):
        engine.__class__ = Other
        return True

    gate, _ = attach(engine, predicate)
    with pytest.raises(FirstDivergenceException, match='modified engine state'):
        engine.step()
    assert gate.execution_locked
    assert type(engine) is PhiSubstrateEngine
    assert_same(engine, original)


def test_predicate_changes_array_writeability_then_restoration_recovers_it():
    engine = PhiSubstrateEngine(n_nodes=5)
    original = capture(engine)

    def predicate(_):
        engine.pos.setflags(write=False)
        return True

    gate, _ = attach(engine, predicate)
    with pytest.raises(FirstDivergenceException):
        engine.step()
    assert gate.execution_locked
    assert engine.pos.flags.writeable
    assert_same(engine, original)
