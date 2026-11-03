"""Opt-in cooperative support/effect serialization for PHI-INFINITY.

This is *not* an authentication layer. All evidence, predicates, and mutators
remain caller-controlled. Atomicity is defined ONLY relative to other threads
that publish through the SAME SynchronizedSupport instance. It cannot stop a
physical input changing, another process, direct state writes, or a malicious
Python participant. In particular, REOPEN still does not prove an independent
interval. Existing PHI equations are never copied or reimplemented here.

Alex Moraru — independent runtime contribution, 2026.
"""

import copy
from contextlib import contextmanager
from functools import wraps
import numpy as np
import threading

from src.gating import FirstDivergenceException, MultiAccessGating
from src.state_transaction import EngineStateTransaction


class SynchronizedSupport:
    """Cooperative in-process source of copied support observations.

    All cooperating publishers *must* use publish(). An effect holds the same
    lock from evidence capture through the native effect's return. This makes
    publish() wait until the effect completes, without simulating mechanics.
    """

    def __init__(self, initial_evidence):
        self._lock = threading.RLock()
        self._local = threading.local()
        self._evidence = copy.deepcopy(initial_evidence)

    def publish(self, evidence):
        """Replace evidence atomically; prevents reentrant publication in effect."""
        if getattr(self._local, 'inside_effect', False):
            raise RuntimeError('Cannot publish from inside an authorized effect')
        prepared = copy.deepcopy(evidence)
        with self._lock:
            self._evidence = prepared

    def snapshot(self):
        """Diagnostic copy only, NOT an authorization token."""
        with self._lock:
            return copy.deepcopy(self._evidence)

    @contextmanager
    def effect_window(self):
        """Yield fresh evidence while serializing all cooperative publications."""
        with self._lock:
            if getattr(self._local, 'inside_effect', False):
                raise RuntimeError('Recursive authorization on same support source')
            self._local.inside_effect = True
            try:
                yield copy.deepcopy(self._evidence)
            finally:
                self._local.inside_effect = False


class _EffectBinding:
    """One bound gate, one support source, and one serialized engine."""

    def __init__(self, gate, support, sealed=False):
        self.sealed = sealed
        self.gate = gate
        self.support = support
        self.check_index = 0
        self.engine_lock = threading.RLock()


def attach_gate_to_engine(engine, gate, support, *, sealed=False):
    """Attach exactly once, optionally requiring the closed built-in PHI profile."""
    if not isinstance(gate, MultiAccessGating):
        raise TypeError('gate must be a MultiAccessGating')
    if not isinstance(support, SynchronizedSupport):
        raise TypeError('support must be a SynchronizedSupport')
    if getattr(gate, '_phi_required_source', support) is not support:
        raise ValueError('Versioned gate must use its bound support source')
    if type(sealed) is not bool:
        raise TypeError('sealed must be a boolean')
    if sealed:
        # Local imports avoid cycles with the native engine module.
        from src.core import PhiSubstrateEngine
        from src.versioned_support import VersionedQuorumGate, VersionedSupport
        if (type(engine) is not PhiSubstrateEngine
                or type(gate) is not VersionedQuorumGate
                or type(support) is not VersionedSupport):
            raise TypeError('Sealed mode requires the exact built-in engine and versioned rule')
        if set(vars(engine)) != _SEALED_ENGINE_FIELDS:
            raise TypeError('Sealed engine has unexpected instance attributes')
    if getattr(engine, '_phi_effect_binding', None) is not None:
        raise RuntimeError('An effect gate is already attached')
    bound_owner = getattr(gate, '_phi_effect_owner', None)
    if bound_owner is not None and bound_owner is not engine:
        raise RuntimeError('This gate is already attached to another engine')
    engine._phi_effect_binding = _EffectBinding(gate, support, sealed)
    gate._phi_effect_owner = engine


_SEALED_ENGINE_FIELDS = frozenset((
    'N', 'sigma', 'alpha', 'beta', 'lmbda', 'gamma', 'mu', 'eta',
    'pos', 'S', 'R',
))


