# Experimental A/B/C Echo Runtime

This is a separate, non-authoritative experiment. It does not modify or extend
the PHI-INFINITY/M authoritative runtime.

The protocol is:

```text
M conceptual solution -> freeze -> exact path
input snapshot -> isolated A
               -> isolated B
input + frozen A + frozen B -> isolated C
frozen C -> explicit additional input in cycle 2
cycle 1 + cycle 2 -> numerical variation measurement
```

A and B receive the same serialized snapshot and no peer output. C receives
only that snapshot and the separately frozen A and B outputs. Every artifact
and receipt has a digest, provenance, and append-only parent genealogy.

The numerical measurement is intentionally downstream of the frozen
conceptual plan. It cannot mutate that plan.

The default stimulus is `Cosa senti?`. The result can test operational
recursion, causal dependence on a previous output, and self-reference in the
protocol. It is not an automatic test or proof of consciousness, sentience, or
subjective experience.

The process boundary uses Python `spawn`. This isolates A and B's in-memory
payloads, but it is not a general OS sandbox: callbacks must not communicate
through external files, networks, or other side channels.