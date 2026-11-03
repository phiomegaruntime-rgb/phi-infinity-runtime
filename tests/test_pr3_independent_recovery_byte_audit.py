"""Independent PR #3 follow-up regressions. No synthetic mechanics replacements.

These use the actual public native / boundary entrypoints. Callback injection
is only used in the documented *unsealed* testing profile.
"""
import threading
import numpy as np
import pytest

from src.boundary import BoundaryEffectReceipt, step_with_boundary
from src.core import PhiSubstrateEngine
from src.effect_authorization import SynchronizedSupport
from src.gating import FirstDivergenceException, MultiAccessGating
from src.versioned_support import VersionedSupport, VersionedQuorumGate
from src.state_transaction import UnsupportedStateError


def effect(engine, path, progress=1.0):
    if path == 'native':
        return engine.step(mechanical_progress=progress)
    return step_with_boundary(engine, BoundaryEffectReceipt.resolved_zero(engine.N),
                              mechanical_progress=progress)


def versioned(path, sealed):
    engine=PhiSubstrateEngine(n_nodes=8,seed=123)
    source=VersionedSupport({'left':True,'right':True})
    gate=VersionedQuorumGate(source, ('left','right'))
    engine.attach_gate(gate,source,sealed=sealed)
    return engine,source,gate


@pytest.mark.parametrize('path', ['native','boundary'])
@pytest.mark.parametrize('decision', [True,False])
def test_reviewer_dtype_flip_reverts_array_alias_and_every_byte(path,decision):
    engine=PhiSubstrateEngine(n_nodes=8,seed=123)
    before=engine.S.copy(order='K'); alias=engine.S
    def mutator(_):
        alias.dtype=alias.dtype.newbyteorder('S')
        return decision
    gate=MultiAccessGating(mutator)
    engine.attach_gate(gate,SynchronizedSupport({'flag':True}))
    with pytest.raises(FirstDivergenceException): effect(engine,path)
    assert gate.execution_locked
    assert engine.S is alias
    assert engine.S.dtype == before.dtype
    assert engine.S.shape == before.shape
    assert engine.S.tobytes() == before.tobytes()


@pytest.mark.parametrize('path', ['native','boundary'])
@pytest.mark.parametrize('sealed', [False,True])
def test_versioned_native_error_requires_newer_positive_publication(path,sealed):
    engine,source,gate=versioned(path,sealed)
    before=tuple(x.tobytes() for x in (engine.pos,engine.S,engine.R))
    with pytest.raises(ValueError): effect(engine,path,float('nan'))
    assert gate.execution_locked and gate.rejected_revision == 0
    assert tuple(x.tobytes() for x in (engine.pos,engine.S,engine.R)) == before
    with pytest.raises(FirstDivergenceException): gate.trigger_reopen()
    assert source.publish({'left':False,'right':True})==1
    with pytest.raises(FirstDivergenceException): gate.trigger_reopen()
    assert source.publish({'left':True,'right':True})==2
    assert gate.trigger_reopen()==2
    assert effect(engine,path,0.75)
    assert not gate.execution_locked and gate.accepted_revision==2


@pytest.mark.parametrize('path', ['native','boundary'])
@pytest.mark.parametrize('sealed', [False,True])
def test_rejection_at_latest_revision_requires_strictly_newer_reopen(path,sealed):
    engine,source,gate=versioned(path,sealed)
    source.publish({'left':True,'right':True})
    source.publish({'left':True,'right':True})
    with pytest.raises(ValueError): effect(engine,path,float('nan'))
    assert gate.rejected_revision==2
    with pytest.raises(FirstDivergenceException): gate.trigger_reopen()
    source.publish({'left':True,'right':False})
    with pytest.raises(FirstDivergenceException): gate.trigger_reopen()
    source.publish({'left':True,'right':True})
    assert gate.trigger_reopen()==4
    assert effect(engine,path,0.4)
    with pytest.raises(ValueError): effect(engine,path,float('nan'))
    assert gate.rejected_revision==4
    with pytest.raises(FirstDivergenceException): gate.trigger_reopen()
    source.publish({'left':True,'right':True})
    assert gate.trigger_reopen()==5


