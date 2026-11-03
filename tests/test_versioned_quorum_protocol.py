"""Declarative quorum, non-forgeable caller metrics, and enforced fresh REOPEN."""

import threading

import numpy as np
import pytest

from src.boundary import BoundaryEffectReceipt, step_with_boundary
from src.core import PhiSubstrateEngine
from src.effect_authorization import SynchronizedSupport
from src.gating import FirstDivergenceException
from src.versioned_support import VersionedQuorumGate, VersionedSupport


def attached():
    engine = PhiSubstrateEngine(n_nodes=8, seed=5)
    source = VersionedSupport({'alpha': True, 'beta': True})
    gate = VersionedQuorumGate(source, ('alpha', 'beta'))
    engine.attach_gate(gate, source)
    return engine, source, gate


def state(engine):
    return (engine.pos.copy(), engine.S.copy(), engine.R.copy(), engine.mu, engine.eta)


def assert_state(engine, previous):
    for name, value in zip(('pos', 'S', 'R'), previous[:3]):
        np.testing.assert_array_equal(getattr(engine, name), value)
    assert (engine.mu, engine.eta) == previous[3:]


@pytest.mark.parametrize('method', ['native', 'boundary'])
def test_quorum_recovery_requires_new_positive_publication(method):
    engine, source, gate = attached()
    receipt = BoundaryEffectReceipt.resolved_zero(engine.N)

    def effect():
        if method == 'native':
            return engine.step()
        return step_with_boundary(engine, receipt)

    assert effect()
    last = state(engine)
    source.publish({'alpha': True, 'beta': False})
    with pytest.raises(FirstDivergenceException):
        effect()
    assert gate.execution_locked
    assert gate.rejected_revision == 1
    assert_state(engine, last)
    with pytest.raises(FirstDivergenceException, match='no newer positive'):
        gate.trigger_reopen()
    with pytest.raises(FirstDivergenceException, match='locked'):
        effect()
    assert_state(engine, last)
    assert source.publish({'alpha': False, 'beta': True}) == 2
    with pytest.raises(FirstDivergenceException, match='no newer positive'):
        gate.trigger_reopen()
    assert source.publish({'alpha': True, 'beta': True}) == 3
    assert gate.trigger_reopen() == 3
    assert effect()
    assert gate.accepted_revision == 3
    assert not gate.execution_locked


def test_quorum_does_not_trust_forged_metrics_argument():
    source = VersionedSupport({'a': False})
    gate = VersionedQuorumGate(source, ('a',))
    with pytest.raises(FirstDivergenceException):
        gate.check_trajectory({'a': True}, 9)
    assert gate.execution_locked
    with pytest.raises(FirstDivergenceException, match='no newer positive'):
        gate.trigger_reopen()
    source.publish({'a': True})
    gate.trigger_reopen()
    gate.check_trajectory({'a': False}, 10)  # source, not this forged argument
    assert not gate.execution_locked


@pytest.mark.parametrize('value', [1, 0, 'true', None, np.bool_(True), [], object()])
def test_versioned_support_rejects_non_boolean_claims(value):
    with pytest.raises(TypeError):
        VersionedSupport({'channel': value})
    source = VersionedSupport({'channel': True})
    with pytest.raises(TypeError):
        source.publish({'channel': value})
    assert source.read_revision() == (0, {'channel': True})


def test_schema_and_wrong_source_attachment_fail_closed():
    source = VersionedSupport({'a': True})
    with pytest.raises(ValueError):
        VersionedQuorumGate(source, ())
    with pytest.raises(ValueError):
        VersionedQuorumGate(source, ('a', 'a'))
    gate = VersionedQuorumGate(source, ('a',))
    engine = PhiSubstrateEngine(n_nodes=5)
    with pytest.raises(ValueError, match='bound support'):
        engine.attach_gate(gate, SynchronizedSupport({'a': True}))
    assert not hasattr(engine, '_phi_effect_binding')
    engine.attach_gate(gate, source)
    assert engine.step()


def test_no_reopen_without_prior_refusal():
    _, _, gate = attached()
    with pytest.raises(FirstDivergenceException, match='prior refusal'):
        gate.trigger_reopen()


def test_versioned_support_publish_cannot_interleave_with_effect():
    entered = threading.Event()
    release = threading.Event()
    writer_start = threading.Event()
    writer_done = threading.Event()
    errors = []

    class RealInstrumented(PhiSubstrateEngine):
        def _step_phi_mechanics(self):
            entered.set()
            if not release.wait(timeout=5):
                raise TimeoutError('test sync failed')
            return super()._step_phi_mechanics()

    engine = RealInstrumented(n_nodes=8)
    source = VersionedSupport({'a': True})
    gate = VersionedQuorumGate(source, ('a',))
    engine.attach_gate(gate, source)

    def run_effect():
        try:
            engine.step()
        except BaseException as exc:
            errors.append(exc)

    def run_writer():
        try:
            writer_start.set()
            source.publish({'a': False})
            writer_done.set()
        except BaseException as exc:
            errors.append(exc)

    first = threading.Thread(target=run_effect)
    second = threading.Thread(target=run_writer)
    try:
        first.start()
        assert entered.wait(timeout=5)
        second.start()
        assert writer_start.wait(timeout=5)
        assert not writer_done.wait(timeout=0.04)
    finally:
        release.set()
        first.join(timeout=5)
        second.join(timeout=5)
    assert not errors
    assert not first.is_alive() and not second.is_alive()
    assert source.read_revision() == (1, {'a': False})
    old = state(engine)
    with pytest.raises(FirstDivergenceException):
        engine.step()
    assert_state(engine, old)
