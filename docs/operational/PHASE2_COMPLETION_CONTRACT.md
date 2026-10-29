# Phase 2 Independent Runtime Completion Contract

Status: frozen acceptance contract for work based on commit
`5224ddfb2ed4912ce13dafb9e0925f4c6ea6c3dd`.

This contract records the finite software requirements and the limits imposed
by the frozen M authorities. It is an acceptance checklist, not a new
mechanical law, proposition constructor, trust root, or authorization.
Implementation may satisfy a software requirement, but it may not weaken a
criterion below. A requirement that cannot be derived from current authority
must remain `UNRESOLVED` and name its missing premise.

## Frozen authority snapshot

The following source bytes are the baseline against which claims in this
contract were read:

| Source | SHA-256 |
|---|---|
| `docs/PHASE0_CANDIDATE_SCOPE.md` | `f0cf6e7d126946c67835101476746699aff4bc8d4645e3a203091286d206b4a6` |
| Amendment 05 — proof-kernel semantics | `945c00cdbb5923885a80b82d25bcf9bb4f48f5d3f7ef43b01a61bf7c45f012b4` |
| Amendment 06 — proposition semantics | `8d010881e43bf9c4bdb5c0382d54ddb8c1876304f3db78a151a8a43a16377b1b` |
| Amendment 07 — trusted grounding | `c36eac1e91393e382c20166afb274eab2bd2b3d88f0325e0ce820fbefd6bcaf6` |
| Amendment 08 — pairwise grounding | `34449eec97c60e5a8724b67d1fdef363e4145ae0d3ffefb9ba75304dd7059a9e` |
| Operational transformation/difference bridge | `01031a1d49bfda5c197511924691ad44dd7aa597f280b3e826388bb16bc9051d` |

Amendment 05 §§2, 3, 8, and 10 says only registered frozen mechanical
inference rules emit `DERIVED_M`, the frozen registry currently has zero
authorized positive mechanical rules, and unresolved proof closure is the
successful result at the first mechanical-inference frontier. Amendment 06
§§2, 8, and 10 supplies no transformation proposition constructor and no
arbitrary caller-fact constructor. Amendment 07 §§3–6 and 9 keeps
`GROUNDED_EXTERNAL` distinct from `DERIVED_M`; a valid signature can support
identity, integrity, freshness, or non-replay but does not establish source or
physical truth. Amendment 08 §§2, 10, and 13 says pairwise external
non-identity does not imply real difference and is not consumed by a frozen
mechanical rule. The operational bridge is candidate-only and does not
promote a result into the M kernel.

Therefore none of those sources authorizes the numerical engine step. The
missing premise is an already-frozen, registered, hash-verified
`MECHANICAL_INFERENCE_RULE` whose exact typed premises and scope derive
authorization for that exact numerical transformation. The implementation
must report `UNRESOLVED` at the applicable proof frontier and perform no
numerical mutation when this premise is absent. No caller assertion, valid
signature, operational candidate, or implementation callback may substitute
for it.

## Requirement / evidence / result matrix

Every row is a release gate. `PASS` requires the listed executable evidence
on the exact release commit; files, names, mocked collaborators, or partial
runs do not count. Baseline status is recorded before implementation.

| ID | Requirement | Required evidence | Baseline status |
|---|---|---|---|
| C1 | Bind runtime identity to actual executable bytes, all runtime code bytes, and exact frozen authority bytes. | Recompute SHA-256 at startup; alter a byte in each identity component and show admission rejects. Include interpreter executable bytes, not only a path or declared version. | NOT IMPLEMENTED |
| C2 | Reject replacement machine, authority, registry, receipt store, and non-fragment input/output. | Adversarial admission tests using substituted instances, forged receipt-shaped values, raw host values, and output values not admitted as exact fragments; each rejection has zero state change. | PARTIAL: experimental M runtime v2 has fragment admission; no binding to the numeric service. |
| C3 | Authenticate support issuers using cryptographic signatures and explicit authorization. | Valid authorized signature accepted as an external assertion; false signature, unknown/revoked key, unauthorized scope, altered request, replay, and revoked support rejected; immutable audit records preserve the reason. | NOT IMPLEMENTED in the governed numerical path. |
| C4 | Do not promote a valid signature into truth or M derivation. | Tests and output distinguish `GROUNDED_EXTERNAL` from `DERIVED_M`; signature validation alone never authorizes the numeric effect. | FROZEN LIMIT; must remain true. |
| C5 | Preserve the sequence conceptual proposition → exact operational path → numerical formalization with verifiable evidence at each stage. | Each stage has an exact typed record, identity/hash, scope, provenance, and tested link to the next; absent derivation yields `UNRESOLVED`, not a guessed mapping. | NOT IMPLEMENTED as one verifiable protocol. |
| C6 | Use only derivations actually supported by the frozen M kernel to authorize the protected numerical step. | Exact kernel result and receipt genealogy are checked by the service; the engine remains unchanged on missing/invalid/unresolved derivation. | `UNRESOLVED`: no frozen registered rule authorizes this step. |
| C7 | Preserve opt-in gating, candidate isolation, exact support revision checks, reentrant revocation protection, and no mutation on rejection. | Regression tests exercise missing/stale/revoked support and reentrant revoke, republish, and restore; retain and inspect aliases to original arrays. | PASS on predecessor 5224 for phase-1 in-memory path; must remain passing. |
| C8 | Persist decisions and state with durable replay and an append-only integrity-checked audit. | Restart, duplicate request, hash-chain tamper, and crash/failure before and after commit tests; state and decision are read from one durable transaction. | NOT IMPLEMENTED. |
| C9 | Provide a separate local service and minimal orchestrator without Internet exposure or embedded secrets. | Start service as a distinct process on loopback only; exercise real request/response and reject non-loopback bind; configuration contains no private key. | NOT IMPLEMENTED. |
| C10 | Demonstrate end-to-end use by at least two distinct real client processes. | Process IDs differ; both use the service; test concurrent/duplicate requests and verify durable decisions and state after service restart. | NOT IMPLEMENTED. |
| C11 | Preserve the 312 predecessor tests and add adversarial regression coverage. | Full suite on the exact commit with bytecode disabled and pytest cache provider disabled; report exact totals and exit status. | BASELINE: 312 passed on 5224. |
| C12 | Keep trust, atomicity, and exposure limits explicit. | Documentation states issuer key ownership/rotation/revocation, local filesystem/database trust assumptions, transaction boundary, and that external irreversible effects are not atomic. | NOT IMPLEMENTED for an independent service. |

## Release decision

The independent software runtime may be called complete only if every
implementable software row C1–C3 and C5, C7–C12 has passing evidence and C6
has the explicit frozen-authority outcome above. C6 being `UNRESOLVED` means
the runtime must not execute the numerical step as an M-authorized effect;
it does not mean M is complete or that the missing premise is false.
Rows C4 and the authority firewall are invariants, not waivable gates.

Do not deploy, bind to a public interface, include private keys/secrets,
memories, conversations, or attachments, or modify the frozen M sources while
implementing this contract.