@pytest.mark.parametrize('path', ['native','boundary'])
def test_byteorder_and_size_reinterpretation_rolls_back(path):
    engine=PhiSubstrateEngine(n_nodes=8,seed=99)
    initial=engine.S.copy(order='K'); ref=engine.S
    def mutator(_):
        ref.dtype = np.dtype('u1')
        ref[:] = 0xEF
        engine.R[:] = 999
        return True
    gate=MultiAccessGating(mutator)
    engine.attach_gate(gate,SynchronizedSupport({'flag':True}))
    with pytest.raises(FirstDivergenceException): effect(engine,path)
    assert gate.execution_locked
    assert engine.S is ref
    assert engine.S.shape == initial.shape and engine.S.dtype == initial.dtype
    assert engine.S.tobytes() == initial.tobytes()


@pytest.mark.parametrize('path', ['native','boundary'])
def test_bit_exact_nan_payloads_signed_zero_and_readonly_flags(path):
    class Extended(PhiSubstrateEngine):
        def __init__(self):
            super().__init__(n_nodes=7)
            self.bits=np.array([0x7FF800000000003A,0x8000000000000000],dtype='u8').view('f8')
            self.bits.setflags(write=False)
    engine=Extended(); alias=engine.bits; before=alias.tobytes()
    def mutator(_):
        engine.bits=alias.copy()
        engine.bits[:]=1.0
        return False
    gate=MultiAccessGating(mutator)
    engine.attach_gate(gate,SynchronizedSupport({'flag':True}))
    with pytest.raises(FirstDivergenceException): effect(engine,path)
    assert gate.execution_locked and engine.bits is alias
    assert engine.bits.tobytes()==before
    assert not engine.bits.flags.writeable


@pytest.mark.parametrize('path', ['native','boundary'])
@pytest.mark.parametrize('decision', [False, True])
def test_aligned_structured_dtype_padding_raw_byte_roundtrip(path,decision):
    dtype=np.dtype([('flag','u1'),('quantity','u8')],align=True)
    class Extended(PhiSubstrateEngine):
        def __init__(self):
            super().__init__(n_nodes=8,seed=66)
            self.ledger=np.empty(5,dtype=dtype)
            self.ledger.view('u1')[:]=np.arange(self.ledger.nbytes,dtype='u1')
    engine=Extended(); ref=engine.ledger; before=ref.tobytes()
    def mutator(_):
        ref.view('u1')[1::dtype.itemsize] = 0xFF  # only padding bytes
        return decision
    gate=MultiAccessGating(mutator)
    engine.attach_gate(gate,SynchronizedSupport({'flag':True}))
    with pytest.raises(FirstDivergenceException): effect(engine,path)
    assert engine.ledger is ref and engine.ledger.tobytes()==before
    assert gate.execution_locked


@pytest.mark.parametrize('path', ['native','boundary'])
def test_strided_padded_array_and_alias_restore(path):
    dtype=np.dtype([('flag','u1'),('quantity','u8')],align=True)
    class Extended(PhiSubstrateEngine):
        def __init__(self):
            super().__init__(n_nodes=8)
            self.base=np.empty((6,3),dtype=dtype)
            self.base.view('u1')[:]=np.arange(self.base.nbytes,dtype='u1').reshape(self.base.view('u1').shape)
            self.ledger=self.base[::2,::-1]
    engine=Extended(); base=engine.base; sub=engine.ledger
    original_base=base.tobytes(); original_view=sub.tobytes()
    def mutator(_):
        base.view('u1')[:]=0xFE
        return True
    gate=MultiAccessGating(mutator)
    engine.attach_gate(gate,SynchronizedSupport({'flag':True}))
    with pytest.raises(FirstDivergenceException): effect(engine,path)
    assert engine.base is base and engine.ledger is sub
    assert base.tobytes()==original_base and sub.tobytes()==original_view


