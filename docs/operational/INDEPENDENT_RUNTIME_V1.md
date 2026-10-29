# Independent Runtime V1 — implemented boundary and reproduction

This is a local-only software runtime experiment based on the frozen Phase 1
successor. It does **not** complete M and does **not** authorize the numerical
engine step.

## Frozen decision and evidence protocol

The service uses the existing `m_machine.ProofKernel` with its frozen empty
positive mechanical-rule registry. For the exact target
`authorization for protected numerical state advancement`, proof closure
returns `UNRESOLVED` at
`FIRST_MECHANICAL_INFERENCE_RULE_FRONTIER`. Its missing premise is an already
frozen, registered, separately authorized, hash-verified
`MECHANICAL_INFERENCE_RULE` with exact premises and scope that concludes this
numerical-step authorization. No such rule exists in the frozen sources.

Each durable decision records three distinct stages:

1. **Conceptual target:** unresolved, with the exact missing premise from the
   proof kernel.
2. **Operational path:** the existing `src.core.PhiSubstrateEngine.step`
   entrypoint and hashes of both its source file and inspected method source.
3. **Numerical state:** no call to the engine is made; before/after hashes and
   the unchanged state version are recorded.

This evidence does not infer a proposition from the path or from changed
numbers. Signed support is an externally asserted statement and may be
recorded or revoked; it is not proof of truth, a grounded M premise, or
`DERIVED_M`. An unresolved request causes no numerical mutation.

## Identity, fragments, and signatures

At service startup, runtime identity is a canonical SHA-256 manifest of the
resolved Python executable bytes, all Python sources in the runtime, M-kernel,
existing engine, and fragment-admission packages, and the frozen-source byte
hashes pinned in `PHASE2_COMPLETION_CONTRACT.md`. The contract itself is pinned
by its SHA-256. Requests must carry closed `FragmentGraph` input with exact
runtime authority/machine fragments and numerical-step target; raw objects,
substituted anchors, extra receipt fields, and non-fragment graph records are
rejected. Success responses expose only a closed fragment graph.

The outer HTTP envelope contains transport/authentication fields and is
Ed25519-signed over canonical JSON. The operator-owned trust configuration
contains public keys and explicit allowed support IDs only. The service
rejects invalid signatures, unknown keys, unauthorized support IDs, altered
requests, replayed nonces, and revoked keys/support. Local issuer revocation is
an operator-only store action, not a client endpoint. The private signing key
must be provisioned and kept outside this repository; no key material is
included here.

## Persistence, service, and trust limits

SQLite uses WAL and `synchronous=FULL`. Each accepted request stores its
decision, support revision, unchanged numeric-state snapshot, request
idempotency record, nonce, and append-only hash-chained audit event in one
transaction. Duplicate request IDs with identical bytes return the stored
result; reusing an ID with different bytes or replaying a nonce is rejected.
The database checks its audit chain and numerical-state checksum on reopen.
SQLite triggers reject audit/request/nonce update or deletion.

The service refuses non-loopback binds. The orchestrator starts it as a
separate process; tests launch two distinct client processes and then restart
the store. Local filesystem/database ownership is the trust boundary. A
privileged database owner can alter the file, drop triggers, or rewrite the
entire hash chain; the hash chain is tamper-evident for ordinary partial
changes, not an externally anchored or hostile-host proof. No TLS, Internet
exposure, external irreversible effect, process-isolation sandbox, or
power-loss hardware test is claimed. Injected failures before and after SQLite
commit and service restart/idempotent replay are covered by tests.

## Reproduce

Requirements: Python with the repository dependencies and OpenSSL 3 CLI.
Run the exact suite with bytecode and pytest cache disabled:

```bash
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider -q
```

The end-to-end test creates its Ed25519 keypair and SQLite database in a
temporary directory, starts the service on `127.0.0.1`, and starts two
independent client processes. No key or database fixture is checked in.

To run the service manually, provide an operator-created JSON trust file
containing only public PEM keys and explicit support-ID scopes, then use:

```bash
python -m independent_runtime.service \
  --database /path/outside/repository/runtime.sqlite \
  --trust-config /path/outside/repository/trust-public.json \
  --host 127.0.0.1 --port 8765
```

The client accepts only a signed request file and sends it to `/v1/submit`.
Do not expose this service publicly or treat its signed assertions as M truth.

## Explicit attested-equations opt-in

The separate action `equations.step.attested` is an opt-in execution of the
existing `PhiSubstrateEngine.step`; it is not the native M action
`numeric.step`. The latter remains `UNRESOLVED` and cannot advance state.

The signed operation manifest binds the initial state SHA-256 and version,
mechanical progress, and exactly seven dependencies consumed by the current
engine: `sigma`, `alpha`, `beta`, `lmbda`, `gamma`, `mu`, and `eta`. Each
dependency has a separately published, revisioned assertion whose canonical
statement binds the parameter name, actual numeric value (including a known
zero), exact parameter scope, engine-model hash, and `src/core.py` hash. The
issuer must be allowlisted for every dependency support ID. The operation
signature covers the complete manifest; the service checks current support
revision, assertion digest, issuer, state hash/version, and request nonce both
before calculation and immediately before durable commit.

The service loads the stored arrays into a provisional instance of the real
engine and invokes its unchanged `step`. It records dependency IDs/revisions,
values, state hashes and the transformation as closed protocol fragments.
Missing, unavailable, non-finite, altered, stale, revoked, wrong-scope,
wrong-model/source or wrong-state dependencies reject without committing.
The M-native result remains `UNRESOLVED`; successful execution means only that
an authorized external issuer attested these inputs and the existing equations
were run. A valid signature does not prove the assertion physically true, and
does not derive M authorization. The assertion set must be explicitly
re-attested for a later state revision.

The two-node regression uses the independently recorded state and unchanged
equations: with `mu=0.05`, the first energy component changes by
`-0.002733781888455633` while the total remains `3.1`; with known `mu=0`,
energy exchange is zero while independent geometry still changes. These are
equation-specific observations, not universal M derivations.
