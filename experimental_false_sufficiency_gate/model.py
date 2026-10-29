"""Fragment-only result model for the false-sufficiency research gate."""

from __future__ import annotations

from dataclasses import dataclass

from experimental_m_runtime_v2 import FragmentGraph, FragmentRef


KIND_GATE_AUTHORITY = FragmentRef("kind:gate-authority")
KIND_CRITERION = FragmentRef("kind:criterion")
KIND_PERSISTENCE = FragmentRef("kind:persistence")
KIND_COUNTEREXAMPLE = FragmentRef("kind:counterexample")
KIND_SCOPE = FragmentRef("kind:scope")

GATE_AUTHORITY_CLAIM = FragmentRef("fragment:claim:gate-authority")
GATE_GENEALOGY_FRAGMENT = FragmentRef("fragment:genealogy:gate")
GATE_DEPENDENCY_FRAGMENT = FragmentRef("fragment:dependency:gate")
GATE_RESULT_FRAGMENT = FragmentRef("fragment:claim:gate-result")
COUNTEREXAMPLE_SUPPORT_FRAGMENT = FragmentRef(
    "fragment:claim:counterexample-support"
)
FALSE_SUFFICIENCY_FRAGMENT = FragmentRef(
    "fragment:claim:false-sufficiency-general-rule"
)
COUNTEREXAMPLE_MARKER = FragmentRef(
    "fragment:counterexample:representation-mechanics-divergence"
)
LOCAL_SCOPE_FRAGMENT = FragmentRef("fragment:scope:local")
GLOBAL_SCOPE_FRAGMENT = FragmentRef("fragment:scope:global")
PERSISTENCE_FRAGMENT = FragmentRef("fragment:persistence:false-sufficiency")

VERDICT_SUPPORTED_LOCAL = FragmentRef("verdict:SUPPORTED_LOCAL")
VERDICT_REOPEN = FragmentRef("verdict:REOPEN")
VERDICT_ACCESS_INSUFFICIENT = FragmentRef("verdict:ACCESS_INSUFFICIENT")
VERDICT_FALSIFIED = FragmentRef("verdict:FALSIFIED")
VERDICT_UNRESOLVED = FragmentRef("verdict:UNRESOLVED")

REASON_SUPPORTED_LOCAL = FragmentRef("reason:supported-local-scope")
REASON_UNSUPPORTED_FALSE_SUFFICIENCY = FragmentRef(
    "reason:unsupported-false-sufficiency"
)
REASON_ACCESS_INSUFFICIENT = FragmentRef("reason:access-insufficient")
REASON_GENERALITY_FALSIFIED = FragmentRef(
    "reason:structural-counterexample-to-generality"
)
REASON_UNRESOLVED = FragmentRef("reason:gate-unresolved")


@dataclass(frozen=True, slots=True)
class GateResult:
    """Every gate result crossing the experiment boundary is a fragment ref."""

    criterion: FragmentRef
    verdict: FragmentRef
    decision: FragmentRef
    reason: FragmentRef
    error: FragmentRef
    output: FragmentRef
    receipt: FragmentRef
    graph: FragmentGraph