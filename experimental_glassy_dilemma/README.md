# Glassy Dilemma Experiment

This is a separate, non-authoritative experiment. It is dedicated to testing
one conceptual solution for the local-continuation dilemma.

The first phase freezes the solution before data:

```text
FROZEN BEFORE DATA
```

The frozen source is `FROZEN_SOLUTION.md`. The loader in `authority.py`
verifies both the complete source digest and the exact statement digest.
Mutation is fail-closed.

This phase adds no data, evaluator, scientific theory, formula, threshold, or
new M rule. A future data phase may report only `COMPATIBLE`,
`INCOMPATIBLE`, or `INSUFFICIENT`; it may not change the frozen statement.

Nothing in this directory is an M-authoritative receipt or a modification of
`m_machine`.