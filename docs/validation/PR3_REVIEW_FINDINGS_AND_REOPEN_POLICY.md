# PHI-INFINITY PR #3 — independently reproduced reviewer findings and bounded corrections

**Date:** 2026-11-02. **Scope:** offline reconstruction of the contributor's
nine-patch package against frozen upstream `4ee4ea34b5b83cccff3463fec607c7ec0e10cd2a`.
This audit did **not** access GitHub, verify the maintainer's stated tenth
commit `b74763ad2e7bd25927de78468b8aee7a12e3c6d0`, or merge PR #3.
We exclude the one contributor Mac instruction file the reviewer says was
removed, yielding a 93-file reconstructed pre-fix tree. The resulting source
is a local follow-up proposal, not a claim that any live branch has changed.

## Findings checked against code, not reviewer authority

| Observation | Original reproduction | Corrected behavior |
|---|---|---|
| Callback changes `engine.S.dtype` to its swapped byte order | All 4 of native/boundary x predicate True/False retain wrong dtype after refusal | Restore original dtype, array identity and every logical element byte under tested mutation |
| Native mechanical progress is `NaN` under versioned gate | All 4 of native/boundary x sealed/unsealed lock with `rejected_revision=None` | Record rejected revision under source publication lock; `REOPEN` requires a strictly newer *all-positive* publication |
| Aligned structured-array padding bytes | Ordinary NumPy `copyto` can leave padding dirty even when fields look equal | Snapshot and restore fixed-width raw record bytes, with independent padding-only mutation regressions |
| NumPy dtype metadata-only mutation | NumPy considers equal numeric dtypes with differing metadata; prior snapshot comparison missed this mutation | Refuse metadata-bearing dtypes at every nested level; detect metadata injection, reject the effect and restore the original dtype |
| Tuple alias after rollback | Earlier restoration rebuilt every tuple even where children were repairable | Preserve original tuple identity when all original children can be repaired; rebind tuple if a child cannot be restored in place |

The reviewer-suggested two-line dtype assignment fixes the specific endian
scenario, but are not the complete state restoration contract. We extend raw
snapshot/restore to preserve structured padding and record strides. Dtypes
with metadata (including metadata nested in structured fields) are **explicitly rejected before any predicate**;
object arrays were already rejected. Array view identity/alias recovery is
not promised after all possible destructive metadata edits: fallback may
rebind engine-owned state, and external aliases may remain altered.

## Explicit error-lock recovery policy

For a `VersionedQuorumGate` attached through the optional authorized-effect
path, **any exception raised within an acquired synchronized effect window**
records the currently observed source revision as `rejected_revision` and
locks execution. This includes support refusal, sealed argument refusal,
unsupported state snapshot, predicate mutation, and a later mechanics error.
The mark occurs *before releasing the shared publication lock*; a concurrent
cooperating publisher cannot overtake the recorded rejection.

`trigger_reopen()` then requires **both**:

1. A strictly newer `VersionedSupport.publish()` revision than the last
   rejected revision, and
2. Every required plain-boolean support channel currently `True`.

The still-invalid argument/state must be repaired before a subsequent call;
`REOPEN` never guarantees that invalid future work will succeed. No publication
(or a newer negative publication) cannot unlock. Reopening after a new positive
publication authorizes a *new attempt*, not a previous failed effect.

When the effect window **cannot be entered**, no trusted in-window revision was
captured; a locked gate may therefore have `rejected_revision=None`, and
explicit engine/gate reconstruction may be required. We do not fabricate a
revision after losing source serialization. The original callback gate's
`MultiAccessGating.trigger_reopen()` behavior is unchanged. Software support
publication is cooperative, not identity verification or physical attestation.

**Error propagation:** the original numerical `ValueError` remains observable
to the caller, while the versioned gate becomes locked. State rollback covers
the declared engine-owned model; external side effects are not transactional.
`accepted_revision` records a quorum check, not necessarily an effect commit.

## Independent verification performed for this follow-up

