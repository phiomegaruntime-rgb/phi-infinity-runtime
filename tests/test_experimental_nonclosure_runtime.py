from __future__ import annotations

from dataclasses import replace

import pytest

from experimental_nonclosure_runtime import (
    ContinuationState,
    FrontierAction,
    FragmentRef,
    FrontierRef,
    LocalClosure,
    NonClosureResult,
    NonClosureRule,
    NonClosureRuntime,
    NonClosureStatus,
    NonClosureSubject,
    OpenFrontier,
    SubjectKind,
    SupportEnvelope,
    SupportRef,
)


def make_subject(
    kind: SubjectKind = SubjectKind.FRAGMENT,
    *,
    evidence: tuple[str, ...] = ("evidence:local",),
) -> NonClosureSubject:
    return NonClosureSubject(
        subject_id=FragmentRef(f"fragment:{kind.value.lower()}"),
        kind=kind,
        support=SupportEnvelope(
            local_scope=SupportRef("scope:local"),
            evidence=tuple(SupportRef(item) for item in evidence),
        ),
        frontier=OpenFrontier(
            consequence=FrontierRef("frontier:consequences"),
            continuation=FrontierRef("frontier:continuation"),
            next_unknown=FrontierRef("frontier:next-unknown"),
            next_question="What support must be followed, reopened, or verified next?",
            actions=(
                FrontierAction.FOLLOW,
                FrontierAction.REOPEN,
                FrontierAction.VERIFY,
            ),
        ),
    )


def test_supported_result_is_local_and_always_open() -> None:
    result = NonClosureRuntime().evaluate(make_subject())

    assert result.status is NonClosureStatus.SUPPORTED_LOCAL
    assert result.is_local
    assert result.is_reopenable
    assert result.local_closure.is_local
    assert not result.local_closure.is_global
    assert result.local_closure.valid_within == result.local_scope
    assert result.local_closure.statement
    assert result.consequence_state is ContinuationState.OPEN
    assert result.continuation_state is ContinuationState.OPEN
    assert result.frontier.consequence.value == "frontier:consequences"
    assert result.frontier.continuation.value == "frontier:continuation"
    assert result.frontier.next_unknown.value == "frontier:next-unknown"
    assert result.frontier.next_question
    assert result.frontier.actions == (
        FrontierAction.FOLLOW,
        FrontierAction.REOPEN,
        FrontierAction.VERIFY,
    )


def test_finite_fragment_endpoint_does_not_end_consequences_or_continuation() -> None:
    result = NonClosureRuntime().evaluate(make_subject())

    assert result.subject_id.value == "fragment:fragment"
    assert result.consequence_state is ContinuationState.OPEN
    assert result.continuation_state is ContinuationState.OPEN
    assert result.frontier is not None
    assert result.local_closure is not None


def test_reopen_is_normal_result_state_not_exception_path() -> None:
    result = NonClosureRuntime().evaluate(
        make_subject(),
        request_reopen=True,
    )

    assert result.status is NonClosureStatus.REOPEN
    assert result.is_reopenable
    assert result.receipt.status is NonClosureStatus.REOPEN
    assert result.receipt.local_closure == result.local_closure


def test_missing_support_is_unresolved_but_still_keeps_frontier_open() -> None:
    result = NonClosureRuntime().evaluate(make_subject(evidence=()))

    assert result.status is NonClosureStatus.UNRESOLVED
    assert result.frontier.consequence
    assert result.frontier.continuation
    assert result.consequence_state is ContinuationState.OPEN
    assert result.continuation_state is ContinuationState.OPEN
    assert result.local_closure.statement


def test_no_result_can_be_constructed_with_a_nonclosure_status() -> None:
    assert {status.value for status in NonClosureStatus} == {
        "SUPPORTED_LOCAL",
        "REOPEN",
        "UNRESOLVED",
    }
    assert not hasattr(NonClosureStatus, "FINAL_PASS")


