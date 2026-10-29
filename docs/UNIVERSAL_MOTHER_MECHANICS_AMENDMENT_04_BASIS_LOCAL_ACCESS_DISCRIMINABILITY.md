# PHI-INFINITY AMENDMENT 04
# BASIS-LOCAL ACCESS DISCRIMINABILITY

**Status:** AUTHORITATIVE SUCCESSOR AMENDMENT

THIS AMENDMENT ADDS NO NEW FUNDAMENTAL CAUSAL OPERATION.

Its role is only to formalize faithful preservation of basis-local access
separability before M-level difference reconstruction.

## 1. Supplied basis and origin

A discrimination basis \(b\) is access representation only. It is supplied
inside one access package \(a\) and has no semantic, causal, ontological,
mechanical, automatic cross-basis, or automatic cross-access meaning.

The M-machine must not construct or select a basis after inspecting data.

Basis origin is representational metadata only. The permitted statuses are:

- `SUPPLIED_AS_ACCESS_BASIS`;
- `DERIVED_AFTER_ACCESS`;
- `BASIS_ORIGIN_UNRESOLVED`.

Only `SUPPLIED_AS_ACCESS_BASIS` may qualify a direct basis-local result.
Missing, ambiguous, or post-hoc-unqualified origin is `UNRESOLVED`.

## 2. Outcome representation

A supplied basis may associate a manifestation with a basis-local outcome:

\[
\operatorname{Outcome}_{a,b}(x,o)
\]

This means only that outcome record \(o\) is the supplied access
representation associated with manifestation \(x\) under \(a,b\). It does not
mean a real state, ontological state, persistent state, or causal state.

All outcome references use exact local access integrity consistent with
Amendment 03.

## 3. Two authorized outcome-relation forms

Amendment 04 permits both supplied forms:

### A. Basis-local resolution class map

\[
\operatorname{OutcomeClassMap}_{a,b}(o_{\mathrm{handle}})
\rightarrow
c_{\mathrm{handle}}
\]

### B. Direct supplied pair relation

\[
\operatorname{OutcomeRelation}_{a,b}(o_x,o_y)
\in
\{
\texttt{SEPARATELY\_RESOLVED},
\texttt{NOT\_SEPARATELY\_RESOLVED},
\texttt{OUTCOME\_RELATION\_UNRESOLVED}
\}
\]

No conversion between the two forms is inferred. If both are supplied and
conflict, the result is `OUTCOME_RELATION_UNRESOLVED`.

## 4. Resolution-class semantics

A resolution-class handle is opaque and basis-local. Its only permitted role
is to preserve that the supplied acquisition basis places an outcome in a
particular represented resolution class.

It has no semantic, ontological, causal, mechanical, magnitude, cross-basis,
or cross-access meaning.

If two outcomes resolve exactly to the same class under the same supplied
basis:

\[
\operatorname{NOT\_SEPARATELY\_RESOLVED}_{a,b}(o_x,o_y)
\]

If they resolve exactly to different supplied classes under that same basis:

\[
\operatorname{SEPARATELY\_RESOLVED}_{a,b}(o_x,o_y)
\]

These results do not imply identity, ontological difference, magnitude,
direction, dependency, causation, or mechanical relevance.

## 5. Exact relation and numerical firewall

The machine may preserve a direct supplied pair relation exactly. It must not
reconstruct one from raw values.

Raw numerical equality or inequality, floating-point comparison, epsilon,
tolerance, rounding, magnitude, distance, statistical significance, and a
bare numerical resolution value do not define outcome relation.

Missing, ambiguous, conflicting, or unresolved class or pair evidence yields
`OUTCOME_RELATION_UNRESOLVED`.

## 6. Basis-local discriminability

Only the following basis-local result is authorized:

\[
\begin{aligned}
&\operatorname{Connects}_a(w,x,y)
\land \operatorname{SuppliedBasis}_a(b)\\
&\land \operatorname{Outcome}_{a,b}(x,o_x)
\land \operatorname{Outcome}_{a,b}(y,o_y)\\
&\land \operatorname{OutcomeRelation}_{a,b}(o_x,o_y)
=\texttt{SEPARATELY\_RESOLVED}
\end{aligned}
\]

Result:

`DISCRIMINABLE_UNDER_BASIS`

When the supplied relation is `NOT_SEPARATELY_RESOLVED`, the result is:

`NOT_DISCRIMINATED_UNDER_BASIS`

When any required input is absent, ambiguous, conflicting, post-hoc, or
unresolved, the result is:

`UNRESOLVED`

This contract is basis-local only. It does not define global
`Discriminable_a`.

## 7. Multiple and cross-basis safety

Results for multiple supplied bases are preserved independently. The machine
must not vote, rank, aggregate, prefer, or collapse them into a global result.

Identical class-token text across bases does not establish comparability.
Different class-token text across bases does not establish distinction.
Without an independently supplied cross-basis contract, comparison is
`UNRESOLVED`.

Different genealogy evidence does not alter an outcome-basis result
automatically. Preserve genealogy-sensitive evidence under its own basis.

## 8. Magnitude and mechanics firewall

Basis-local discriminability does not imply:

- ontological distinction;
- \(\Delta\) magnitude or direction;
- dependency;
- exchange;
- causation;
- mechanical relevance;
- a new Mother Mechanics.

No `Delta`, dependency, exchange, causal, relevance, continuation, or FABEST
result is emitted by this amendment.

The executable access path stops at:

`GLOBAL_DISCRIMINABILITY_FRONTIER`