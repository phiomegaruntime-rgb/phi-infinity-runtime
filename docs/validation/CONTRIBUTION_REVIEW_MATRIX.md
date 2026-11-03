# Contribution review matrix — evidence, boundaries and precise claims

| Component | Original issue | Proposed change | Evidence | Cannot claim |
|---|---|---|---|---|
| Gate transitions | No direct gate tests | Five frozen-state regression | `tests/test_gate_independent_audit.py` | Source authentication |
| Predicate failure | Unexpected exceptions did not lock | Fail-closed evaluation | `tests/test_gate_predicate_fail_closed.py` | That support was physically absent |
| Native real effect | No gate call site | Opt-in, serialized authorization of `engine.step()` | `tests/test_authorized_real_effects.py` | Prevent raw `.S`/`.R` writes |
| Boundary real effect | Separate mutating route | Same opt-in guard on `step_with_boundary()` | Exact state refusal and parity tests | That all possible Python callers are guarded |
| Check/effect race | Fresh read alone leaves a gap | Shared lock holds across real effect | Deterministic two-thread test | External atomicity across processes or physical world |
| Multi-language oracle | Only Python gate semantics | Independent C11 bounded state machine, 5120 decisions | `tests/test_c11_gate_oracle.py` | Proof of the M theory |
| Numerical behavior | No new physics permitted | Original mechanics untouched | Bit-exact state/result parity on tested cases | Formal global equivalence |

## Source review locations

`src/gating.py` stays the only definition of FirstDivergence and REOPEN.
`src/effect_authorization.py` owns the optional support transaction contract.
`src/core.py` and `src/boundary.py` gain only the authorization hook, not a
second state transition implementation.

## No hidden compatibility claim

- Normal, unattached engines remain ungated by design.
- `SynchronizedSupport.publish()` serializes competing *cooperative threads*.
- An out-of-band external change still can invalidate support after capture.
- `trigger_reopen()` does not itself validate interval independence.
- Direct updates to engine public arrays and calls to private mechanics remain
  possible and outside this feature's documented public entry-point contract.
- Error recovery from a midway mathematical exception is not a numerical
  rollback contract.
- Archived C11 tester check totals exercise C11 algorithms, not PHI mechanics.

Nothing in this contribution claims a completed physical implementation of M.

## Added review stages after the original five

| Stage | Source-backed enhancement | Verification | Scope |
|---|---|---|---|
| 06 | `EngineStateTransaction` for all supported instance fields; predicate mutation refusal; rollback after native and boundary exceptions | `tests/test_transactional_effects.py` | Opt-in protected effects; unrecognized state refused before mechanics |
| 07 | `VersionedSupport` and `VersionedQuorumGate`, with no user callback and requiring a newer positive software publication before REOPEN | `tests/test_versioned_quorum_protocol.py` | Local cooperative publication, not a physical attestation |
| 08 | Sealed native PHI profile rejecting subclass mechanics, custom progress/array hooks, invalid state schema; independent C11 versioned oracle | `tests/test_sealed_phi_effect_profile.py`, `tests/test_c11_versioned_quorum_oracle.py` | Exact built-in engine and typed numeric evidence only |
| 09 | Staged review documentation and real examples | `python -m examples.versioned_sealed_gate`, all tests | Source comments, application instructions, provenance |

**Changed contract:** Under an attached gate, supported engine-owned numerical
state is now rolled back on refusal or a failed effect (stage 06). This
supersedes the earlier row which said errors had no numerical rollback.
When sealed mode is requested (stage 08), the runtime refuses arbitrary
acceptance predicates and subclass methods rather than pretending arbitrary
Python external side effects can be transactionally undone. This also
supersedes the original report's `trigger_reopen()` limitation *for the new
versioned gate only*; the original gate retains its original REOPEN semantics.
