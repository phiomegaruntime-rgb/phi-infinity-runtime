# Sealed opt-in PHI numerical effect profile

Stage 08 adds `engine.attach_gate(gate, source, sealed=True)` to **exclude**
Python callbacks and unregistered subclass state from the specific protected
numerical path. It does not substitute any PHI mechanics or demand new hardware.

## Closed contract

- Engine must have the exact native `PhiSubstrateEngine` class, not a subclass.
- Gate must be exact `VersionedQuorumGate`, and publisher must be exact
  `VersionedSupport` bound to that gate.
- The engine instance must have exactly the native state fields. In-progress
  steps verify scalar values and the shapes/types of its three float64 arrays.
- Progress arguments must be built-in `float`/`int`. `__float__` on caller
  objects is never invoked by this mode.
- Boundary receipts must be an exact `BoundaryEffectReceipt` with float64
  arrays of required shapes. Each array is copied before the actual numerical
  effect, not passed as an externally mutable reference.
- All protected work remains serialized with the support publisher; engine
  arrays are transacted and rolled back on exceptions.
- No user-defined acceptance callback is evaluated. No user-defined subclass
  mechanics are executed by the sealed path.

Usage:

```python
from src.core import PhiSubstrateEngine
from src.effect_authorization import SynchronizedSupport
from src.versioned_support import VersionedSupport, VersionedQuorumGate

engine = PhiSubstrateEngine(n_nodes=8, seed=42)
support = VersionedSupport({'ch_a': True, 'ch_b': True})
gate = VersionedQuorumGate(support, ('ch_a', 'ch_b'))
engine.attach_gate(gate, support, sealed=True)
engine.step()
support.publish({'ch_a': False, 'ch_b': True})
# Next engine.step(): FirstDivergenceException, no PHI state effect.
```

Runnable real numerical example: `python3 -m examples.versioned_sealed_gate`.

## Why this strengthens rather than replaces PHI

A Python function with arbitrary filesystem, OS or network permissions cannot
be guaranteed rollback-safe by a numerical engine. The sealed profile solves
that *within its supported path* by declining arbitrary predicates, subclass
method bodies, dynamic numeric protocols and object-array argument hooks.
This is a **closed call contract**, not a general-purpose Python sandbox or
physical authentication. A hostile participant with direct access to the
Python process, source objects, class definitions or external resources
remains outside the authorization security boundary.

The positive, no-fault sealed path runs the same original native and
boundary-aware PHI calculations. Tests compare results and all three engine
arrays byte-for-byte against unstaged, ungated copies across multiple seeds
and progress values. Nothing in this work alters the eleven laws or asserts
that PHI-INFINITY is a physically universal implementation.

Run:

```bash
python3 -m pytest -q tests/test_sealed_phi_effect_profile.py
```
