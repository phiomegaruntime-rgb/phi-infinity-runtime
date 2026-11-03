# Independent gate audit — frozen Python target

Contributor: Alexandru (Alex) Moraru. Review target: `4ee4ea34b5b83cccff3463fec607c7ec0e10cd2a`.

**Scope:** `src/gating.py`, `MultiAccessGating.check_trajectory`,
`trigger_reopen`, and the genuine engine effect call sites.

## Frozen five transitions

Before running the tests, the expected state machine was:

| Event | Expected | Frozen implementation |
|---|---|---|
| Supported check | accept, unlocked | matches |
| Support withdrawn before check | FirstDivergence, locked | matches |
| Support restored without REOPEN | reject, locked | matches |
| REOPEN while unsupported | next check rejects and locks | matches |
| Restore plus REOPEN | next check accepted | matches |

Evidence is explicitly caller-supplied. The gate does not authenticate it.
REOPEN clears a boolean; the printed demand for an independent interval is not enforced.

## Actual effect boundary counterexample

`PhiSubstrateEngine.step()` changes `pos`, `S`, and `R` after an unrelated
isolated gate has accepted an earlier supplied metric. There was no
`MultiAccessGating` call in this engine execution path at the frozen ref.
The test demonstrates **an integration gap**, not a bypass of an integrated gate.
`src/boundary.py:step_with_boundary()` is another public mutating path.

## Predicate exceptions

In the frozen implementation, an exception raised by the caller's predicate
propagates and does **not** set `execution_locked`. That is a fail-open
exception policy, separate from evaluation to false. Fix belongs in later PR,
not this test-only PR. No result here establishes physical theory M.

Run: `python -m pytest -q tests/test_gate_independent_audit.py`