def test_result_rejects_raw_status_and_cannot_be_relabelled_as_final() -> None:
    result = NonClosureRuntime().evaluate(make_subject())

    with pytest.raises(TypeError):
        replace(result, status="FINAL_PASS")


def test_local_closure_cannot_exist_without_its_open_counterpart() -> None:
    result = NonClosureRuntime().evaluate(make_subject())

    with pytest.raises(TypeError):
        replace(result, local_closure=None)
    with pytest.raises(TypeError):
        replace(result, frontier=None)


def test_local_closure_is_explanatory_not_reality_closure() -> None:
    result = NonClosureRuntime().evaluate(make_subject())

    assert result.local_closure.is_local is True
    assert result.local_closure.is_global is False
    assert result.frontier.is_open is True
    assert result.frontier.next_unknown != result.frontier.consequence
    assert result.frontier.next_unknown != result.frontier.continuation
    assert set(result.frontier.actions) == {
        FrontierAction.FOLLOW,
        FrontierAction.REOPEN,
        FrontierAction.VERIFY,
    }


def test_receipt_is_derived_from_the_local_subject_and_status() -> None:
    subject = make_subject()
    result = NonClosureRuntime().evaluate(subject)
    repeated = NonClosureRuntime().evaluate(subject)

    assert result.receipt.receipt_id == repeated.receipt.receipt_id
    assert result.receipt.subject_id == subject.subject_id
    assert result.receipt.local_scope == subject.support.local_scope
    assert result.receipt.consequence_frontier == subject.frontier.consequence
    assert result.receipt.continuation_frontier == subject.frontier.continuation
    assert result.receipt.local_closure == result.local_closure
    assert result.receipt.next_unknown == subject.frontier.next_unknown
    assert result.receipt.next_question == subject.frontier.next_question
    assert result.receipt.frontier_actions == subject.frontier.actions


def test_same_nonclosure_rule_applies_recursively_to_runtime_rule_and_test() -> None:
    runtime = NonClosureRuntime()

    runtime_result = runtime.evaluate_runtime(make_subject(SubjectKind.RUNTIME))
    rule_result = runtime.evaluate_rule(make_subject(SubjectKind.RULE))
    test_result = runtime.evaluate_test(make_subject(SubjectKind.TEST))

    assert {
        runtime_result.status,
        rule_result.status,
        test_result.status,
    } == {NonClosureStatus.SUPPORTED_LOCAL}
    assert all(result.is_reopenable for result in (
        runtime_result,
        rule_result,
        test_result,
    ))
    assert all(
        result.consequence_state is ContinuationState.OPEN
        and result.continuation_state is ContinuationState.OPEN
        for result in (runtime_result, rule_result, test_result)
    )


def test_recursive_entrypoints_reject_the_wrong_subject_kind() -> None:
    runtime = NonClosureRuntime()

    with pytest.raises(ValueError):
        runtime.evaluate_runtime(make_subject(SubjectKind.FRAGMENT))
    with pytest.raises(ValueError):
        runtime.evaluate_rule(make_subject(SubjectKind.FRAGMENT))
    with pytest.raises(ValueError):
        runtime.evaluate_test(make_subject(SubjectKind.FRAGMENT))


def test_open_frontier_requires_distinct_consequence_and_continuation_dimensions() -> None:
    with pytest.raises(ValueError):
        OpenFrontier(
            consequence=FrontierRef("frontier:same"),
            continuation=FrontierRef("frontier:same"),
            next_unknown=FrontierRef("frontier:unknown"),
            next_question="Which unknown remains?",
            actions=(FrontierAction.FOLLOW,),
        )


def test_rule_is_an_explicit_local_rule_and_does_not_close_the_subject() -> None:
    subject = make_subject()
    result = NonClosureRule().apply(subject)

    assert result.status is NonClosureStatus.SUPPORTED_LOCAL
    assert result.receipt.rule_id.value == "rule:experimental-non-closure-v1"
    assert result.is_reopenable