@pytest.mark.parametrize('path', ['native','boundary'])
def test_mutable_child_in_immutable_tuple_retains_tuple_identity(path):
    class Extended(PhiSubstrateEngine):
        def __init__(self):
            super().__init__(n_nodes=7)
            self.history=([1,2],{'stable':3})
    engine=Extended(); tuple_alias=engine.history; list_alias=engine.history[0]
    def mutator(_):
        list_alias.append(5)
        engine.history=([], {})
        return True
    gate=MultiAccessGating(mutator)
    engine.attach_gate(gate,SynchronizedSupport({'flag':True}))
    with pytest.raises(FirstDivergenceException): effect(engine,path)
    assert engine.history is tuple_alias
    assert engine.history[0] is list_alias and list_alias == [1,2]


@pytest.mark.parametrize('path', ['native','boundary'])
def test_sealed_preflight_execution_error_has_reopen_policy(path):
    engine,source,gate=versioned(path,True)
    if path=='native':
        with pytest.raises(FirstDivergenceException,match='Sealed effect argument refusal'):
            engine.step(mechanical_progress='invalid')
    else:
        with pytest.raises(FirstDivergenceException,match='Sealed effect argument refusal'):
            step_with_boundary(engine,object())
    assert gate.rejected_revision==0 and gate.execution_locked
    with pytest.raises(FirstDivergenceException): gate.trigger_reopen()
    source.publish({'left':True,'right':True})
    assert gate.trigger_reopen()==1
    assert effect(engine,path)


@pytest.mark.parametrize('path', ['native','boundary'])
def test_snapshot_error_records_rejection_but_does_not_run_predicate(path):
    class Extended(PhiSubstrateEngine):
        def __init__(self):
            super().__init__(n_nodes=7)
            self.unsupported=object()
    engine=Extended(); source=VersionedSupport({'a':True})
    gate=VersionedQuorumGate(source,('a',)); engine.attach_gate(gate,source)
    before=engine.S.tobytes()
    with pytest.raises(UnsupportedStateError): effect(engine,path)
    assert gate.rejected_revision==0 and gate.execution_locked
    assert engine.S.tobytes()==before
    del engine.unsupported
    with pytest.raises(FirstDivergenceException): gate.trigger_reopen()
    source.publish({'a':True})
    gate.trigger_reopen()
    assert effect(engine,path)


def test_metadata_dtype_rejected_without_touching_mechanics():
    class Extended(PhiSubstrateEngine):
        def __init__(self):
            super().__init__(n_nodes=7)
            self.metadata_array=np.zeros(2,dtype=np.dtype('f8',metadata={'callback':'unsafe'}))
    engine=Extended(); called=[]
    gate=MultiAccessGating(lambda evidence:called.append(1) or True)
    engine.attach_gate(gate,SynchronizedSupport({'a':True}))
    with pytest.raises(FirstDivergenceException) as reported: engine.step()
    assert isinstance(reported.value.__cause__, UnsupportedStateError)
    assert gate.execution_locked and called==[]


def test_publication_race_after_native_failure_records_previous_revision():
    started=threading.Event(); release=threading.Event(); writer_started=threading.Event(); writer_done=threading.Event()
    class RaisedAfterWork(PhiSubstrateEngine):
        def _step_phi_mechanics(self):
            started.set()
            if not release.wait(5):
                raise TimeoutError('test-timeout')
            super()._step_phi_mechanics()
            raise ArithmeticError('injected after genuine mechanics')
    engine=RaisedAfterWork(n_nodes=8)
    source=VersionedSupport({'a':True})
    gate=VersionedQuorumGate(source,('a',)); engine.attach_gate(gate,source)
    outcomes=[]
    def work():
        try: engine.step()
        except BaseException as e: outcomes.append(type(e))
    def publish():
        writer_started.set(); outcomes.append(('rev',source.publish({'a':True}))); writer_done.set()
    first=threading.Thread(target=work); second=threading.Thread(target=publish)
    try:
        first.start(); assert started.wait(5)
        second.start(); assert writer_started.wait(5)
        assert not writer_done.wait(.05)
        assert gate.rejected_revision is None
    finally:
        release.set();first.join(5);second.join(5)
    assert not first.is_alive() and not second.is_alive()
    assert ArithmeticError in outcomes and ('rev',1) in outcomes
    assert gate.rejected_revision==0 and gate.execution_locked
    assert gate.trigger_reopen()==1


