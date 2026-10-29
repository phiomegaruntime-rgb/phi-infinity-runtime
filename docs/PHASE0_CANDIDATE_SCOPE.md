# Phase 0 Candidate: Scope and Verification Boundaries

This candidate is based on the public `main` snapshot
`4ee4ea34b5b83cccff3463fec607c7ec0e10cd2a`. It adds the selected runtime
experiments, their tests, and the accompanying mechanical amendments while
retaining the documents already present in that public snapshot. It excludes
agent memory, pasted prompts/conversations, and unrelated attached assets.

## Reproduce the test suite

Use Python 3.13 or a compatible supported Python version with pytest installed:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider -ra -q
```

The final candidate commit and the exact result of this command must be recorded
by the release operator. A green result is required before calling this
candidate verified.

## Support checks and effects

The candidate contains several distinct levels of evidence; they must not be
treated as interchangeable:

- `m_machine` validates typed grounding, provenance, genealogy, and revocation
  within its in-memory model. Its tests exercise rejected and revoked
  derivations.
- `experimental_m_runtime_v2.AdmissionBoundary` validates fragment-graph
  admission, the configured machine/authority identity, and internally
  derived receipts. Its tests exercise forged receipt-shaped input and raw
  host values.
- `operational_m.transformation_bridge` can return a candidate result when its
  explicit prerequisites are supplied. It does not perform or promote a
  physical/external transformation.
- `src/gating.py` is a predicate-driven lock/reopen helper. It is not wired to
  the M admission boundary or to an effect sink.

Repository inspection does not establish an integrated, atomic
support-check-to-effect path. In particular, this candidate does not prove
that a rejected request causes zero external mutations, that evidence cannot
be revoked between checking and effect execution, or that a transaction
atomically couples support validation to an irreversible effect. No synthetic
effect controller is added to make that claim appear tested.

## Completion limits

This is a candidate collection of runtime experiments, not a claim that the
independent runtime is complete or that M is complete. Durable persistence and
replay, an independent service, an orchestrator, durable append-only audit,
and end-to-end tests using two distinct real clients remain outside the
verified scope unless separately implemented and demonstrated.
