# PHI-INFINITY EXPERIMENTAL M RUNTIME V2

**Status:** FROZEN CONCEPTUAL AUTHORITY

This authority is independent from `m_machine` CURRENT and from the prior
`experimental_m_runtime`. It defines the representation boundary only; it does
not add a new physical law or claim universal physical proof.

## 1. Closed fragment foundation

1. Every semantically relevant value is represented by a fragment.
2. No semantically used value is external to the closed fragment graph.
3. `INFINITO` is the root fragment of every admitted execution snapshot.
4. Every relation, rule, authority item, hash, metadata item, provenance,
   ancestry, genealogy, operator, criterion, status, decision, reason, error,
   receipt, and output is a fragment or a relation between fragments.
5. A host value that is not converted to a fragment before admission is
   rejected and cannot contribute to `ALLOW`.

## 2. Ordered M-only admission

The authoritative execution order is:

```text
M-only conceptual solution
→ frozen solution receipt
→ exact M path
→ formalization
→ execution
→ output closure
```

Only one public admission boundary may emit `ALLOW`.

## 3. Closure and genealogy

The input graph must be completely closed before execution:

- every node is a fragment;
- every node kind is a fragment reference;
- every edge is a fragment reference;
- every reference resolves;
- every node is reachable from the `INFINITO` root;
- authority and frozen hashes are represented and match the frozen authority.

The output graph is checked again after execution. No output fragment may
escape the `INFINITO` closure.

No closure may propagate beyond the genealogy and dependencies actually
represented in the graph. A claimed closure without accessible genealogy or
dependencies is not a terminal negative result: it emits `REOPEN`.

## 4. Recursive anti-false-sufficiency rule

The anti-false-sufficiency rule is itself a fragment in the same graph and is
subject to the same closure checks as every other rule.

If a claim fragment lacks represented genealogy or dependency support, the
authorized result is `REOPEN`. The runtime must not convert unsupported
closure into `ALLOW`, `BLOCK`-as-final-truth, or an inferred replacement.

## 5. Boundary and receipt rule

After admission, the semantic engine consumes only `FragmentRef` values and a
closed `FragmentGraph`. It does not consume raw strings, dictionaries,
numbers, booleans, callbacks, or arbitrary host objects.

Execution receipts are produced inside the authorized M-only path. Caller
supplied receipt-shaped fragments are evidence candidates only; they cannot
authorize execution or replace the frozen receipt.

The result of admission is a fragment graph and fragment references. A raw
dictionary is never an admitted output.