def test_recovery_rejection_does_not_make_guarded_call_pass_with_nan():
    e,s,g=versioned('native',True)
    for expected_revision in range(4):
        with pytest.raises(ValueError): e.step(mechanical_progress=float('nan'))
        assert g.rejected_revision==expected_revision and g.execution_locked
        with pytest.raises(FirstDivergenceException): g.trigger_reopen()
        assert s.publish({'left':True,'right':True})==expected_revision+1
        assert g.trigger_reopen()==expected_revision+1
    assert e.step(mechanical_progress=1.0)

@pytest.mark.parametrize('path', ['native','boundary'])
@pytest.mark.parametrize('field', ['pos','S','R'])
@pytest.mark.parametrize('decision', [True,False])
def test_reverse_endian_flips_all_three_live_engine_arrays(path,field,decision):
    engine=PhiSubstrateEngine(n_nodes=8,seed=7)
    ref=getattr(engine,field); initial=ref.tobytes(); before_dtype=ref.dtype
    def mutate(_):
        ref.dtype=ref.dtype.newbyteorder('S')
        return decision
    gate=MultiAccessGating(mutate)
    engine.attach_gate(gate,SynchronizedSupport({'a':True}))
    with pytest.raises(FirstDivergenceException): effect(engine,path)
    assert gate.execution_locked
    assert getattr(engine,field) is ref
    assert ref.dtype==before_dtype and ref.tobytes()==initial


@pytest.mark.parametrize('path', ['native','boundary'])
@pytest.mark.parametrize('sealed', [False,True])
@pytest.mark.parametrize('progress', [float('nan'),float('inf'),float('-inf'),-1.0,0.0])
def test_invalid_mechanical_progress_failclosed_and_recovers_after_fresh_positive(path,sealed,progress):
    engine,source,gate=versioned(path,sealed)
    before=(engine.pos.tobytes(),engine.S.tobytes(),engine.R.tobytes())
    with pytest.raises(ValueError): effect(engine,path,progress)
    assert gate.execution_locked and gate.rejected_revision==0
    assert (engine.pos.tobytes(),engine.S.tobytes(),engine.R.tobytes())==before
    with pytest.raises(FirstDivergenceException): gate.trigger_reopen()
    assert source.publish({'left':True,'right':True})==1
    assert gate.trigger_reopen()==1
    assert effect(engine,path,1.0)


@pytest.mark.parametrize('path', ['native','boundary'])
@pytest.mark.parametrize('dtype', [np.dtype('>f8'),np.dtype('<f8'),np.dtype('>i8')])
def test_non_native_endian_ledger_restoration(path,dtype):
    class Extended(PhiSubstrateEngine):
        def __init__(self):
            super().__init__(n_nodes=7)
            self.ledger=np.arange(6).astype(dtype)
    engine=Extended(); a=engine.ledger; expected=a.tobytes()
    def mutate(_):
        a.dtype=a.dtype.newbyteorder('S')
        a[:]=1
        return True
    gate=MultiAccessGating(mutate)
    engine.attach_gate(gate,SynchronizedSupport({'a':True}))
    with pytest.raises(FirstDivergenceException): effect(engine,path)
    assert gate.execution_locked
    assert engine.ledger is a and a.dtype==dtype and a.tobytes()==expected


