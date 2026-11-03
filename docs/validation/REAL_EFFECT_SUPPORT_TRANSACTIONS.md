# Opt-in guard on real PHI effect paths — precise scope

Contributor: Alex Moraru. Target: frozen upstream tree
`4ee4ea34b5b83cccff3463fec607c7ec0e10cd2a`.

## Why the original gap mattered

The frozen `MultiAccessGating.check_trajectory()` was never called by
`PhiSubstrateEngine.step()` or `boundary.step_with_boundary()`. Merely adding a
fresh reader call at the entrance is still susceptible to a support withdrawal
**between** the observation and the effect. A reader that returns a stale true
observation remains sufficient to drive a real PHI step. This is a real
check/effect race; no alternative physics model has been invented.

## Integration contract

An engine may opt in with:

```python
from src.core import PhiSubstrateEngine
from src.gating import MultiAccessGating
from src.effect_authorization import SynchronizedSupport

support = SynchronizedSupport({'present': True})
gate = MultiAccessGating(lambda evidence: evidence['present'])
engine = PhiSubstrateEngine(seed=42)
engine.attach_gate(gate, support)
engine.step()                       # passes while support published as present
support.publish({'present': False})
engine.step()                       # FirstDivergenceException, no effect
```

`SynchronizedSupport` deep-copies evidence at initialization, publication and
reading. The guarded **actual** `step()` / `step_with_boundary()` holds the same
synchronization lock from fresh evidence read, through the predicate check,
through the complete original numerical effect. Cooperating publisher threads
cannot withdraw evidence through `publish()` until the effect completes.
A matching per-engine lock serializes concurrently invoked guarded effect calls.
Reentrant `publish()` while an effect is active refuses explicitly.

A failed check changes `gate.execution_locked`, but leaves `engine.pos`, `engine.S`,
`engine.R`, `engine.mu`, and `engine.eta` unchanged; tests assert exact equality.
The counter counts accepted checks, not physical time or a guaranteed complete
effect, and does not define a new mechanical clock.

A second `attach_gate()` is rejected. A single gate object cannot attach to
multiple engines. Ungated engines follow the unchanged native equations,
with no injected support checks; accepted guarded steps must be byte-identical
to their ungated counterparts on the same host (tested across seeds/progress).

## Guarantees and non-guarantees

| Claim | Status |
|---|---|
| Isolated five-step lock/REOPEN protocol | exercised |
| Refusal blocks real native and boundary-aware entry points | exercised |
| Concurrent `support.publish()` cannot interleave with guarded effect | exercised using actual native mechanics in two threads |
| Original PHI equation outputs match when support accepts | tested numerically bit-for-bit for specified cases |
| Support authenticity / independent observation | **NOT PROVIDED** |
| External sensor or another process cannot change while effect runs | **NOT PROVIDED** |
| Python code cannot mutate `engine.S` / call a private helper directly | **NOT PROVIDED** |
| Reopening proves an independent interval | **NOT PROVIDED** |
| Mechanical step partial failures roll back supported engine-owned state | **PROVIDED from optional stage 06**, including predicate mutation refusal and real effect exception recovery |
| A universal physical claim about M | **NOT CLAIMED** |

The guarded contract is therefore **cooperatively serialized in-process
publication**, not globally atomic physical support. It addresses the specific
race *only if every publisher goes through the same support object*. An
external reader without this contract cannot inherit the guarantee. Direct
writes to mutable engine arrays bypass the public effect interfaces.

The provided adversarial test explicitly demonstrates stale publication after
an out-of-band value changes. It is a documented limitation, **not** a
passing security result. Separately, `trigger_reopen()` still clears a boolean
and does not enforce temporal independence. Authentic support provenance and
trusted REOPEN verification require a separately agreed interface/specification.

## Why no change to M or PHI mechanics?

The original `_step_phi_mechanics()` and
`_step_with_boundary_phi_mechanics()` are not redefined, substituted or
rewritten. This protects the contributor/maintainer boundary and avoids
smuggling in a new interpretation of admissibility. The decorator is placed
on the real public effect paths, not on a made-up stand-in wrapper.

Run: `python -m pytest -q tests/test_authorized_real_effects.py`.


## Later transaction and closed-rule extensions

The above original stage-03 notes intentionally describe what stage 03 alone
implemented. A later, separately reviewable **stage 06** adds a supported
engine-state transaction, closing its previously noted numerical rollback gap.
A later **stage 07** introduces versioned Boolean channel support and enforced
new-publication recovery. **Stage 08** introduces the sealed native profile to
avoid arbitrary Python callbacks and subclass methods within this code path.
See [state transactions](ENGINE_STATE_TRANSACTION_REVIEW.md),
[versioned quorum](VERSIONED_QUORUM_AND_REOPEN.md), and
[sealed profile](SEALED_PHI_PROFILE.md).
