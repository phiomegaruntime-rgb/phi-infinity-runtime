# Accessible relations: bounded implementation step

The user's clarification is that M does not prescribe a universal fixed amount
or object of exchange. The particular transformation depends on the actual
network of necessities, availabilities and internal/external relations. All of
these, including the relations, are fragments. A missing available description
must not be silently interpreted as zero or as an ontological absence.

## Audit of b0b7193

`src/core.py` has seven spatially uniform coefficients with default values:
sigma=1.2, alpha=0.04, beta=0.25, lmbda=0.01, gamma=0.3, mu=0.05, eta=0.01.
It also uses numerical floors 0.01 and denominator regularizers 1e-8 and 1e-3.
The attested service overrides all seven defaults with explicitly signed values;
they can change between requests, but are not derived from a dependency network.
Its signed `mechanical_progress` is likewise supplied rather than reconstructed.
Thus 'fixed' needs qualification: defaults and formula-level numerical choices
are fixed in this model; attested parameter values need not remain constant.
The current position/state coupling does vary with state. The existing engine
is not literally a constant exchange table, but it is a chosen quantitative
model, not a demonstrated universal reconstruction from M.

## Added component

`independent_runtime/relations.py` evaluates explicitly supplied exact arithmetic
relations over a finite accessible snapshot. All identifiers refer to fragments;
literal/expression fields are wire syntax, not privileged ontological kinds.
It records consumed fragments, missing supports and the full snapshot digest.
Recursive unavailable inputs, cycles without a supplied resolution, invalid
division and representation depth limits cannot acquire invented values.
Known zero remains distinct from missing input. Fractions preserve represented
small nonzero quantities instead of rounding them away in this component.

Tests use a caller-supplied minimum rule solely as a transparent test fixture.
This is NOT a newly derived exchange law, a cell/tumour model or a rule of M.
The component does not infer the correct arithmetic relation from observations.
Its successful status explicitly says NOT_M_DERIVED.

## Boundary and next work

This component is read-only and is not connected to numeric state mutation,
signature verification or the existing attested service. Snapshot hashes alone
do not establish reality, freshness, completeness or authority. Integration must
bind actual observations, all consumed relations and their revisions to the
effect transaction; a stale relation must invalidate the candidate. No existing
M-native refusal is changed and no frozen engine equation or threshold changed.

The next conceptual question is how a case supplies or establishes its specific
quantitative relations and sufficient access. This implementation does not
claim to inspect an infinite network or determine inaccessible information.

## Recursive investigation, 2026-10-30

An absent represented input now produces an AccessRequest identifying the
fragment, an inspection target, the observation to acquire, and its dependency
path back to the requested transformation. This describes incomplete access,
never an absent relation in reality. Explicit access records can name an
assembly/contact/internal fragment and a case-specific observation. Without
such information the resolver asks to establish that fragment's value or
internal relations; it does not invent an instrument or physical decomposition.

`investigate` passes these requests to a caller-provided acquisition function,
validates each returned observation/enrichment, and resolves the new snapshot.
An observed fragment can reveal further internal dependencies: the next access
request follows them recursively. Shared dependencies retain their separate
paths. After each enrichment, requests are regenerated from the new snapshot.
An unchanged response stops rather than consuming the same observation forever.

Termination distinguishes a result within accessible representation, no further
available access, and exhaustion of an explicitly supplied round budget. Cycles
without an established solution ask for examination of the cyclic relations;
known zero denominators ask for examination of the division's applicability,
not remeasurement until an arbitrary nonzero denominator appears.

The supplied acquisition function is responsible for actual observation and
provenance. This component has no sensors, does not disassemble physical objects,
does not certify that returned observations are true, and never changes the
numerical engine. Tests use explicitly labelled arithmetic fixtures, not claims
of measured watch/cell behaviour. Effect-time integration remains separate.