@pytest.mark.parametrize('path', ('native', 'boundary'))
@pytest.mark.parametrize('decision', (True, False))
@pytest.mark.parametrize('shape', ((6, 4), (6, 4, 3)))
@pytest.mark.parametrize('dtype', (
    np.dtype('f8'),
    np.dtype('>f8'),
    np.dtype([('flag', 'u1'), ('count', 'i8')], align=True),
    np.dtype('V16'),
), ids=('native-f64', 'big-endian-f64', 'aligned-structured', 'opaque-void'))
@pytest.mark.parametrize('layout', ('C', 'column-slice-reverse', 'transpose', 'F', 'reverse-rows'))
def test_full_public_effect_raw_record_rollback_matrix(path, decision, shape, dtype, layout):
    """Independent byte-for-byte adversarial matrix on REAL public engine effects.

    Uses two *aliased* state fields, not a mock transaction. Every cell flips
    record bytes and, when meaningful, reverses dtype byte order. The full
    base buffer, noncontiguous view, identity, strides and original dtype
    must all survive the rejected predicate.
    """
    order = 'F' if layout == 'F' else 'C'
    base = np.empty(shape, dtype=dtype, order=order)
    raw = np.dtype(f'V{dtype.itemsize}')
    records = np.empty(shape, dtype=raw)
    for i in range(records.size):
        records.flat[i] = np.void(bytes((i * 31 + j * 17 + 3) % 256
                                         for j in range(dtype.itemsize)))
    np.copyto(base.view(raw), records)
    if layout == 'column-slice-reverse':
        ref = base[::2, ::-1]
    elif layout == 'transpose':
        ref = base.transpose(tuple(reversed(range(base.ndim))))
    elif layout == 'reverse-rows':
        ref = base[::-1]
    else:
        ref = base

    class Extended(PhiSubstrateEngine):
        def __init__(self):
            super().__init__(n_nodes=8, seed=113)
            self.base = base
            self.special = ref

    engine = Extended()
    base_alias, ref_alias = engine.base, engine.special
    original = (base.tobytes(), ref.tobytes(), ref.dtype, ref.strides, base.strides)

    def mutator(_):
        if dtype.kind != 'V':
            ref.dtype = ref.dtype.newbyteorder('S')
        corruption = np.empty(ref.shape, dtype=raw)
        corruption.fill(np.void(bytes([0xA5]) * dtype.itemsize))
        np.copyto(ref.view(raw), corruption)
        return decision

    gate = MultiAccessGating(mutator)
    engine.attach_gate(gate, SynchronizedSupport({'guard': True}))
    with pytest.raises(FirstDivergenceException):
        effect(engine, path)
    assert gate.execution_locked
    assert engine.base is base_alias and engine.special is ref_alias
    assert (base.tobytes(), ref.tobytes(), ref.dtype, ref.strides, base.strides) == original


@pytest.mark.parametrize('path', ('native', 'boundary'))
@pytest.mark.parametrize('decision', (False, True))
def test_dtype_metadata_equates_unequally_and_is_restored(path, decision):
    """NumPy dtype equality intentionally ignores metadata: catch it anyway."""
    engine = PhiSubstrateEngine(n_nodes=8, seed=123)
    alias = engine.S
    before = alias.tobytes()
    original_dtype = alias.dtype
    illegal_dtype = np.dtype(original_dtype, metadata={'injected': 'predicate'})
    assert illegal_dtype == original_dtype  # independent test precondition

    def mutator(_):
        alias.dtype = illegal_dtype
        assert alias.dtype.metadata == {'injected': 'predicate'}
        return decision

    gate = MultiAccessGating(mutator)
    engine.attach_gate(gate, SynchronizedSupport({'flag': True}))
    with pytest.raises(FirstDivergenceException):
        effect(engine, path)
    assert gate.execution_locked
    assert engine.S is alias
    assert engine.S.dtype == original_dtype
    assert engine.S.dtype.metadata is None
    assert engine.S.tobytes() == before


@pytest.mark.parametrize('path', ('native', 'boundary'))
def test_nested_structured_dtype_metadata_refused_before_predicate(path):
    inner = np.dtype('i8', metadata={'mutability': ['unsafe']})
    nested = np.dtype([('small', 'u1'), ('payload', inner)], align=True)
    assert nested.metadata is None
    assert nested.fields['payload'][0].metadata is not None

    class Extended(PhiSubstrateEngine):
        def __init__(self):
            super().__init__(n_nodes=8)
            self.ledger = np.zeros(4, dtype=nested)

    engine = Extended()
    called = []
    gate = MultiAccessGating(lambda _: called.append(True) or True)
    engine.attach_gate(gate, SynchronizedSupport({'a': True}))
    with pytest.raises(FirstDivergenceException) as error:
        effect(engine, path)
    assert isinstance(error.value.__cause__, UnsupportedStateError)
    assert called == []
    assert gate.execution_locked
