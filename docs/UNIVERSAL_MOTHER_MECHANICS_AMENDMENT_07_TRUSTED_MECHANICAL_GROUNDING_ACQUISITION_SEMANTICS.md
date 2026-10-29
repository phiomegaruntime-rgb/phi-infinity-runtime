# PHI-INFINITY AMENDMENT 07
# TRUSTED MECHANICAL GROUNDING / ACQUISITION SEMANTICS

## 1. Authority boundary

THIS AMENDMENT ADDS NO NEW FUNDAMENTAL CAUSAL OPERATION.

THIS AMENDMENT DOES NOT DERIVE PHYSICAL TRUTH FROM SYMBOLIC DATA.

THIS AMENDMENT DEFINES HOW EXTERNALLY GROUNDED ACQUISITION PREMISES ARE
REPRESENTED, VALIDATED, SCOPED, AUDITED, AND KEPT DISTINCT FROM M-DERIVED
CONCLUSIONS.

THIS AMENDMENT DOES NOT DEFINE SOURCE SEMANTICS.

This amendment is an EXTERNAL EPISTEMIC ACQUISITION INTERFACE and a
NON_GENERATIVE_GROUNDING_SUBSTRATE. It does not alter the Mother Mechanics,
the Fundamental Laws, Amendments 01-06, or any registered mechanical theorem.

## 2. Four distinct grounding objects

The grounding architecture SHALL preserve:

GROUNDING CONTRACT
    !=
TRUST ROOT
    !=
GROUNDING ASSERTION
    !=
GROUNDED MECHANICAL PREMISE.

A GROUNDING CONTRACT is an immutable reusable specification of what an
accepted grounder is permitted to assert and under which exact conditions.

A TRUST ROOT is an explicit external acceptance of one exact contract,
contract version, authority, channel set, and trust scope for an execution.

A GROUNDING ASSERTION is one immutable acquisition-instance claim made under
one exact contract and claimed trust root.

A GROUNDED MECHANICAL PREMISE is one mechanical proposition admitted only
after exact non-generative validation of the assertion against the contract,
trust root, channel, scope, integrity, replay, and applicability constraints.

Contract existence creates no trust root, assertion, or grounded premise.
Trust-root existence creates no assertion or grounded premise. Assertion
existence without exact validation creates no grounded premise.

## 3. Origin separation

Proposition meaning and proposition origin SHALL remain distinct.

The proposition-origin classes are:

ACCESS_REPRESENTATION
GROUNDED_EXTERNAL
DERIVED_M
NATIVE_REPRESENTED.

FALSIFICATION_RESULT is a result class, not a proposition origin.

GROUNDED_EXTERNAL != DERIVED_M.

ACCESS_REPRESENTATION != GROUNDED_EXTERNAL.

A GROUNDED_EXTERNAL premise is accepted under an explicit external grounding
contract. M did not infer it. Grounding SHALL NOT emit DERIVED_M.

## 4. Weak acquisition-trace proposition

This amendment freezes exactly one new proposition type:

REAL_ACQUISITION_TRACE_EXISTS.

Its minimum meaning is:

A mechanically instantiated acquisition trace exists within the exact scope
accepted by a valid grounding assertion under an explicitly trusted grounding
contract.

REAL_ACQUISITION_TRACE_EXISTS is existential and witness-free with respect to
source semantics. An identified trace is a provenance referent, not a source,
source-event, source-difference, causal, or mechanical witness.

Its constructor policy is TRUSTED_GROUNDING_ONLY.

Type registration or contract registration creates zero proposition instances.

REAL_ACQUISITION_TRACE_EXISTS does not imply REAL_DIFFERENCE_EXISTS,
REAL_CONSEQUENCE_EXISTS, source identity, source property, source event,
source difference, calibration truth outside contract scope, source
persistence, source correctness, causal mechanism, or semantic-label truth.

The constructor policy of REAL_DIFFERENCE_EXISTS remains
NO_CONSTRUCTOR_CURRENTLY_AUTHORIZED.

## 5. Grounding contract and trust root

A grounding contract SHALL preserve exact identity, version, semantic
specification, semantic hash, permitted assertion kind, permitted proposition
type, required scope semantics, explicit channel constraints, replay and
current-applicability rules, constructor policy, authority metadata, and the
source-semantics exclusion.

Changing contract semantics creates a new identity, version, or semantic hash.
Historical assertions retain the exact contract identity under which they were
evaluated. Contract semantics SHALL NOT be mutated in place.

A trust root means only that an execution explicitly accepts one contract and
version under an exact scope and channel set.

Trust-root origin is EXTERNALLY_ACCEPTED_NOT_DERIVED_BY_M.

Trust-root registration is an explicit external or project-configuration
operation. A trust root SHALL NOT be inferred from assertion data,
self-signing, signature validity alone, repository presence, contract
existence, an untrusted record, or a human label.

The default trusted-root count is zero.

Trust is scope-bound. Acceptance for one contract, version, channel, execution,
acquisition class, scope, or validity interval does not authorize claims
outside that accepted boundary.

Historical trust-root acceptance is immutable and append-only. Revocation
changes current applicability and does not rewrite historical acceptance.

## 6. Grounding assertion and exact validation

