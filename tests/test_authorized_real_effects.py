"""Actual mutating PHI call paths, guarded by synchronized support.

No simulated physics, fabricated receipts, or alternate effect wrappers.
"""
import threading
import time

import numpy as np
import pytest

from src.boundary import BoundaryEffectReceipt, step_with_boundary
from src.core import PhiSubstrateEngine
from src.effect_authorization import SynchronizedSupport
from src.gating import FirstDivergenceException, MultiAccessGating


def state(engine):
    return (engine.pos.copy(), engine.S.copy(), engine.R.copy(), engine.mu, engine.eta)


def assert_unchanged(engine, before):
    for actual, expected in zip((engine.pos, engine.S, engine.R), before[:3]):
        np.testing.assert_array_equal(actual, expected)
    assert (engine.mu, engine.eta) == before[3:]


def assert_same_engine(a,b):
    assert_unchanged(a,state(b))


def attach(engine, present=True):
    source = SynchronizedSupport({'present': present})
    gate = MultiAccessGating(lambda evidence: evidence['present'])
    engine.attach_gate(gate,source)
    return gate,source


@pytest.mark.parametrize('effect', ['native','boundary'])
def test_five_transitions_at_real_effect_boundary(effect):
    engine=PhiSubstrateEngine(n_nodes=8,seed=42)
    gate,source=attach(engine,True)
    receipt=BoundaryEffectReceipt.resolved_zero(engine.N)
    def execute():
        if effect=='native': return engine.step(mechanical_progress=0.7)
        return step_with_boundary(engine,receipt,mechanical_progress=0.7)
    first=state(engine)
    assert execute()  # actual effect while supported
    after_accept=state(engine)
    assert any(not np.array_equal(a,b) for a,b in zip(after_accept[:3],first[:3]))
    source.publish({'present':False})
    with pytest.raises(FirstDivergenceException,match=r'k\*=1'):
        execute()
    assert gate.execution_locked
    assert_unchanged(engine, after_accept)
    source.publish({'present':True})
    with pytest.raises(FirstDivergenceException,match='locked'):
        execute()
    assert_unchanged(engine, after_accept)
    gate.trigger_reopen()
    source.publish({'present':False})
    with pytest.raises(FirstDivergenceException,match=r'k\*=1'):
        execute()
    assert gate.execution_locked
    assert_unchanged(engine, after_accept)
    source.publish({'present':True})
    gate.trigger_reopen()
    assert execute()
    assert not gate.execution_locked


@pytest.mark.parametrize('seed',range(16))
@pytest.mark.parametrize('progress',[0.25,1.0,2.5])
def test_native_accepted_result_exact_parity(seed,progress):
    original=PhiSubstrateEngine(n_nodes=11,seed=seed)
    guarded=PhiSubstrateEngine(n_nodes=11,seed=seed)
    gate,_=attach(guarded,True)
    for i in range(3):
        out_a=original.step(mechanical_progress=progress)
        out_b=guarded.step(mechanical_progress=progress)
        assert_same_engine(original,guarded)
        assert out_a.keys()==out_b.keys()
        for key in out_a:
            if isinstance(out_a[key],np.ndarray):np.testing.assert_array_equal(out_a[key],out_b[key])
            else: assert out_a[key]==out_b[key]
    assert not gate.execution_locked


@pytest.mark.parametrize('seed',range(12))
def test_boundary_accepted_result_exact_parity(seed):
    original=PhiSubstrateEngine(n_nodes=9,seed=seed)
    guarded=PhiSubstrateEngine(n_nodes=9,seed=seed)
    _,_=attach(guarded,True)
    receipt=BoundaryEffectReceipt.resolved_zero(original.N)
    for i in range(2):
        out_a=step_with_boundary(original,receipt,mechanical_progress=0.8)
        out_b=step_with_boundary(guarded,receipt,mechanical_progress=0.8)
        assert_same_engine(original,guarded)
        assert out_a.keys()==out_b.keys()
        for key in out_a:
            if isinstance(out_a[key],np.ndarray):np.testing.assert_array_equal(out_a[key],out_b[key])
            else:assert out_a[key]==out_b[key]


def test_support_observation_is_independent_of_external_dictionary_alias():
    external={'present':True}
    source=SynchronizedSupport(external)
    external['present']=False
    assert source.snapshot()['present'] is True
    observed=source.snapshot();observed['present']=False
    assert source.snapshot()['present'] is True
    source.publish(external)
    assert source.snapshot()['present'] is False


def test_invalid_attachment_and_repeated_attachment_preserve_state():
    e=PhiSubstrateEngine(n_nodes=5,seed=10)
    before=state(e)
    with pytest.raises(TypeError): e.attach_gate(None,SynchronizedSupport(True))
    with pytest.raises(TypeError): e.attach_gate(MultiAccessGating(bool),lambda:True)
    assert_unchanged(e,before)
    gate,source=attach(e)
    with pytest.raises(RuntimeError,match='already attached'):
        e.attach_gate(MultiAccessGating(bool),source)
    with pytest.raises(RuntimeError):
        PhiSubstrateEngine(n_nodes=4).attach_gate(gate,SynchronizedSupport(True))
    assert_unchanged(e,before)


