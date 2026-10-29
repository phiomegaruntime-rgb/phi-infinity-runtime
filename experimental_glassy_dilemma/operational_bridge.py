"""Frozen, M-only operational bridge for the glassy-dilemma experiment.

The bridge is deliberately conservative.  It records what can be carried from
M CURRENT and the conceptual freeze without adding a physical measurement rule.
It does not import or modify the authoritative M runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .bridge_authority import BridgeFreezeManifest, load_bridge_freeze


DefinitionStatus = Literal["DERIVED", "UNRESOLVED"]


@dataclass(frozen=True, slots=True)
class OperationalDefinition:
    """One frozen definition or an explicit unresolved frontier."""

    name: str
    status: DefinitionStatus
    operational_rule: str
    source_basis: tuple[str, ...]
    unresolved_reason: str | None = None


@dataclass(frozen=True, slots=True)
class OperationalBridge:
    """The complete bridge contract admitted before any future dataset."""

    manifest: BridgeFreezeManifest
    definitions: tuple[OperationalDefinition, ...]
    unresolved_definitions: tuple[str, ...]

    @property
    def can_emit_data_verdict(self) -> bool:
        """Whether a pre-dataset rule permits COMPATIBLE or INCOMPATIBLE."""

        return not self.unresolved_definitions

    def definition(self, name: str) -> OperationalDefinition:
        for definition in self.definitions:
            if definition.name == name:
                return definition
        raise KeyError(name)


OPERATIONAL_DEFINITIONS: tuple[OperationalDefinition, ...] = (
    OperationalDefinition(
        name="DIFFERENCE",
        status="DERIVED",
        operational_rule=(
            "At representation level only, two supplied values in the same "
            "declared scope differ when their canonical JSON values are not "
            "exactly equal. This is not a claim of physical difference."
        ),
        source_basis=(
            "M CURRENT section 3: DIFFERENCES",
            "M CURRENT section 10: preserve represented consequence",
        ),
    ),
    OperationalDefinition(
        name="PERSISTENCE",
        status="UNRESOLVED",
        operational_rule=(
            "M states that persistence is continuity through transformation, "
            "not absolute identity, but supplies no finite observation rule."
        ),
        source_basis=(
            "M CURRENT section 2: persistence is continuity through transformation",
        ),
        unresolved_reason=(
            "No pre-dataset rule specifies the ordered continuation relation, "
            "observation horizon, tolerance, or transformation witness."
        ),
    ),
    OperationalDefinition(
        name="LOCAL_SUFFICIENCY",
        status="UNRESOLVED",
        operational_rule=(
            "The freeze refers to local sufficiency for autonomous continuation "
            "but does not define a decidable representation-level predicate."
        ),
        source_basis=(
            "FROZEN_SOLUTION statement: local sufficiency to complete continuation",
            "M CURRENT section 9: unresolved access is not fabricated closure",
        ),
        unresolved_reason=(
            "Defining autonomy, completion, and the required local field would "
            "add a human closure criterion."
        ),
    ),
    OperationalDefinition(
        name="CONTINUATION",
        status="UNRESOLVED",
        operational_rule=(
            "M supplies continuation or reorganization as the grammar endpoint, "
            "but not a dataset-to-next-configuration transition rule."
        ),
        source_basis=(
            "M CURRENT section 3: continuation / reorganization",
            "FROZEN_SOLUTION statement: complete its own continuation",
        ),
        unresolved_reason=(
            "A transition function, step relation, temporal interpretation, or "
            "prediction horizon would be a new construct."
        ),
    ),
    OperationalDefinition(
        name="REOPEN",
        status="DERIVED",
        operational_rule=(
            "When local closure is insufficient, do not conclude absolute "
            "stoppage; reopen only the supplied unresolved dimensions: field, "
            "dependencies, genealogy, scale, and access."
        ),
        source_basis=(
            "FROZEN_SOLUTION statement: REOPEN field/dependencies/genealogy/scale/access",
            "M CURRENT section 9: unresolved exterior is not zero",
        ),
    ),
)


def load_operational_bridge(repository_root: str) -> OperationalBridge:
    """Verify and load the bridge without reading any dataset."""

    manifest = load_bridge_freeze(repository_root)
    unresolved = tuple(
        definition.name
        for definition in OPERATIONAL_DEFINITIONS
        if definition.status == "UNRESOLVED"
    )
    return OperationalBridge(
        manifest=manifest,
        definitions=OPERATIONAL_DEFINITIONS,
        unresolved_definitions=unresolved,
    )