A grounding assertion SHALL preserve one exact assertion identity, contract
identity and version, claimed trust-root identity, acquisition-instance
identity, acquisition-channel identity, trace identity, exact mechanical
scope, immutable provenance, integrity information, replay or freshness state,
historical validity, and current applicability.

Validated assertions are immutable. Correction creates a new assertion.

ValidGroundingAssertion(assertion, contract, trust_root, scope) is a
non-generative exact contract-conformance relation.

Validation MAY inspect exact identities, hashes, signatures or integrity,
contract version, prior trust-root registration, required contract fields,
explicit contract channel relations, exact scope, replay or freshness state,
and current applicability.

Validation SHALL NOT inspect or infer semantic plausibility, source truth,
physical-model fit, probability, confidence, voting, majority, statistical
inference, human labels, source identity, source property, source difference,
or causal structure.

Channel identity alone does not prove acquisition. Payload equality, payload
hash equality across contexts, filename, label, device type, or timestamp
alone does not establish trace identity.

A valid grounding assertion means that the assertion conforms to an externally
accepted grounding contract. It does not mean that M independently discovered
or certified physical truth.

An assertion without a matching accepted trust root, exact contract and
version, permitted channel, exact scope, valid integrity, and current
applicability SHALL create zero grounded premises.

Caller metadata such as "grounded", "real", confidence, or probability SHALL
remain ACCESS_REPRESENTATION and cannot authorize grounding.

## 7. Grounded proposition provenance and kernel admission

A valid assertion MAY construct exactly one
REAL_ACQUISITION_TRACE_EXISTS proposition with origin GROUNDED_EXTERNAL.

Every grounded proposition SHALL retain exact references to its trust root,
contract identity, contract version, contract semantic hash, grounding
assertion, acquisition channel, acquisition trace, exact scope, provenance,
historical validity, current applicability, and validation identity.

The Proof Kernel MAY admit that proposition to exact mechanical-rule premise
matching only when its type is frozen, constructor policy permits trusted
grounding, contract and trust-root identities verify, assertion validation
succeeds, scope is exact, current applicability is true, and grounding
ancestry is intact.

Admission is proof infrastructure. It does not infer source semantics.

For one proof genealogy, a conclusion's grounding-root set is the exact union
of its parent premise grounding-root sets. This union is provenance only and
is not the mechanical Dependency stage. Root-free propositions retain an
empty grounding-root set.

Alternative proof genealogies retain separate root sets and separate current
applicability. One surviving genealogy may remain currently applicable when
another genealogy is revoked. Historical proposition identity remains stable.

## 8. History, replay, revocation, and conflict

HISTORICAL GROUNDING VALIDITY != CURRENT APPLICABILITY.

A replayed historical assertion SHALL NOT masquerade as a new current
acquisition. Replay or freshness state is preserved by the assertion and
evaluated for current applicability.

Revocation of a trust root, contract, channel, or assertion changes current
applicability only. It SHALL NOT delete historical contracts, trust roots,
assertions, propositions, receipts, or proof genealogies.

A genealogy depending on a revoked root becomes currently inapplicable.
Another independent exact genealogy rooted only in currently applicable roots
may remain applicable. No root substitutes for another without an independent
exact proof genealogy.

Exactly incompatible grounded propositions under overlapping scope SHALL both
be preserved with their assertions and trust roots. Grounding chooses no
winner. Amendment 05 conflict and UNRESOLVED semantics remain authoritative.
Root count, assertion count, confidence, voting, or majority determines no
mechanical truth.

## 9. Source-semantics firewall

VALID_GROUNDING_ASSERTION(trace)
    ->
REAL_ACQUISITION_TRACE_EXISTS
    [origin = GROUNDED_EXTERNAL]

DOES NOT imply that any source semantic claim is true.

Grounding a trace SHALL NOT construct source_1, source_event_1,
source_difference_1, cause_1, external_object_1, or any equivalent hidden
source node.

The grounding layer SHALL NOT emit REAL_DIFFERENCE_EXISTS,
REAL_CONSEQUENCE_EXISTS, Dependency, Exchange, Transformation, Propagation,
Consequence, Continuation, REOPEN, or FirstDivergence.

Cryptographic attestation may support authority identity, contract identity,
assertion integrity, endpoint identity, freshness, or non-replay. Attestation
does not independently establish source semantics, calibration truth, source
property, source difference, causal interpretation, or physical truth outside
the accepted contract.

## 10. Default and explicit execution boundaries

Installing this amendment and its grounding infrastructure trusts no root,
creates no grounding assertion, and creates no grounded premise.

Ordinary ungrounded raw access remains UNRESOLVED at
RAW_MECHANICAL_BOOTSTRAP_FRONTIER with zero new DERIVED_M.

One explicit accepted trust root and one exact valid assertion may admit one
REAL_ACQUISITION_TRACE_EXISTS premise. Because the currently registered
theorem requires REAL_DIFFERENCE_EXISTS, that theorem remains dormant and
creates zero REAL_CONSEQUENCE_EXISTS and zero new DERIVED_M.

The resulting frontier is
POST_GROUNDING_MECHANICAL_RECONSTRUCTION_FRONTIER: a first grounded mechanical
premise exists, but no frozen mechanical rule currently derives a further
mechanical proposition from that exact premise type.

This frontier is not REOPEN, FirstDivergence, M failure, source reconstruction,
or authorization to return to Dependency or proceed to FABEST.