def test_false_support_no_mutation_even_after_initial_accepted_isolated_check():
    engine=PhiSubstrateEngine(n_nodes=8,seed=84)
    gate,source=attach(engine,True)
    gate.check_trajectory({'present':True},99)
    before=state(engine)
    source.publish({'present':False})
    with pytest.raises(FirstDivergenceException):engine.step()
    assert gate.execution_locked
    assert_unchanged(engine,before)


def test_callback_exception_locks_and_state_unchanged():
    engine=PhiSubstrateEngine(n_nodes=8,seed=21)
    source=SynchronizedSupport({'value':0})
    def predicate(evidence):
        if evidence['value']==0:raise LookupError('source unusable')
        return evidence['value']>0
    gate=MultiAccessGating(predicate)
    engine.attach_gate(gate,source)
    before=state(engine)
    with pytest.raises(FirstDivergenceException) as err:engine.step()
    assert isinstance(err.value.__cause__,LookupError)
    assert gate.execution_locked
    assert_unchanged(engine,before)


def test_reentrant_publish_from_predicate_refuses_without_state_change():
    source=SynchronizedSupport({'ok':True})
    def predicate(evidence):
        source.publish({'ok':False})
        return True
    gate=MultiAccessGating(predicate)
    engine=PhiSubstrateEngine(n_nodes=8,seed=21)
    engine.attach_gate(gate,source)
    before=state(engine)
    with pytest.raises(FirstDivergenceException) as err:engine.step()
    assert isinstance(err.value.__cause__,RuntimeError)
    assert gate.execution_locked
    assert source.snapshot()['ok'] is True
    assert_unchanged(engine,before)


def test_provider_failure_before_effect_fails_closed_and_state_unchanged():
    class UncopyableOnRead:
        def __init__(self):self.count=0
        def __deepcopy__(self,memo):
            self.count+=1
            if self.count>1:raise IOError('injected source-copy fault')
            return self
    input_data=UncopyableOnRead()
    source=SynchronizedSupport(input_data)
    engine=PhiSubstrateEngine(n_nodes=8,seed=21)
    gate=MultiAccessGating(bool)
    engine.attach_gate(gate,source)
    before=state(engine)
    with pytest.raises(FirstDivergenceException,match='Could not acquire') as err:engine.step()
    assert isinstance(err.value.__cause__,IOError)
    assert gate.execution_locked
    assert_unchanged(engine,before)


def test_serialized_support_publication_waits_for_native_real_effect():
    """Execution window covers real mechanics, not only fresh support reading."""
    started=threading.Event();unblock=threading.Event();writer_started=threading.Event()
    writer_finished=threading.Event(); failures=[]
    class InstrumentedRealEngine(PhiSubstrateEngine):
        def _step_phi_mechanics(self):
            started.set()
            if not unblock.wait(timeout=5):raise TimeoutError('test did not unblock')
            return super()._step_phi_mechanics() # genuine native mechanics
    engine=InstrumentedRealEngine(n_nodes=8,seed=18)
    gate,source=attach(engine,True)
    def effect():
        try:engine.step()
        except BaseException as e:failures.append(e)
    def writer():
        try:
            writer_started.set()
            source.publish({'present':False})
            writer_finished.set()
        except BaseException as e:failures.append(e)
    a=threading.Thread(target=effect); b=threading.Thread(target=writer)
    try:
        a.start()
        assert started.wait(timeout=5)  # guard accepted; real method entered
        b.start()
        assert writer_started.wait(timeout=5)
        assert not writer_finished.wait(timeout=0.04) # blocked by guard's lock
        # Do not call snapshot() here: it correctly waits on the same lock.
    finally:
        unblock.set()
        a.join(timeout=5); b.join(timeout=5)
    assert not a.is_alive() and not b.is_alive()
    assert not failures
    assert writer_finished.is_set()
    assert source.snapshot()['present'] is False
    before=state(engine)
    with pytest.raises(FirstDivergenceException):engine.step()
    assert_unchanged(engine,before)
    assert gate.execution_locked


def test_authorization_does_not_claim_external_physical_atomicity():
    """Out-of-band changes are not intercepted: defined scope, not a pass."""
    outside={'present':True}
    support=SynchronizedSupport({'present':outside['present']})
    e=PhiSubstrateEngine(n_nodes=6,seed=1)
    gate=MultiAccessGating(lambda d:d['present'])
    e.attach_gate(gate,support)
    outside['present']=False  # NOT a SynchronizedSupport.publish!
    before=state(e)
    e.step() # accepted from the last PUBLISHED evidence, not from reality
    assert not gate.execution_locked
    assert any(not np.array_equal(x,y) for x,y in zip(state(e)[:3],before[:3]))
    assert support.snapshot()['present'] is True
