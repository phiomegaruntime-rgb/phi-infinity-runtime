# Versioned multi-access support and software-enforced REOPEN

Frozen target: `4ee4ea34b5b83cccff3463fec607c7ec0e10cd2a`.
Contributor: Alex Moraru.

`src/versioned_support.py` supplies two **optional** components:

- `VersionedSupport`: a synchronized publisher of plain dictionaries of
  **exact built-in Boolean** flags. Every `publish()` commits a new monotonic
  local revision under the support/effect lock. `read_revision()` returns a
  coherent `(revision, copied_flags)` pair.
- `VersionedQuorumGate`: a `MultiAccessGating` implementation that requires
  **all configured channels** to be `True`. It reads its bound publisher under
  lock, ignoring the caller's `step_metrics` argument. It executes no
  caller-supplied acceptance callback.

## Recovery state machine

Suppose `required_channels=('sensor_a','sensor_b')` and the source is accepted
at revision `r=0`.

| Input | Outcome |
|---|---|
| First check, both channels true | Accepted |
| New publish with `sensor_a=False` | Revision increases |
| Next check | FirstDivergence; lock and rejected revision recorded |
| `trigger_reopen()` with unchanged or negative evidence | Refused, lock persists |
| New independent **software publication** with both channels true | Revision increases |
| `trigger_reopen()` | Unlocks only when revision is strictly newer than rejection |
| Next supported check | Accepted |
| Caller passes forged `{'sensor_a':True}` while provider says false | Rejected |

The revision contract is a deterministic local **fresh-publication
condition**; it does not prove the new observation is independent in the
physical world. Only the actual sensor/publisher implementation can speak to
its provenance. Direct writes to internal Python attributes bypass this
cooperative protocol and are not described as authenticated inputs.

## Exhaustive independent verification

`verification/c11/versioned_quorum_oracle.c` defines a separate C11 reference
state machine over 6 event types and every length-5 event string:
`6^5 = 7,776 sequences`, yielding **38,880 reference decisions**. The Python
comparison in `tests/test_c11_versioned_quorum_oracle.py` invokes the actual
versioned gate for every native reference row. It also supplies deliberately
forged check metrics to prove the decision reads the bound support source.

The existing C11 oracle from stage 04 separately checks 5,120 original gate
transition decisions. Neither oracle is a proof about an external sensor, the
truth of M, or the completeness of the PHI physical model.

Run:

```bash
python3 -m pytest -q tests/test_versioned_quorum_protocol.py tests/test_c11_versioned_quorum_oracle.py
```

The original `MultiAccessGating.trigger_reopen()` is intentionally unchanged
for compatibility. New verification requirements are **opted into** by
choosing `VersionedQuorumGate`.

## 2026-11-02 follow-up: execution-error revision recovery

The original stage-07 direct support-withdrawal protocol worked, but it
failed to mark `rejected_revision` when a **real PHI effect** raised after an
accepted versioned quorum check. NaN mechanical progress reproduced this in
all four native/boundary and sealed/unsealed combinations. The authorized
effect now records any in-window execution refusal under the same source
publication lock, including preflight and snapshot errors. REOPEN still needs
a new strictly later publication with all required channels positive. A failed
source-window acquisition has no trustworthy revision and may instead require
reconstruction. The original nonversioned gate is unmodified.

The definitive bounded policy, explicit limitations and test evidence are in
`docs/validation/PR3_REVIEW_FINDINGS_AND_REOPEN_POLICY.md`.
