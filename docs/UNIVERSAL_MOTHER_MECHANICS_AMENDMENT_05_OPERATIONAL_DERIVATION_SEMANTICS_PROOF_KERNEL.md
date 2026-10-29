# PHI-INFINITY AMENDMENT 05
# OPERATIONAL DERIVATION SEMANTICS / PROOF KERNEL

**Status:** AUTHORITATIVE SUCCESSOR AMENDMENT

THIS AMENDMENT ADDS NO NEW FUNDAMENTAL CAUSAL OPERATION.

THIS AMENDMENT DEFINES HOW FROZEN RULES MAY BE APPLIED.
IT DOES NOT DEFINE NEW MECHANICAL RULE CONTENT.

It preserves the frozen Mother Mechanics, the Fundamental Laws, Amendments
01–04, the temporal closure, and the native represented mechanics.

## 1. Proof semantics and mechanical content

\[
\boxed{
\text{PROOF / EXECUTION SEMANTICS}
\neq
\text{SUBSTANTIVE MECHANICAL RULE CONTENT}
}
\]

The proof kernel may verify authority, match exact typed premises and scopes,
construct receipts exactly as a frozen rule specifies, preserve provenance
and proof genealogy, preserve duplicates and conflicts, compute proof closure,
and emit `UNRESOLVED` or justified `REOPEN`.

It must not decide dependency, exchange, redistribution, transformation,
propagation, consequence, readjustment, continuation, causal relevance, or
physical mechanism.

## 2. Rule classes and emission firewall

The rule classes are:

- `ACCESS_REPRESENTATION_RULE`;
- `EXECUTION_CONTROL_RULE`;
- `MECHANICAL_INFERENCE_RULE`;
- `FALSIFICATION_RULE`.

An `ACCESS_REPRESENTATION_RULE` or `EXECUTION_CONTROL_RULE` must never emit
`DERIVED_M`.

Only a separately audited, frozen, registered, and hash-verified
`MECHANICAL_INFERENCE_RULE` may emit `DERIVED_M`.

A `FALSIFICATION_RULE` may emit only the exact frozen falsification result
declared by that rule.

At the freeze of this amendment, the raw proof-kernel registry contains zero
authorized positive `MECHANICAL_INFERENCE_RULE` entries.

## 3. Frozen rule identity and registration

Every rule must expose a canonical ID, rule class, authoritative source and
range, authority-range hash, complete semantic specification and hash, exact
premise schema, scope constraints, conclusion schema, unresolved behavior,
implementation identity and hash where applicable, version, and any required
separate authorization.

Implementation code may execute an already frozen semantic rule. A callback
must not define mechanical meaning. A mechanical rule whose meaning exists
only inside implementation code must be rejected.

Changing a rule's semantics creates a new rule identity. Historical receipts
retain the exact rule and implementation hashes used to create them.

## 4. Exact premise and scope matching

A rule may fire only when its exact typed premises are present in the same
authorized scope or are connected by an explicitly authorized scope relation.

Matching must not use semantic similarity, fuzzy labels, approximate values,
inferred identity, filenames, human categories, cross-access token equality,
cross-basis token equality, model fitting, or nearest-neighbour search.

Every application preserves applicable access, basis, scale, field or context,
genealogy, and mechanical execution-instance scope. No local conclusion is
silently globalized.

## 5. Receipts, provenance, and history

Every conclusion preserves direct parent receipt IDs, proof genealogy, rule
ID and class, rule hash, authority source/range/hash, execution scope, evidence
provenance, result class, derivation status, and implementation mapping/hash
where applicable.

\[
\boxed{
\text{HISTORICAL RECEIPT VALIDITY}
\neq
\text{CURRENT APPLICABILITY}
}
\]

Proof history is append-only. Later access must not rewrite or delete a
historical receipt. It may produce a new applicability result, conflict,
superseding current reconstruction, additional provenance, or unresolved
current state.

## 6. Proof closure and scheduling

For one immutable execution snapshot and frozen rule set, the kernel loads
valid receipts, applies every exactly enabled rule, appends genuinely new
proof information, and repeats until no new proof information exists.

This is `PROOF_CLOSURE`, not physical equilibrium.

The result must not depend on first-rule, newest-rule, source-order,
shortest-proof, or implementation-order preference. Any priority relation
must itself be explicit frozen authority.

Exact duplicate conclusions may share one conclusion identity only if every
distinct proof genealogy remains preserved. Semantic equivalence must not be
inferred.

## 7. Conflict and contradiction

Exact incompatible conclusions in overlapping scope are both preserved with
their proof genealogies. The affected current target becomes `UNRESOLVED`
unless an explicit frozen rule resolves the incompatibility.

The kernel may mark contradiction only when exact result types declare mutual
exclusion or an explicit frozen rule declares two typed conclusions
incompatible. It must not use semantic, numerical, statistical, or domain
contradiction heuristics.

## 8. Negation, unresolved, reopening, and falsification

Failure to derive \(Q\) does not imply \(\neg Q\).

`UNRESOLVED` means that current authorized premises and frozen rules do not
uniquely justify the target conclusion under the current scope. It does not
mean false, zero, absent, impossible, no real relation, `FirstDivergence`, or
software failure.

`REOPEN` is execution control only. It may request access, scale, field,
boundary, genealogy, or an explicitly justified combination only when the
unresolved receipt chain supports that request. It must not invent replacement
evidence and must not emit `DERIVED_M`.

Proof closure exhaustion must not emit `FirstDivergence`. FirstDivergence may
be emitted only by a separately frozen `FALSIFICATION_RULE` whose exact
prerequisites are valid receipts.

## 9. Candidate and native-mechanics firewalls

The proof kernel contains no graph enumeration, hidden-node insertion,
mechanism proposal, scoring, probability, optimization, ranking, model
selection, or free candidate generation.

Its architecture is:

\[
\text{RECEIPTS}
\rightarrow
\text{FROZEN EXPLICIT RULES}
\rightarrow
\text{PROOF CLOSURE}.
\]

Executing supplied native mechanics is not reconstructing mechanics from raw
access. Existing native represented operations are not raw proof-kernel rules
unless separately audited, frozen, and registered.

## 10. Current raw frontier

With zero authorized positive raw mechanical rules, proof closure produces
zero new `DERIVED_M` facts. This is the required successful behavior.

Raw access execution therefore preserves Amendment 03 access integrity and
Amendment 04 basis-local results, invokes the proof kernel, returns
`UNRESOLVED`, and stops at:

`FIRST_MECHANICAL_INFERENCE_RULE_FRONTIER`

The absence of a mechanical rule is a specification frontier and does not
automatically justify `REOPEN` or `FirstDivergence`.

The remaining substantive research question is:

> What is the first substantive mechanical inference rule uniquely forced by
> frozen Mother Mechanics, if any?
