"""Exact, opt-in PHI engine-state transaction for guarded public effects.

Captures all instance attributes of the engine (except its synchronization
binding) using a deliberately closed data model. Mutable arrays and built-in
containers are restored IN PLACE, including objects replaced on the engine.
Unknown state types refuse before an effect: they are never silently skipped.

This protects engine-owned represented state, not filesystem/network effects,
threads outside the cooperative lock, or objects reachable through closures.
"""

from dataclasses import dataclass
import struct

import numpy as np


class UnsupportedStateError(TypeError):
    """An engine attribute cannot be snapshotted/restored under the contract."""


_SCALAR_TYPES = (type(None), bool, int, float, complex, str, bytes)
_MAX_DEPTH = 24


def _dtype_has_metadata(dtype):
    """Reject metadata anywhere in a NumPy dtype's nested field tree.

    NumPy intentionally ignores ``dtype.metadata`` when comparing dtypes.
    Equality by itself therefore cannot authenticate a snapshot's dtype.
    The supported transaction model has NO metadata-bearing dtypes, even
    those buried in structured fields or subarray element types.
    """
    if dtype.metadata is not None:
        return True
    if dtype.fields is not None:
        return any(_dtype_has_metadata(field[0])
                   for field in dtype.fields.values())
    if dtype.subdtype is not None:
        return _dtype_has_metadata(dtype.subdtype[0])
    return False


def _scalar_token(value):
    if type(value) is float:
        return (float, struct.pack('!d', value))
    if type(value) is complex:
        return (complex, struct.pack('!dd', value.real, value.imag))
    if isinstance(value, np.generic):
        return (type(value), value.tobytes())
    return (type(value), value)


@dataclass
class _SnapshotValue:
    kind: str
    original: object
    content: object
    metadata: object = None


def _freeze(value, ancestors, depth=0):
    if depth > _MAX_DEPTH:
        raise UnsupportedStateError('Engine state nesting exceeds supported depth')
    kind = type(value)
    if kind in _SCALAR_TYPES or isinstance(value, np.generic):
        if isinstance(value, np.generic) and value.dtype.hasobject:
            raise UnsupportedStateError('Object-containing scalar is unsupported')
        return _SnapshotValue('scalar', value, _scalar_token(value))
    if kind is np.ndarray:
        if value.dtype.hasobject:
            raise UnsupportedStateError('Object arrays cannot be safely snapshotted')
        if _dtype_has_metadata(value.dtype):
            raise UnsupportedStateError('Arrays with mutable dtype metadata are unsupported')
        # A normal ndarray.copy() may omit bytes in structured dtype padding.
        # Copy as raw fixed-width records to preserve every element byte.
        values = np.empty_like(value, order='K')
        if value.dtype.itemsize:
            record_dtype = np.dtype(f'V{value.dtype.itemsize}')
            np.copyto(values.view(record_dtype), value.view(record_dtype))
        else:
            np.copyto(values, value)
        return _SnapshotValue('array', value, values,
                              (value.flags.writeable, value.strides))
    if kind not in (list, tuple, dict, set, frozenset):
        raise UnsupportedStateError(f'Unsupported engine state attribute: {kind.__name__}')
    if id(value) in ancestors:
        raise UnsupportedStateError('Cyclic engine state cannot be snapshotted')
    ancestors.add(id(value))
    try:
        if kind in (list, tuple):
            content = [_freeze(x, ancestors, depth + 1) for x in value]
        elif kind is dict:
            if any(type(k) not in (str, int, bool, float) for k in value):
                raise UnsupportedStateError('Engine mapping keys must be primitive scalars')
            content = [(k, _freeze(v, ancestors, depth + 1)) for k, v in value.items()]
        else:
            if any(type(x) not in _SCALAR_TYPES for x in value):
                raise UnsupportedStateError('Unsupported engine set element type')
            content = value.copy()
        return _SnapshotValue(kind.__name__, value, content)
    finally:
        ancestors.remove(id(value))


def _matches(current, frozen):
    if frozen.kind == 'scalar':
        return _scalar_token(current) == frozen.content if (
            type(current) is type(frozen.original)) else False
    if current is not frozen.original:
        return False
    if frozen.kind == 'array':
        original = frozen.content
        return (not _dtype_has_metadata(current.dtype)
                and current.dtype == original.dtype and current.shape == original.shape
                and current.strides == frozen.metadata[1]
                and current.flags.writeable == frozen.metadata[0]
                and current.tobytes() == original.tobytes())
    if frozen.kind in ('list', 'tuple'):
        return (len(current) == len(frozen.content)
                and all(_matches(x, y) for x, y in zip(current, frozen.content)))
    if frozen.kind == 'dict':
        return (list(current) == [k for k, _ in frozen.content]
                and all(_matches(current[k], item) for k, item in frozen.content))
    if frozen.kind in ('set', 'frozenset'):
        return current == frozen.content
    raise AssertionError(frozen.kind)


