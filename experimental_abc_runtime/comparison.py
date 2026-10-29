"""Content-sensitive comparison for the non-authoritative A/B/C experiment."""

from __future__ import annotations

from collections.abc import Mapping
import json

from .model import (
    ABCTestResult,
    ContentSensitiveCase,
    ContentSensitiveComparison,
    canonical_json,
)


CONTENT_FIELDS = (
    "stimulus",
    "prior_c_digest",
    "prior_c_content",
    "prior_relation_valid",
    "peer_output_present",
)
STRUCTURED_C_FIELDS = (
    "differences",
    "convergences",
    "omissions",
    "unknowns",
    "assumptions",
    "contradictions",
)


def _projection(wire: str) -> dict[str, object]:
    payload = json.loads(wire)
    if not isinstance(payload, dict):
        raise ValueError("A/B output must be an object for content comparison.")
    return {key: payload[key] for key in CONTENT_FIELDS if key in payload}


def _changed_fields(first: dict[str, object], second: dict[str, object]) -> tuple[str, ...]:
    return tuple(
        key
        for key in CONTENT_FIELDS
        if first.get(key) != second.get(key)
    )


def _edit_distance(left: str, right: str) -> int:
    """Deterministic Levenshtein distance over canonical JSON projections."""

    previous = list(range(len(right) + 1))
    for index, left_char in enumerate(left, start=1):
        current = [index]
        for right_index, right_char in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def _structural_profile(wire: str) -> dict[str, tuple[str, ...]]:
    payload = json.loads(wire)
    if not isinstance(payload, dict):
        raise ValueError("C output must be an object for content comparison.")
    profile: dict[str, tuple[str, ...]] = {}
    for field in STRUCTURED_C_FIELDS:
        value = payload.get(field, [])
        if not isinstance(value, list):
            raise ValueError(f"C field {field!r} is not a list.")
        profile[field] = tuple(canonical_json(item) for item in value)
    return profile


def _structural_delta(first_wire: str, second_wire: str) -> int:
    first = _structural_profile(first_wire)
    second = _structural_profile(second_wire)
    return sum(
        len(set(first[field]) ^ set(second[field]))
        for field in STRUCTURED_C_FIELDS
    )


def _require_allow(results: Mapping[str, ABCTestResult], name: str) -> ABCTestResult:
    result = results.get(name)
    if result is None or not result.is_success:
        raise ValueError(f"Content comparison requires successful condition {name!r}.")
    return result


def compare_content_sensitive(
    results: Mapping[str, ABCTestResult],
) -> ContentSensitiveComparison:
    """Apply one frozen criterion to real echo, null, and foreign controls."""

    required = ("real_echo", "null_no_reinjection", "false_echo_foreign_surface")
    selected = {name: _require_allow(results, name) for name in required}
    stimulus_values = {
        result.cycles[0].input_snapshot.payload.get("stimulus")
        for result in selected.values()
    }
    if len(stimulus_values) != 1:
        raise ValueError("Content comparison requires one identical stimulus.")
    plans = {
        (
            result.m_plan.conceptual_solution_digest,
            result.m_plan.freeze_digest,
            result.m_plan.exact_path,
        )
        for result in selected.values()
    }
    if len(plans) != 1:
        raise ValueError("Content comparison requires one frozen M plan.")
    for result in selected.values():
        if any(
            payload.get("peer_output_present") is not False
            for cycle in result.cycles
            for payload in (cycle.output_a.payload, cycle.output_b.payload)
        ):
            raise ValueError("Content comparison detected A/B peer visibility.")

    cases: list[ContentSensitiveCase] = []
    for name, result in selected.items():
        first, second = result.cycles
        a_first = _projection(first.output_a.wire)
        a_second = _projection(second.output_a.wire)
        b_first = _projection(first.output_b.wire)
        b_second = _projection(second.output_b.wire)
        cases.append(
            ContentSensitiveCase(
                condition=name,
                a_changed_fields=_changed_fields(a_first, a_second),
                b_changed_fields=_changed_fields(b_first, b_second),
                a_delta_distance=_edit_distance(
                    canonical_json(a_first), canonical_json(a_second)
                ),
                b_delta_distance=_edit_distance(
                    canonical_json(b_first), canonical_json(b_second)
                ),
                c_structural_delta=_structural_delta(
                    first.output_c.wire, second.output_c.wire
                ),
            )
        )

    real = selected["real_echo"]
    foreign = selected["false_echo_foreign_surface"]
    real_a2 = _projection(real.cycles[1].output_a.wire)
    foreign_a2 = _projection(foreign.cycles[1].output_a.wire)
    real_b2 = _projection(real.cycles[1].output_b.wire)
    foreign_b2 = _projection(foreign.cycles[1].output_b.wire)
    real_case = next(case for case in cases if case.condition == "real_echo")
    foreign_case = next(
        case for case in cases if case.condition == "false_echo_foreign_surface"
    )
    real_measurement = real.measurement
    foreign_measurement = foreign.measurement
    if real_measurement is None or foreign_measurement is None:
        raise ValueError("Content comparison requires both measurements.")
    distinguishable = all(
        (
            real_measurement.injected_matches_cycle_1_c,
            not foreign_measurement.injected_matches_cycle_1_c,
            real_measurement.injected_surface_shape_matches,
            foreign_measurement.injected_surface_shape_matches,
            _edit_distance(
                canonical_json(real_a2), canonical_json(foreign_a2)
            )
            > 0,
            _edit_distance(
                canonical_json(real_b2), canonical_json(foreign_b2)
            )
            > 0,
        )
    )
    return ContentSensitiveComparison(
        cases=tuple(cases),
        real_vs_foreign_a2_distance=_edit_distance(
            canonical_json(real_a2), canonical_json(foreign_a2)
        ),
        real_vs_foreign_b2_distance=_edit_distance(
            canonical_json(real_b2), canonical_json(foreign_b2)
        ),
        real_vs_foreign_a_delta_difference=abs(
            real_case.a_delta_distance - foreign_case.a_delta_distance
        ),
        real_vs_foreign_b_delta_difference=abs(
            real_case.b_delta_distance - foreign_case.b_delta_distance
        ),
        distinguishable=distinguishable,
        criterion=(
            "same stimulus and frozen M plan",
            "same A/B content projection fields",
            "Levenshtein distance over canonical projected JSON",
            "C structural symmetric difference over available fields",
            "real C1 provenance match plus nonzero real-vs-foreign A2/B2 distance",
        ),
    )