def _sealed_arguments(func, engine, args, kwargs):
    """Reject implicit Python callback hooks in the closed PHI call profile.

    Only the built-in PHI engine, plain progress scalars, and primitive numeric
    receipts are admissible. Boundary receipts are copied before the effect,
    removing live references to the caller's mutable arrays during mechanics.
    """
    from src.core import PhiSubstrateEngine
    if type(engine) is not PhiSubstrateEngine:
        raise TypeError('Sealed effect requires the built-in PHI engine')
    if set(vars(engine)) != (_SEALED_ENGINE_FIELDS | {'_phi_effect_binding'}):
        raise TypeError('Sealed effect rejects added engine attributes')
    if type(engine.N) is not int or engine.N < 1:
        raise TypeError('Sealed engine requires a positive built-in node count')
    for parameter in ('sigma', 'alpha', 'beta', 'lmbda', 'gamma', 'mu', 'eta'):
        value = vars(engine)[parameter]
        if type(value) not in (int, float) or not np.isfinite(value):
            raise TypeError('Sealed engine parameters must be finite built-in scalars')
    if engine.sigma == 0:
        raise TypeError('Sealed engine requires nonzero coupling scale')
    for field, shape in (('pos', (engine.N, 2)), ('S', (engine.N, 3)),
                         ('R', (engine.N,))):
        arr = vars(engine)[field]
        if (type(arr) is not np.ndarray or arr.shape != shape
                or arr.dtype != np.dtype('float64') or not arr.flags.writeable):
            raise TypeError('Sealed PHI state requires writable float64 native arrays')
    name = func.__name__
    prepared_args = args
    prepared_kwargs = dict(kwargs)
    if name == 'step':
        if len(args) > 1 or (args and 'mechanical_progress' in kwargs):
            raise TypeError('Invalid sealed native step arguments')
        progress = (args[0] if args else kwargs.get('mechanical_progress', 1.0))
    elif name == 'step_with_boundary':
        from src.boundary import BoundaryEffectReceipt
        if len(args) == 1 and 'receipt' not in kwargs:
            receipt = args[0]
        elif len(args) == 0 and 'receipt' in kwargs:
            receipt = kwargs['receipt']
        else:
            raise TypeError('Exactly one boundary receipt is required')
        if type(receipt) is not BoundaryEffectReceipt or type(receipt.resolved) is not bool:
            raise TypeError('Sealed receipt must be a plain BoundaryEffectReceipt')
        for item, shape in ((receipt.flow_e, (engine.N,)),
                            (receipt.flow_r, (engine.N,)),
                            (receipt.geometry, (engine.N, 2)),
                            (receipt.coupling_mass, (engine.N,))):
            if (type(item) is not np.ndarray or item.shape != shape
                    or item.dtype != np.dtype('float64')):
                raise TypeError('Sealed receipts require shaped float64 native arrays')
        # Make a private, immutable-to-the-caller copy before native mechanics.
        private_receipt = BoundaryEffectReceipt(
            flow_e=receipt.flow_e.copy(), flow_r=receipt.flow_r.copy(),
            geometry=receipt.geometry.copy(),
            coupling_mass=receipt.coupling_mass.copy(), resolved=receipt.resolved,
        )
        if args:
            prepared_args = (private_receipt,)
        else:
            prepared_kwargs['receipt'] = private_receipt
        progress = kwargs.get('mechanical_progress', 1.0)
    else:
        raise TypeError('Unknown PHI state-changing entry point')
    if type(progress) not in (int, float):
        raise TypeError('Sealed mechanical progress must be a built-in number')
    return prepared_args, prepared_kwargs


def authorized_effect(func):
    """Serialize, authorize and transact one real public PHI state transition.

    The opt-in path snapshots every supported engine instance attribute before
    invoking the caller's predicate. A predicate mutation is rolled back and
    refused even if the predicate returns True. Mechanics exceptions likewise
    roll back and lock, rather than leaving a partly committed PHI state.
    """
    @wraps(func)
    def invoke(engine, *args, **kwargs):
        binding = getattr(engine, '_phi_effect_binding', None)
        if binding is None:
            return func(engine, *args, **kwargs)
        with binding.engine_lock:
            if binding.gate.execution_locked:
                raise FirstDivergenceException(
                    'System locked in FirstDivergence. REOPEN protocol required.'
                )
            entered = False
            txn = None
            try:
                with binding.support.effect_window() as metrics:
                    entered = True
                    try:
                        # Closed profile performs argument/source checks before
                        # either the gate or actual mechanics execute.
                        if binding.sealed:
                            try:
                                args, kwargs = _sealed_arguments(func, engine, args, kwargs)
                            except BaseException as preflight_error:
                                binding.gate.execution_locked = True
                                raise FirstDivergenceException(
                                    '[FIRSTDIVERGENCE] Sealed effect argument refusal.'
                                ) from preflight_error
                        # Fail closed if a subclass brings unsupported state. No
                        # incomplete snapshot can be mistaken for a transaction.
                        txn = EngineStateTransaction(engine, binding)
                        try:
                            binding.gate.check_trajectory(metrics, binding.check_index)
                        except BaseException:
                            binding.gate.execution_locked = True
                            txn.restore()
                            raise
                        if binding.gate.execution_locked:
                            txn.restore()
                            raise FirstDivergenceException(
                                '[FIRSTDIVERGENCE] Gate became locked during evaluation.'
                            )
                        if not txn.unchanged():
                            binding.gate.execution_locked = True
                            txn.restore()
                            raise FirstDivergenceException(
                                '[FIRSTDIVERGENCE] Acceptance predicate modified engine state.'
                            )
                        binding.check_index += 1
                        try:
                            result = func(engine, *args, **kwargs)
                        except BaseException:
                            binding.gate.execution_locked = True
                            txn.restore()
                            raise
                        return result
                    except BaseException:
                        # Record the refused revision BEFORE releasing the
                        # publication lock, even for native execution errors.
                        # Other (callback) gate semantics remain unchanged.
                        from src.versioned_support import VersionedQuorumGate
                        if isinstance(binding.gate, VersionedQuorumGate):
                            binding.gate._record_execution_refusal()
                        raise
            except BaseException as exc:
                if not entered and not binding.gate.execution_locked:
                    binding.gate.execution_locked = True
                    raise FirstDivergenceException(
                        '[FIRSTDIVERGENCE] Could not acquire fresh support evidence.'
                    ) from exc
                if txn is None and not binding.gate.execution_locked:
                    binding.gate.execution_locked = True
                    raise FirstDivergenceException(
                        '[FIRSTDIVERGENCE] Engine state cannot be transacted safely.'
                    ) from exc
                raise
    return invoke
