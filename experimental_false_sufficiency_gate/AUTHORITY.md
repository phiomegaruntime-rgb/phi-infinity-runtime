# FALSE SUFFICIENCY GENERALITY RESEARCH GATE

**Status:** FROZEN RESEARCH HYPOTHESIS AND FALSIFIER

This experiment is separate from `experimental_m_runtime_v2`. It does not
modify CURRENT, the v2 authority, the v2 semantic formula, or any v2 hash.

## 1. Frozen hypothesis

A persistent divergence between representation and accessible mechanics
requires at least one closure that propagates beyond the genealogy and
dependencies actually supported by the accessible fragment graph.

The hypothesis is not a universal theorem. It is a research claim restricted
to the structural domain represented by this gate.

## 2. Frozen falsifier

The hypothesis is falsified if a represented case has all of the following:

1. every required closure is supported locally;
2. every accessible dependency is represented;
3. genealogy and persistence are represented;
4. no conclusion propagates beyond its supported scope; and
5. representation still diverges systematically from the accessible mechanics.

Such a case must produce the explicit fragment verdict `FALSIFIED`. It must not
be silently classified as a locally supported closure.

## 3. Structural test boundary

The test domain uses fragment structure rather than domain labels as semantic
explanations. A claim without genealogy or dependency support must return
`REOPEN`. A closed graph with insufficient access must return
`ACCESS_INSUFFICIENT`. A supported local closure may remain valid within its
scope. The anti-false-sufficiency rule is itself represented as a claim with
dependencies and persistence; unsupported continuation of that claim reopens.

No result from this gate establishes universality outside the represented
structural domain.