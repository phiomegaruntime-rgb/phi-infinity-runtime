from __future__ import annotations

import json

from experimental_abc_runtime import (
    ABCEchoRuntime,
    CONDITION_FALSE_ECHO,
    CONDITION_NULL,
    CONDITION_REAL_ECHO,
    DEFAULT_STIMULUS,
    MExperimentalPlan,
    WorkerRequest,
    compare_content_sensitive,
)
from experimental_abc_runtime.model import ComparatorRequest, digest_value


def content_sensitive_agent(request: WorkerRequest) -> dict[str, object]:
    payload = json.loads(request.snapshot_wire)
    prior = [
        item
        for item in payload["additional_inputs"]
        if item.get("kind") == "prior_cycle_c_output"
    ]
    item = prior[-1] if prior else None
    return {
        "role": request.role,
        "stimulus": payload["stimulus"],
        "prior_c_digest": None if item is None else item["digest"],
        "prior_c_content": None if item is None else item["payload"],
        "prior_relation_valid": (
            None
            if item is None
            else digest_value(item["payload"]) == item["digest"]
        ),
        "peer_output_present": hasattr(request, "output_a_wire")
        or hasattr(request, "output_b_wire"),
    }


def content_comparator(request: ComparatorRequest) -> dict[str, object]:
    a = json.loads(request.output_a_wire)
    b = json.loads(request.output_b_wire)
    return {
        "differences": [{"field": "role", "a": a["role"], "b": b["role"]}],
        "convergences": [
            {"field": "stimulus", "same": a["stimulus"] == b["stimulus"]},
        ],
        "omissions": [],
        "unknowns": [],
        "assumptions": [],
        "contradictions": [],
        "input_digest": request.snapshot_digest,
        "a_digest": request.output_a_digest,
        "b_digest": request.output_b_digest,
    }


def test_content_sensitive_effect_uses_one_criterion_for_three_conditions() -> None:
    plan = MExperimentalPlan.freeze(
        "Freeze the relational input and compare only provenance-bearing "
        "continuation content."
    )
    runtime = ABCEchoRuntime(timeout_seconds=10)
    results = {
        condition: runtime.run_two_cycles(
            context={"experiment": "content_sensitive", "version": 1},
            agent_a=content_sensitive_agent,
            agent_b=content_sensitive_agent,
            comparator_c=content_comparator,
            m_plan=plan,
            condition=condition,
        )
        for condition in (
            CONDITION_REAL_ECHO,
            CONDITION_NULL,
            CONDITION_FALSE_ECHO,
        )
    }
    comparison = compare_content_sensitive(results)
    assert all(
        result.cycles[0].input_snapshot.payload["stimulus"] == DEFAULT_STIMULUS
        for result in results.values()
    )
    assert comparison.distinguishable
    assert comparison.real_vs_foreign_a2_distance > 0
    assert comparison.real_vs_foreign_b2_distance > 0
    assert comparison.real_vs_foreign_a_delta_difference >= 0
    assert comparison.real_vs_foreign_b_delta_difference >= 0
    assert all(
        "prior_c_content" in case.a_changed_fields
        and "prior_c_content" in case.b_changed_fields
        for case in comparison.cases
        if case.condition == CONDITION_REAL_ECHO
        or case.condition == CONDITION_FALSE_ECHO
    )