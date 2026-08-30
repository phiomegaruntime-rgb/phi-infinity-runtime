
# PHI-INFINITY Validation

This directory preserves falsification work separately from the runtime.

## Categories

### Permanent regression tests

Located in:

`tests/`

These encode invariants that future PHI-INFINITY changes are not permitted
to break silently.

### Reproducible research/validation gates

Located in:

`validation/gates/`

These may test mathematical identifiability, research hypotheses or other
properties that are important but are not automatically treated as
fundamental runtime invariants.

### Evidence

Located in:

`validation/evidence/`

These files preserve outputs, collected-test manifests and repository
provenance from confirmed validation runs.

### Validation ledger

See:

`docs/validation/VALIDATION_LEDGER_CURRENT.md`

A passing gate means only that the specific attempted falsification did not
destroy the tested PHI property.

It does not imply universal proof of PHI-INFINITY.

<!-- PHI:EMPIRICAL_GATES:START -->
## Empirical Reality Gates

Empirical Reality Gates are separate from permanent runtime regression.

Alpha:

`gates/empirical_reality_gate_alpha.py`

Direct source tables:

`data/empirical_reality_gate_alpha/`

Actual execution evidence:

`evidence/2026-08-30/empirical_reality_gate_alpha.txt`

The preserved source tables are public-table transcriptions rather than
original raw instrument files.

A passing empirical gate establishes empirical compatibility for the tested
families, not universal proof.
<!-- PHI:EMPIRICAL_GATES:END -->
