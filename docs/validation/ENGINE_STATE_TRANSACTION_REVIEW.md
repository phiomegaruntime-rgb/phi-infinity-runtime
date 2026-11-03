# Engine-owned state transaction — independent contribution

Frozen target: `4ee4ea34b5b83cccff3463fec607c7ec0e10cd2a`.
Contributor: Alex Moraru. This stage adds an **opt-in** transaction to the
existing serialized-effect integration, not a new PHI equation or replacement
numerical engine.

## Concrete counterexamples before this stage

1. A predicate for an already-attached `MultiAccessGating` could execute
   `engine.S[0, 0] = -999`, then return `True`. The earlier authorization
   checked only the Boolean decision and consequently ran real mechanics
   with the changed engine state.
2. An overriden `_step_phi_mechanics` could execute the real parent equations,
   then throw. `engine.step()` restored `mu` and `eta` in `finally`, but the
   already-changed `S`, `R`, and `pos` survived.
3. A boundary call could fail after partial native mutation, creating the
   same state discontinuity. The absence of a rollback contract was observable.

The new tests reproduce these scenarios on real `PhiSubstrateEngine.step()`
and real `step_with_boundary()` entry points, not fabricated wrappers.

## What the new transaction performs

Under the existing engine lock and shared `SynchronizedSupport.effect_window`:

1. Capture every supported instance attribute before the acceptance rule.
2. Reject an unsupported attribute or a subclass with additional `__slots__`
   before evaluating the predicate or mechanics.
3. Run the existing gate. On refusal or evaluation error, restore the
   supported state and retain FirstDivergence lock.
4. Compare every captured attribute (including byte-exact NumPy array
   contents, arrays' writeability, mutable-container identity, and engine
   class). A successful predicate that modified engine state is refused,
   rolled back, and locked.
5. Run exactly the original public numerical entry point, retaining the
   source publication lock until it returns. On any raised exception, restore
   captured engine-owned state and lock. Normal returns commit the state.

The transaction covers built-in primitive attributes, NumPy scalar types,
non-object NumPy arrays, and recursively supported list/tuple/dict/set
containers. It restores original mutable container references in place in
ordinary supported cases. Unsupported types are **rejected**, never ignored.
The actual native mechanics and boundary equations are AST-identical to the
frozen originals, excluding the already-existing authorization decorators.

### Rollback test source

`tests/test_transactional_effects.py` verifies:
- accepted-looking and negative predicates that mutate engine state;
- array rebinds, array aliases, nested subclass containers, changed class,
  new attributes and writeability flags;
- predicate mutation followed by exception;
- failures after genuine native equations and partial real boundary work;
- persistent lock and exact original numeric state on refusal;
- rejection of an unsupported slotted subclass before any callback runs;
- successful state updates from a supported subclass without false rollback;
- invalid progress after authorization, with restoration.

Run `python3 -m pytest -q tests/test_transactional_effects.py`.

## Engineering contract

State rollback is guaranteed for the **documented supported state model** of
engine-owned data. It is not a sandbox for caller code with arbitrary
filesystem, network, thread or third-party object effects. Those effects
cannot be undone by NumPy snapshots. For users who do not trust arbitrary
predicates or subclass method bodies, stage 08 adds an opt-in **sealed PHI**
profile: only the original engine, fixed Boolean support rule, primitive
numeric arguments, and copied native boundary receipts are accepted.

Unattached engines retain the exact previously published call paths and
outputs. This contribution does not modify the physical or theoretical claims
of PHI-INFINITY / M.

## 2026-11-02 follow-up: byte-exact metadata and alias handling

An independent reviewer reproduced a missing NumPy dtype restoration after
a callback changed the `S.dtype` byte order. This was independently reproduced
for native and boundary effects with callback True/False and then corrected.
The snapshot now uses fixed-width byte records to preserve structured padding
which `np.copyto` of structured fields can silently omit. Restores dtype
before shape, restores original strides when possible, and checks exact bytes.
Original tuple identity is retained when all children are repaired in place.
Metadata-bearing dtypes, including nested structured-field metadata, are
rejected as unsupported (as are object arrays). Metadata injected later is
also detected even though NumPy dtype equality ignores dtype metadata.
Some destructive ndarray mutations still cannot restore external aliases: the
engine may be rebound to a safe copy, and this is not an arbitrary-code sandbox.
See `tests/test_pr3_independent_recovery_byte_audit.py` and
`docs/validation/PR3_REVIEW_FINDINGS_AND_REOPEN_POLICY.md`.
