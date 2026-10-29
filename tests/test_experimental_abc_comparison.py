from __future__ import annotations

import json

import pytest

from experimental_abc_runtime import (
    ABCEchoRuntime,
    CONDITION_BROKEN_ECHO,
    CONDITION_FALSE_ECHO,
    CONDITION_NULL,
    CONDITION_REAL_ECHO,
    DEFAULT_STIMULUS,
    MExperimentalPlan,
    WorkerRequest,
)
from experimental_abc_runtime.model import ComparatorRequest, digest_value


def echo_observer(request: WorkerRequest) -> dict[str, object]:
    payload = json.loads(request.snapshot_wire)
    prior = [
        item
        for item in payload["additional_inputs"]
        if item.get("kind") == "prior_cycle_c_output"
    ]
    prior_item = prior[-1] if prior else None
    return {
        "role": request.role,
        "stimulus": payload["stimulus"],
        "prior_c_digest": None if prior_item is None else prior_item["digest"],
        "prior_relation_valid": (
            None
            if prior_item is None
            else digest_value(prior_item["payload"]) == prior_item["digest"]
        ),
        "peer_output_present": hasattr(request, "output_a_wire")
        or hasattr(request, "output_b_wire"),
    }


def integrating_comparator(
    request: ComparatorRequest,
) -> dict[str, list[object] | object]:
    a = json.loads(request.output_a_wire)
    b = json.loads(request.output_b_wire)
    return {
        "differences": [{"field": "role", "a": a["role"], "b": b["role"]}],
        "convergences": [
            {"field": "stimulus", "same": a["stimulus"] == b["stimulus"]},
            {
                "field": "peer_visibility",
                "same": not a["peer_output_present"]
                and not b["peer_output_present"],
            },
        ],
        "omissions": [],
        "unknowns": [],
        "assumptions": [],
        "contradictions": [],
        "request_fields": sorted(request.__dataclass_fields__),
        "input_digest": request.snapshot_digest,
        "a_digest": request.output_a_digest,
        "b_digest": request.output_b_digest,
    }


def _plan() -> MExperimentalPlan:
    return MExperimentalPlan.freeze(
        "Represent the stimulus and each isolated continuation as immutable "
        "provenance-bearing fragments; measure only the frozen cycle outputs."
    )


def _run(condition: str):
    return ABCEchoRuntime(timeout_seconds=10).run_two_cycles(
        context={"experiment": "internal_echo", "version": 1},
        agent_a=echo_observer,
        agent_b=echo_observer,
        comparator_c=integrating_comparator,
        m_plan=_plan(),
        condition=condition,
    )


@pytest.mark.parametrize(
    "condition",
    (
        CONDITION_REAL_ECHO,
        CONDITION_NULL,
        CONDITION_FALSE_ECHO,
        CONDITION_BROKEN_ECHO,
    ),
)
def test_default_stimulus_four_condition_comparison(condition: str) -> None:
    result = _run(condition)
    assert result.cycles
    assert result.cycles[0].input_snapshot.payload["stimulus"] == DEFAULT_STIMULUS
    assert result.cycles[0].output_a.payload["peer_output_present"] is False
    assert result.cycles[0].output_b.payload["peer_output_present"] is False
    if condition == CONDITION_BROKEN_ECHO:
        assert result.decision == "BLOCK"
        assert result.measurement is None
        assert "payload digest does not match" in (result.failure_reason or "")
        return
    assert result.is_success
    assert result.measurement is not None
    assert all(
        field in result.cycles[0].output_c.payload["request_fields"]
        for field in (
            "snapshot_wire",
            "snapshot_digest",
            "output_a_wire",
            "output_a_digest",
            "output_b_wire",
            "output_b_digest",
        )
    )
    assert len(result.receipts) == 9
    if condition == CONDITION_REAL_ECHO:
        assert result.measurement.reinjection_source == "REINJECTED_FROM_PRIOR_CYCLE"
        assert result.measurement.injected_matches_cycle_1_c is True
        assert result.measurement.injected_relation_valid is True
        assert result.measurement.a_output_changed is True
        assert result.measurement.b_output_changed is True
    elif condition == CONDITION_NULL:
        assert result.measurement.reinjection_source == "NONE"
        assert result.measurement.reinjection_applied is False
        assert result.measurement.injected_digest is None
        assert result.measurement.a_output_changed is False
        assert result.measurement.b_output_changed is False
    elif condition == CONDITION_FALSE_ECHO:
        assert result.measurement.reinjection_source == "FOREIGN_CONTROL_PAYLOAD"
        assert result.measurement.injected_matches_cycle_1_c is False
        assert result.measurement.injected_surface_shape_matches is True
        assert result.measurement.injected_relation_valid is True
        assert result.measurement.a_output_changed is True
        assert result.measurement.b_output_changed is True