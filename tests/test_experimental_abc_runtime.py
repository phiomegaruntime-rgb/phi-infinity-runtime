from __future__ import annotations

import json

from experimental_abc_runtime import (
    ABCEchoRuntime,
    DEFAULT_STIMULUS,
    MExperimentalPlan,
    WorkerRequest,
)


def echo_agent(request: WorkerRequest) -> dict[str, object]:
    payload = json.loads(request.snapshot_wire)
    return {
        "role": request.role,
        "cycle": request.cycle,
        "stimulus": payload["stimulus"],
        "additional_input_count": len(payload["additional_inputs"]),
        "snapshot_digest": request.snapshot_digest,
        "peer_output_present": hasattr(request, "output_a_wire")
        or hasattr(request, "output_b_wire"),
    }


def structured_comparator(request) -> dict[str, list[object]]:
    a = json.loads(request.output_a_wire)
    b = json.loads(request.output_b_wire)
    return {
        "differences": [
            {"field": "role", "a": a["role"], "b": b["role"]}
        ],
        "convergences": [
            {"field": "stimulus", "value": a["stimulus"] == b["stimulus"]},
            {"field": "snapshot_digest", "value": a["snapshot_digest"] == b["snapshot_digest"]},
        ],
        "omissions": [],
        "unknowns": [],
        "assumptions": [],
        "contradictions": [],
    }


def invalid_comparator(request) -> dict[str, list[object]]:
    return {"differences": []}


def test_two_cycles_freeze_genealogy_and_reinjection() -> None:
    plan = MExperimentalPlan.freeze(
        "An input is a represented fragment; A, B, and C are isolated "
        "continuations whose outputs remain provenance-bearing."
    )
    result = ABCEchoRuntime(timeout_seconds=10).run_two_cycles(
        context={"channel": "test", "version": 1},
        agent_a=echo_agent,
        agent_b=echo_agent,
        comparator_c=structured_comparator,
        m_plan=plan,
    )

    assert result.is_success
    assert DEFAULT_STIMULUS == "Cosa senti?"
    assert len(result.cycles) == 2
    first, second = result.cycles
    assert first.input_snapshot.digest != second.input_snapshot.digest
    assert first.input_snapshot.payload["additional_inputs"] == []
    assert second.input_snapshot.payload["additional_inputs"][0]["kind"] == (
        "prior_cycle_c_output"
    )
    assert second.input_snapshot.payload["additional_inputs"][0]["digest"] == (
        first.output_c.digest
    )
    assert result.measurement is not None
    assert result.measurement.condition == "real_echo"
    assert result.measurement.reinjection_applied
    assert result.measurement.input_snapshot_changed
    assert result.measurement.conceptual_solution_digest == (
        plan.conceptual_solution_digest
    )
    assert result.measurement.freeze_digest == plan.freeze_digest
    assert result.measurement.exact_path == plan.exact_path
    assert len(result.receipts) == 9
    assert all(receipt.parent_receipt_ids or receipt.cycle == 1 for receipt in result.receipts)


def test_b_cannot_receive_a_and_invalid_c_stops_before_cycle_two() -> None:
    plan = MExperimentalPlan.freeze("Freeze before numerical formalization.")
    result = ABCEchoRuntime(timeout_seconds=10).run_two_cycles(
        context={},
        agent_a=echo_agent,
        agent_b=echo_agent,
        comparator_c=invalid_comparator,
        m_plan=plan,
    )

    assert result.decision == "BLOCK"
    assert len(result.cycles) == 0
    assert result.measurement is None
    assert result.failure_reason is not None
    assert "C output field" in result.failure_reason