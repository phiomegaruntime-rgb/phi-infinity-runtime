"""Immutable data model for the non-authoritative A/B/C echo experiment.

This module deliberately does not import or extend the authoritative M runtime.
It records an experiment about recursion, causal dependence, and operational
self-reference; it cannot establish consciousness or subjective experience.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, TypeAlias


JSONValue: TypeAlias = (
    None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]
)


def canonical_json(value: Any) -> str:
    """Serialize JSON-compatible data deterministically and fail closed."""

    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("A/B/C payloads must be finite JSON-compatible data.") from exc


def digest_wire(wire: str) -> str:
    return hashlib.sha256(wire.encode("utf-8")).hexdigest()


def digest_value(value: Any) -> str:
    return digest_wire(canonical_json(value))


M_ONLY_EXACT_PATH = (
    "ACCESSIBLE_CONFIGURATION",
    "DIFFERENCE",
    "DEPENDENCY",
    "EXCHANGE",
    "TRANSFORMATION",
    "PROPAGATION",
    "CONSEQUENCE",
    "READJUSTMENT",
    "CONTINUATION",
)


@dataclass(frozen=True, slots=True)
class MExperimentalPlan:
    """Frozen M protocol metadata; numerical results cannot mutate it."""

    conceptual_solution: str
    conceptual_solution_digest: str
    freeze_digest: str
    exact_path: tuple[str, ...] = M_ONLY_EXACT_PATH
    numerical_fields: tuple[str, ...] = (
        "reinjection_effect",
        "ab_variation",
        "unresolved_residuals",
        "convergence_stability",
    )

    @classmethod
    def freeze(cls, conceptual_solution: str) -> "MExperimentalPlan":
        if not isinstance(conceptual_solution, str) or not conceptual_solution.strip():
            raise ValueError("The M conceptual solution must be non-empty.")
        solution_digest = digest_value(
            {"conceptual_solution": conceptual_solution}
        )
        freeze_digest = digest_value(
            {
                "conceptual_solution_digest": solution_digest,
                "exact_path": M_ONLY_EXACT_PATH,
            }
        )
        return cls(
            conceptual_solution=conceptual_solution,
            conceptual_solution_digest=solution_digest,
            freeze_digest=freeze_digest,
        )


@dataclass(frozen=True, slots=True)
class InputSnapshot:
    """An immutable wire snapshot. Workers receive only ``wire``."""

    cycle: int
    wire: str
    digest: str
    parent_cycle_id: str | None = None

    @classmethod
    def create(
        cls,
        *,
        stimulus: JSONValue,
        context: JSONValue,
        cycle: int,
        additional_inputs: tuple[JSONValue, ...] = (),
        parent_cycle_id: str | None = None,
    ) -> "InputSnapshot":
        if cycle < 1:
            raise ValueError("Cycle numbers start at one.")
        payload = {
            "stimulus": stimulus,
            "context": context,
            "additional_inputs": list(additional_inputs),
            "cycle": cycle,
            "parent_cycle_id": parent_cycle_id,
        }
        wire = canonical_json(payload)
        return cls(
            cycle=cycle,
            wire=wire,
            digest=digest_wire(wire),
            parent_cycle_id=parent_cycle_id,
        )

    @property
    def payload(self) -> dict[str, JSONValue]:
        """Return a fresh decoded copy; the stored snapshot remains unchanged."""

        value = json.loads(self.wire)
        if not isinstance(value, dict):
            raise ValueError("Input snapshot wire is not an object.")
        return value

    @property
    def stimulus(self) -> JSONValue:
        return self.payload["stimulus"]

    @property
    def context(self) -> JSONValue:
        return self.payload["context"]

    @property
    def additional_inputs(self) -> tuple[JSONValue, ...]:
        return tuple(self.payload["additional_inputs"])


@dataclass(frozen=True, slots=True)
class WorkerRequest:
    """The complete payload visible to exactly one A or B process."""

    role: str
    cycle: int
    snapshot_wire: str
    snapshot_digest: str
    parent_cycle_id: str | None


@dataclass(frozen=True, slots=True)
class ComparatorRequest:
    """The complete payload visible to C, and only to C."""

    cycle: int
    snapshot_wire: str
    snapshot_digest: str
    output_a_wire: str
    output_a_digest: str
    output_b_wire: str
    output_b_digest: str


@dataclass(frozen=True, slots=True)
class FrozenArtifact:
    """A separately frozen input, A output, B output, or C output."""

    name: str
    cycle: int
    wire: str
    digest: str
    provenance: tuple[str, ...]
    receipt_id: str

    def __post_init__(self) -> None:
        if digest_wire(self.wire) != self.digest:
            raise ValueError(f"Digest mismatch for frozen artifact {self.name!r}.")
        if not self.provenance:
            raise ValueError(f"Provenance is required for {self.name!r}.")

    @property
    def payload(self) -> JSONValue:
        return json.loads(self.wire)


COMPARISON_FIELDS = (
    "differences",
    "convergences",
    "omissions",
    "unknowns",
    "assumptions",
    "contradictions",
)


def validate_comparison_wire(wire: str) -> dict[str, JSONValue]:
    value = json.loads(wire)
    if not isinstance(value, dict):
        raise ValueError("C output must be a JSON object.")
    for field_name in COMPARISON_FIELDS:
        field_value = value.get(field_name)
        if not isinstance(field_value, list):
            raise ValueError(
                f"C output field {field_name!r} must be a JSON list."
            )
    return value


@dataclass(frozen=True, slots=True)
class CycleRecord:
    cycle_id: str
    cycle: int
    input_snapshot: FrozenArtifact
    output_a: FrozenArtifact
    output_b: FrozenArtifact
    output_c: FrozenArtifact
    receipts: tuple[Any, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class VariationMeasurement:
    """Formalized after both cycles; it never changes the frozen M plan."""

    condition: str
    reinjection_source: str
    reinjection_applied: bool
    input_snapshot_changed: bool
    injected_digest: str | None
    injected_matches_cycle_1_c: bool
    injected_surface_shape_matches: bool | None
    injected_relation_valid: bool | None
    a_output_changed: bool
    b_output_changed: bool
    a_output_delta: int
    b_output_delta: int
    unresolved_cycle_1: int
    unresolved_cycle_2: int
    unresolved_delta: int
    convergence_overlap: float
    convergence_stable: bool
    conceptual_solution_digest: str
    freeze_digest: str
    exact_path: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ABCTestResult:
    decision: str
    condition: str
    m_plan: MExperimentalPlan
    cycles: tuple[CycleRecord, ...]
    measurement: VariationMeasurement | None
    receipts: tuple[Any, ...]
    failure_reason: str | None = None

    @property
    def is_success(self) -> bool:
        return self.decision == "ALLOW" and len(self.cycles) == 2


@dataclass(frozen=True, slots=True)
class ContentSensitiveCase:
    condition: str
    a_changed_fields: tuple[str, ...]
    b_changed_fields: tuple[str, ...]
    a_delta_distance: int
    b_delta_distance: int
    c_structural_delta: int


@dataclass(frozen=True, slots=True)
class ContentSensitiveComparison:
    """Same content criterion applied to real, null, and foreign controls."""

    cases: tuple[ContentSensitiveCase, ...]
    real_vs_foreign_a2_distance: int
    real_vs_foreign_b2_distance: int
    real_vs_foreign_a_delta_difference: int
    real_vs_foreign_b_delta_difference: int
    distinguishable: bool
    criterion: tuple[str, ...]