- Original reconstructed contributor suite: **180 passed**, zero skips.
- Follow-up adversarial module: **235 passed** across two real public effect
  paths and sealed/unsealed configurations, endian reversals for `pos/S/R`,
  dtype itemsize changes, NaN payload / signed-zero bytes, aligned padding,
  sliced arrays, tuple and array aliases, sealed preflight, snapshot refusal,
  concurrent publication and strictly fresh REOPEN. A 160-case additional
  public-effect matrix exercises 2-/3-D arrays, C/Fortran/transpose/reversed
  and sliced layouts, native/foreign-endian and aligned structured dtypes,
  both predicate decisions, and both public effect paths. Six additional
  cases reject metadata injection and nested-metadata snapshots.
- Combined: **415 passed**, zero skips in local Python 3.13/NumPy 2.3.
- Both original C11 comparators remain present and execute **44,000 bounded
  comparison decisions**: 5,120 gate transitions + 38,880 quorum decisions.
- 9 original patches replay sequentially on a separate local Git repository;
  **94 out of 94** nine-stage files match the reconstruction byte-for-byte.
- Frozen `core.py` (4 functions) and `boundary.py` (8 functions): **all 12
  original bodies AST-identical** after excluding authorization decorators.
- 8 independent deliberate faulty variants were each rejected by the new tests
  (dtype restoration, error revision, raw padding, tuple alias, stale REOPEN,
  nonpositive REOPEN, metadata-only dtype change, and nested dtype metadata).

The evidence is bounded software behavior. It proves neither a physical
implementation nor process-global atomicity, and it does not approve an
independent Rust/C11 rewrite or any Cocytus integration.

## Reproduction

```bash
python3 -m pytest -q -rs
python3 -m pytest -q tests/test_pr3_independent_recovery_byte_audit.py
```

Both original C11 oracle tests select an available C11 compiler; verify that
one is installed to avoid skips. The separately packaged offline audit
contains original-input SHA-256 hashes, patch-replay equality, independent
mutation sensitivity, and byte-for-byte frozen-baseline inventory.

## Separate metadata-equivalence flaw found during contributor self-review

NumPy regards `np.dtype('f8') == np.dtype('f8', metadata={'x': 1})` as
`True`. A predicate can therefore assign metadata to a live engine array
without changing its numeric values or bytes; ordinary dtype equality failed
to notice it. This is **not** one of the two reviewer findings. The independent
review found it in the follow-up and added a recursive dtype metadata guard,
including nested structured field dtypes, to the supported transaction model.
Both public effect paths now refuse such modification, restore the original
metadata-free dtype, and retain raw bytes and aliases in those tests.

The test count and artifact manifest refer to the *offline follow-up tree*,
not any fetched GitHub branch or maintainer-provided patch. This release does
not attest that the public PR has been merged or that its remote head matches
our synthetic local 93-file pre-fix baseline.


## NumPy compatibility and zero-warning evidence (2026-11-02 addendum)

The callback-enabled rollback deliberately restores a caller-visible NumPy
`ndarray` **in place** after a rejected adversarial dtype reinterpretation.
The restoration code and adversarial tests require `ndarray.dtype` assignment.
NumPy 2.5 **deprecated** setting `ndarray.dtype`; its suggested replacement
`array.view(new_dtype)` produces a view and does not, by itself, restore the
original external alias identity.  A private NumPy `_set_dtype` escape hatch,
process-wide warning filtering, or silent alias rebinding is **not** adopted.

Accordingly, this proposal explicitly limits its tested dependency support to
`numpy>=2.3,<2.5` in `requirements.txt` pending an independently reviewed
alias-safe migration.  This upper bound is a **compatibility constraint**, not
proof of modern NumPy support and not a resolution of the architectural issue.
We do not claim to have removed dtype mutation from the implementation.

Independently reexecuted on Linux/Python 3.13/NumPy 2.3.5:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -W error::DeprecationWarning -m pytest -q -rs
# 415 passed, no warnings or skips
```

`PYTEST_DISABLE_PLUGIN_AUTOLOAD` avoids unrelated third-party pytest plugin
initialization; it does not suppress warnings from the project or its tests.
For publication, repeat this command on the contributor's Mac after installing
the dependency constraints in the **private** virtual environment.  Do not
report the Mac zero-warning check as passing until it actually runs.

NumPy 2.5 may run the tests with deprecation warnings, but that version is
outside the stated compatibility range and is not release-qualified by this
addendum.  Future support should replace in-place dtype mutation only after
its alias, bytewise, metadata, and concurrent access behavior has separate
acceptance tests.  The core mechanics remain unchanged.