def _restore(frozen):
    """Restore original references and supported nested values, including aliases."""
    kind = frozen.kind
    ref = frozen.original
    if kind == 'scalar':
        return ref
    if kind == 'array':
        values = frozen.content
        try:
            # Restore dtype *before* shape: byte-order/field reinterpretation
            # otherwise corrupts the copy while preserving apparent values.
            if ref.dtype != values.dtype or _dtype_has_metadata(ref.dtype):
                ref.dtype = values.dtype
            if ref.shape != values.shape:
                ref.resize(values.shape, refcheck=True)
            if ref.strides != frozen.metadata[1]:
                ref.strides = frozen.metadata[1]
            if not ref.flags.writeable:
                ref.setflags(write=True)
            # Void-record copy preserves byte-exact structured padding too.
            if values.dtype.itemsize:
                record_dtype = np.dtype(f'V{values.dtype.itemsize}')
                np.copyto(ref.view(record_dtype), values.view(record_dtype))
            else:
                np.copyto(ref, values)
            ref.setflags(write=frozen.metadata[0])
            return ref
        except (TypeError, ValueError, RuntimeError):
            # Identity/alias restoration is impossible after some destructive
            # metadata edits. Restore engine-owned values and refusal instead.
            restored = np.empty_like(values, order='K')
            if values.dtype.itemsize:
                record_dtype = np.dtype(f'V{values.dtype.itemsize}')
                np.copyto(restored.view(record_dtype), values.view(record_dtype))
            else:
                np.copyto(restored, values)
            restored.setflags(write=frozen.metadata[0])
            return restored
    if kind == 'list':
        ref[:] = [_restore(item) for item in frozen.content]
        return ref
    if kind == 'tuple':
        # Preserve the original immutable tuple and external aliases whenever
        # its mutable children can be repaired in place. If a child had to be
        # rebound after unrecoverable metadata damage, create a replacement
        # tuple rather than leaving an incorrect child in engine-owned state.
        repaired = tuple(_restore(item) for item in frozen.content)
        return ref if all(a is b for a, b in zip(repaired, ref)) else repaired
    if kind == 'dict':
        entries = [(key, _restore(item)) for key, item in frozen.content]
        ref.clear()
        ref.update(entries)
        return ref
    if kind == 'set':
        ref.clear()
        ref.update(frozen.content)
        return ref
    if kind == 'frozenset':
        return ref
    raise AssertionError(kind)


class EngineStateTransaction:
    """Snapshot the full supported instance-state map of an engine.

    Snapshot creation is read-only. Restoration also removes new attributes.
    The binding lock itself is excluded, and always restored to its original
    identity if an adversarial predicate attempts to replace that attribute.
    """

    _EXCLUDED = '_phi_effect_binding'

    def __init__(self, engine, binding):
        if not hasattr(engine, '__dict__'):
            raise UnsupportedStateError('Engine must have a state dictionary')
        for base in type(engine).__mro__:
            slots = base.__dict__.get('__slots__', ())
            if isinstance(slots, str):
                slots = (slots,)
            if any(name not in ('__dict__', '__weakref__') for name in slots):
                raise UnsupportedStateError('Slotted subclass state requires an explicit adapter')
        self.engine_type = type(engine)
        self.engine = engine
        self.binding = binding
        self.fields = {
            name: _freeze(value, set())
            for name, value in vars(engine).items()
            if name != self._EXCLUDED
        }

    def unchanged(self):
        if type(self.engine) is not self.engine_type:
            return False
        actual = vars(self.engine)
        if actual.get(self._EXCLUDED) is not self.binding:
            return False
        if set(actual) != set(self.fields) | {self._EXCLUDED}:
            return False
        return all(_matches(actual[name], frozen)
                   for name, frozen in self.fields.items())

    def restore(self):
        if type(self.engine) is not self.engine_type:
            self.engine.__class__ = self.engine_type
        actual = vars(self.engine)
        restored = {key: _restore(value) for key, value in self.fields.items()}
        actual.clear()
        actual.update(restored)
        actual[self._EXCLUDED] = self.binding
