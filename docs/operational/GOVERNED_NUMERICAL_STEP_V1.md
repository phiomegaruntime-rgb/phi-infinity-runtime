# Opt-in supported step on the existing PHI numerical engine

## Transformation and declared support

The effect in this experiment is a single in-memory numerical transition of
the existing `src.core.PhiSubstrateEngine`: its `pos`, `S`, and `R` arrays are
advanced by the engine's unchanged `step()` implementation. The configured
operational requirement is one caller-recorded support ID for that step.

This requirement is deliberately not presented as a native M theorem,
authenticated identity, or independently verified physical fact. The current
frozen M rules do not authorize this numerical transition. The support text is
a caller assertion held by a process-local `CallerSupportAuthority`; code
holding that object can publish or withdraw it. This is not cryptographic
authentication or an access-control boundary against arbitrary code running
in the same process.

## Effective path

With `opt_in=True`, the governed path is:

1. `CallerSupportAuthority.verify()` records the current support revision.
2. `GovernedPhiStepper.step()` takes the same authority lock and checks that
   the required support is present, not awaiting reopen, and still at the
   verified revision.
3. It snapshots the actual engine's `pos`, `S`, and `R`, then calls that same
   engine instance's existing `PhiSubstrateEngine.step()`, without changing its
   equations.
4. It validates the resulting arrays' shapes, dtypes, and finite values. If
   transformation or validation raises, it restores all three arrays and the
   step parameters before returning the error.

The report contains hashes of the actual numerical arrays immediately before
and after the transition, plus the metrics returned by the engine. It is an
operational report, not an M receipt or proof of the caller's assertion.

## Reproduced numerical sample

Using two nodes, seed `13`, the positions
`[[-1, 0], [1, 0]]`, structural state
`[[2, 1, 0.5], [1.1, 2, 0.7]]`, residual `[0.1, 0.2]`, and
`mechanical_progress=1.0`, the gated call to the existing engine produced:

- Before: `pos=[[-1, 0], [1, 0]]`; `S=[[2, 1, 0.5], [1.1, 2, 0.7]]`;
  `R=[0.1, 0.2]`.
- After: `pos=[[-0.9959558724910916, 0], [0.9960594365150425, 0]]`;
  `S=[[1.9972662181115444, 1.0030209033317077, 0.5],
  [1.1027337818884557, 1.9969790966682923, 0.7]]`;
  `R=[0.1001554159580268, 0.20002457117551095]`.
- State SHA-256: `0073afe893aadc702d53c144abe6c64fcdfdf5e3920591968b434ce16fa21fb3`
  → `f84b4473173c74c895ddd42a341d55b700e6dc6bc3de5cfdcf7c5cb7a32132df`.

## Withdrawal, restoration, and reopen

Every publish, withdrawal, and reopen increments the support revision and
invalidates prior verification. Withdrawal also sets `reopen_required`.
Restoring support does not clear that flag. Reopen is rejected while support is
absent; after support is restored, reopen clears the flag but still requires a
new `verify()` before stepping. A stale or missing verification rejects before
the original engine arrays are changed.

## Concurrency and limits

The process-local `RLock` serializes updates made through the configured
authority object with governed steps. If withdrawal obtains the lock first, a
step is rejected; if a step already holds the lock, it completes before the
withdrawal takes effect. A transformation exception restores the original
numerical arrays before the governed call exits.

Direct calls to the historical `engine.step()` and direct writes to the
engine's public arrays bypass this gate and are not protected by its lock.
Other processes, external effects, durable storage, authenticated support
issuers, native M derivation of the requirement, and atomicity for irreversible
effects are outside this experiment. The original equations, historical entry
points, and frozen M contracts remain unchanged.
