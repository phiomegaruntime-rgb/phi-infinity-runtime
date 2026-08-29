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
7. **Law of Proper Time ($d\tau$):** Time is the local rate of structural transformation.
8. **Law of Universality:** Invariant mechanics underlying all physical/semiotic phenomena.
9. **Law of Consequences:** Every real difference generates propagating transformations.
10. **Law of Transformation:** Strict conservation; state redistribution without magic deletion.
11. **Law of Boundaries ($M_C$):** Boundaries are themselves permeable, active interface fragments.

> *Full axiomatic formulation available in [`docs/THE_11_FUNDAMENTAL_LAWS.md`](docs/THE_11_FUNDAMENTAL_LAWS.md).*

---

## Core Architecture (`src/`)

* **`core.py`:** 6 primitive invariant equations, antisymmetric tanh flows, local proper time ($d\tau$), and stress-induced force inversion $(1 - \beta R_i)$.
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
