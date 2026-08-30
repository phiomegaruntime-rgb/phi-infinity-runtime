# PHI-INFINITY (Phi-Infinity) Computational Runtime

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22150329.svg)](https://doi.org/10.5281/zenodo.22150329)
[![GitHub License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Deterministic bottom-up relational computing framework for multi-agent governance, invariant substrates, emergent boundary persistence, and anti-hallucination semantic bridging.

**Author:** Massimiliano Brighindi
**Edition:** Integral Blueprint 2026 (v1.2.0)
**Version DOI:** [10.5281/zenodo.22150329](https://doi.org/10.5281/zenodo.22150329)
**Concept DOI:** [10.5281/zenodo.22143113](https://doi.org/10.5281/zenodo.22143113)

---

## Axiomatic Foundation: The 11 Fundamental Laws

The runtime, equations, and translation protocols are rigorous computational implementations of the **11 Fundamental Laws of Fragment Mechanics** (v1.0 — 28/08/2026):

1. **Law of INFINITY:** Reality consists of infinite continuous fragments.
2. **Law of Recursive Fragmentation:** No terminal scale or irreducible static particle.
3. **Law of Dependence & Exchanges:** Persistence is sustained exclusively by field exchanges.
4. **Fragment-Field Law:** Duality of scale; every field is a fragment and vice versa.
5. **Law of Proper Equilibrium:** Homeostasis as dynamic compatibility of flows.
6. **Law of Non-Identity:** Distinct entities have at least one real differential trace.
7. **Law of Local Temporal Structure ($d\tau$):** Time is the local rate of structural transformation.
8. **Law of Universality:** Invariant mechanics underlying all physical/semiotic phenomena.
9. **Law of Consequences:** Every real difference generates propagating transformations.
10. **Law of Transformation:** Strict conservation; state redistribution without magic deletion.
11. **Law of Boundaries ($M_C$):** Boundaries are themselves permeable, active interface fragments.

> *Full axiomatic formulation available in [`docs/THE_11_FUNDAMENTAL_LAWS.md`](docs/THE_11_FUNDAMENTAL_LAWS.md).*

---

## Core Architecture (`src/`)

* **`core.py`:** 6 primitive invariant equations, antisymmetric tanh flows, local represented structural path increment, and stress-induced force inversion $(1 - \beta R_i)$.
* **`membrane.py`:** Emergent boundary persistence metric ($M_C$) evaluating topological cohesion.
* **`gating.py`:** Ex-ante deterministic gating (`FirstDivergence` and `REOPEN`).
* **`translator.py`:** Universal Bidirectional Translation Protocol ($T_{H \to \Phi}$ deconstruction & $T_{\Phi \to H}$ anti-hallucination semantic bridging).
* **`demo.py`:** Standalone diagnostic and multi-metric plotting engine.

---

## Quick Start & Execution

```bash
git clone [https://github.com/](https://github.com/)phiomegaruntime-rgb/phi-infinity-runtime.git
cd phi-infinity-runtime
python main.py
python demo.py
```

---

## Citation & Reference

```bibtex
@software{brighindi2026phi_infinity_v120,
  author       = {Brighindi, Massimiliano},
  title        = {PHI-INFINITY (Phi-Infinity) Computational Runtime: Deterministic Substrate Invariant Engine, 11 Fundamental Laws & Universal Translator},
  year         = {2026},
  version      = {1.2.0},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.22150329},
  url          = {[https://doi.org/](https://doi.org/)10.5281/zenodo.22150329}
}
```

---

## License

(c) 2026 Massimiliano Brighindi. Released under the MIT License.

<!-- PHI-OMNIA-BEGIN -->

## OMNIA: Ambiguity Without Forced Selection

The inverse bridge does not assume that the numerically best
compatible latent state is the real one.

For accessible observation bases \(B_1,\ldots,B_n\):

\[
\mathcal Z_{\mathrm{OMNIA}}
=
\bigcap_i
\mathcal Z(B_i)
\]

Operationally, every candidate genealogy must remain compatible
with every currently accessible basis.

OMNIA does **not** use majority voting or semantic weighting.

The surviving genealogies are then continued through the native
PHI runtime.

If no compatible genealogy is found:

`UNRESOLVED_IN_SEARCH_DOMAIN`

If one observable continuation class remains:

`ONE_CONTINUATION_CLASS_WITHIN_EXPLORED_SEARCH_DOMAIN`

If multiple PHI-distinguishable continuation classes remain:

`UNKNOWN_AMBIGUOUS_UNDER_CURRENT_ACCESS`

Therefore:

\[
\text{compatibility} \neq \text{uniqueness}
\]

and:

\[
|\mathcal Z/\sim_\Phi|>1
\Rightarrow
UNKNOWN
\]

The current implementation supports aligned positional observation
bases. Extension to heterogeneous sources requires a future
observation interface and must not introduce human semantic mappings
into PHI state variables or dynamics.

The numerical search is finite. A single discovered continuation
class means one class **within the explored search domain**, not
proof of global latent uniqueness.

<!-- PHI-OMNIA-END -->

<!-- PHI-BOUNDARY-BEGIN -->

## INFINITY → Field → Fragment

A local computational scope is not treated as the boundary of reality.

PHI-INFINITY therefore distinguishes:

\[
\text{computational boundary}
\neq
\text{real boundary}
\]

A containing field does not need to be copied entirely into a local
fragment. It transmits only the consequences that actually reach the
fragment during the current transformation.

Conceptually:

\[
\Omega
\rightarrow
F_1
\rightarrow
F_2
\rightarrow
\dots
\rightarrow
F_n
\]

Each level may transmit boundary consequences to the next.

Multiple containing shells compose additively.

If the relevant exterior contribution remains unresolved, the runtime
must not silently replace it with zero.

Therefore:

\[
\text{not accessible}
\neq
0
\]

For dynamic continuation, unresolved exterior effects cause explicit
abstention.

For membrane evaluation, an unresolved exterior cannot justify
persistence. A dissolution conclusion may still be guaranteed when
the currently known exterior already forces the upper bound of
\(M_C\) to be at or below 1.

The native equations in `src/core.py` and `src/membrane.py` remain
unchanged.

<!-- PHI-BOUNDARY-END -->


<!-- PHI-RELEVANCE-BEGIN -->

## Consequence Preservation

PHI-INFINITY does not equate small numerical magnitude with
irrelevance.

The operational rule is:

\[
\Delta \neq 0
\Rightarrow
\text{preserve the consequence}
\]

Every represented accessible consequence is retained and composed
with the others before continuation is evaluated.

A numerical tolerance may describe the limits of current
computation, but it must never become a statement that a real
difference has no consequence.

Therefore:

\[
\text{below current numerical resolution}
\neq
\text{irrelevant}
\]

and:

\[
\text{unresolved}
\neq
0
\]

If a real exterior source is present but its effect collapses to zero
in the current numerical representation, the runtime explicitly
reports:

`PRESERVE_BELOW_CURRENT_NUMERICAL_RESOLUTION`

rather than discarding the source.

If the consequence itself remains unresolved:

`REQUIRE_MORE_ACCESS`

The controller also prevents per-source threshold pruning. Many small
consequences are composed before the resulting continuation is
evaluated.

This avoids turning a computational threshold into a version of the
sorites ("heap") paradox.

The continuous PHI quantity may change gradually even when a later
human-facing classification crosses a named boundary.

The native PHI mechanics remain unchanged.

<!-- PHI-RELEVANCE-END -->

<!-- PHI-TIME-STRUCTURE-BEGIN -->

## Flow, Mechanical Progress, and Personal Time

PHI-INFINITY now separates the mechanical trajectory from the numerical
coordinate used to traverse it.

The runtime uses

\[
d\lambda_{\mathcal M}
\]

as a neutral `mechanical_progress` coordinate.

It is not universal time and it is not proper time.

The previous quantity

\[
\|\Delta S\|
\]

is now treated only as a represented structural path increment.

Structural, geometric and residual transformations are exposed separately.

A zero represented transformation is never promoted to the ontological claim
that reality is static.

Coherent reparameterization must preserve the represented trajectory.

Personal-time relations remain emergent:

\[
d\tau_i
=
\rho_i\,d\lambda_{\mathcal M},
\qquad
q_{ij}
=
\frac{\rho_i}{\rho_j},
\]

but no universal formula for \(\rho_i\) has yet been introduced.

The temporal model therefore requires coherence between local flows rather
than global synchronization.

See:

`docs/PERSONAL_TIME_AND_MECHANICAL_PROGRESS.md`

<!-- PHI-TIME-STRUCTURE-END -->

<!-- PHI:README_TEMPORAL_CLOSURE:START -->
## Temporal branch — CURRENT structural closure

PHI-INFINITY currently separates numerical progression from temporal
structure:

\[
\boxed{
\lambda_{\mathcal M}\neq\tau
}
\]

The primary temporal object is relational:

\[
\boxed{
\mathcal C_{ij}
\rightarrow
\Sigma_{ij}
\rightarrow
q_{ij}
}
\]

A scalar representation

\[
q_{ij}=\rho_i/\rho_j
\]

is used only when the temporal relation network is integrable.

Therefore \(\rho_i\) is not treated as a universal primitive.

Current status:

- temporal architecture: **provisionally closed**;
- universal quantitative law
  \(\mathcal C_{ij}\rightarrow\Sigma_{ij}\): **open**;
- runtime mechanics: unchanged.

See:

`docs/TEMPORAL_BRANCH_CLOSURE_CURRENT.md`
<!-- PHI:README_TEMPORAL_CLOSURE:END -->

<!-- PHI:README_UNIVERSAL_MECHANICS:START -->
## Universal Mother Mechanics — CURRENT falsification target

PHI-INFINITY's central universality hypothesis is:

\[
\boxed{
\forall F\subset\Omega:
\mathcal M_F=\mathcal M
}
\]

Fragments and configurations need not be identical.

The invariant candidate is the mechanics by which differences,
dependencies, exchanges, transformations and consequences produce
continuation.

The hypothesis is now frozen before adversarial testing.

First required gate:

**Recursive Scale Identity**

Canonical contract:

`docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md`
<!-- PHI:README_UNIVERSAL_MECHANICS:END -->

<!-- PHI:VALIDATION_LEDGER:START -->
## Cumulative validation and falsification record

PHI-INFINITY preserves validation work cumulatively.

Permanent invariants are encoded in `tests/`.

Reproducible non-runtime validation gates are stored in `validation/gates/`.

Historical confirmed outputs, falsification sequence and interpretation
limits are recorded under:

`docs/validation/`

Current ledger:

`docs/validation/VALIDATION_LEDGER_CURRENT.md`

Rule:

\[
\boxed{
\text{NEW PHI CHANGE}
\Rightarrow
\text{MUST SURVIVE ALL PREVIOUS PERMANENT INVARIANTS}
}
\]

A passing test does not prove universal PHI validity. It establishes only
that the tested falsification route did not destroy the corresponding
property.
<!-- PHI:VALIDATION_LEDGER:END -->
