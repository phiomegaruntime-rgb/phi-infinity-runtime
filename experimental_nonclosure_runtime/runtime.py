"""Runtime whose ordinary result is local support plus an open frontier."""

from __future__ import annotations

from dataclasses import dataclass

from .model import (
    ContinuationState,
    LocalClosure,
    NonClosureReceipt,
    NonClosureResult,
    NonClosureStatus,
    NonClosureSubject,
    RuleRef,
    SpecificOpening,
    SubjectKind,
)


NON_CLOSURE_RULE = RuleRef("rule:experimental-non-closure-v1")


def _local_closure(
    subject: NonClosureSubject,
    status: NonClosureStatus,
) -> LocalClosure:
    """Create the explanatory half without changing the open frontier."""

    if status is NonClosureStatus.SUPPORTED_LOCAL:
        statement = (
            f"Within support scope {subject.support.local_scope.value}, "
            f"the available evidence locally supports {subject.subject_id.value}; "
            "this explanation does not settle what lies beyond that support."
        )
    elif status is NonClosureStatus.REOPEN:
        statement = (
            f"Within support scope {subject.support.local_scope.value}, "
            f"{subject.subject_id.value} requires local reopening; "
            "the available evidence is not treated as a final explanation."
        )
    else:
        statement = (
            f"Within support scope {subject.support.local_scope.value}, "
            f"the available evidence does not locally resolve {subject.subject_id.value}; "
            "the missing support remains explicit."
        )
    return LocalClosure(
        statement=statement,
        valid_within=subject.support.local_scope,
        evidence=subject.support.evidence,
    )


@dataclass(frozen=True, slots=True)
class NonClosureRule:
    """A rule application is itself subject to the non-closure contract."""

    rule_id: RuleRef = NON_CLOSURE_RULE

    def apply(
        self,
        subject: NonClosureSubject,
        *,
        request_reopen: bool = False,
    ) -> NonClosureResult:
        if type(subject) is not NonClosureSubject:
            raise TypeError("NonClosureRule accepts only NonClosureSubject values.")
        if not subject.support.evidence:
            status = NonClosureStatus.UNRESOLVED
        elif request_reopen:
            status = NonClosureStatus.REOPEN
        else:
            status = NonClosureStatus.SUPPORTED_LOCAL
        local_closure = _local_closure(subject, status)
        opening = SpecificOpening.derive(
            origin=subject.subject_id,
            closure=local_closure,
            continuation_frontier=subject.frontier.continuation,
            dependency_frontier=subject.frontier.next_unknown,
        )
        result_frontier = subject.frontier.__class__(
            consequence=subject.frontier.consequence,
            continuation=subject.frontier.continuation,
            next_unknown=opening.dependency_frontier,
            next_question=subject.frontier.next_question,
            actions=subject.frontier.actions,
        )
        result_subject = NonClosureSubject(
            subject_id=subject.subject_id,
            kind=subject.kind,
            support=subject.support,
            frontier=result_frontier,
        )
        receipt = NonClosureReceipt.issue(
            rule_id=self.rule_id,
            subject=result_subject,
            status=status,
            local_closure=local_closure,
            opening=opening,
        )
        return NonClosureResult(
            status=status,
            subject_id=subject.subject_id,
            subject_kind=subject.kind,
            local_scope=subject.support.local_scope,
            local_closure=local_closure,
            opening=opening,
            consequence_state=ContinuationState.OPEN,
            continuation_state=ContinuationState.OPEN,
            frontier=result_frontier,
            receipt=receipt,
        )


class NonClosureRuntime:
    """Independent experimental runtime; it has no global-close operation."""

    def __init__(self, rule: NonClosureRule | None = None) -> None:
        self._rule = NonClosureRule() if rule is None else rule
        if type(self._rule) is not NonClosureRule:
            raise TypeError("NonClosureRuntime requires a NonClosureRule.")

    @property
    def rule(self) -> NonClosureRule:
        return self._rule

    def evaluate(
        self,
        subject: NonClosureSubject,
        *,
        request_reopen: bool = False,
    ) -> NonClosureResult:
        """Evaluate locally without ever converting finite support into closure."""

        return self._rule.apply(subject, request_reopen=request_reopen)

    def evaluate_runtime(self, subject: NonClosureSubject) -> NonClosureResult:
        """Apply the same rule to a runtime representation recursively."""

        if subject.kind is not SubjectKind.RUNTIME:
            raise ValueError("evaluate_runtime requires a runtime subject.")
        return self.evaluate(subject)

    def evaluate_rule(self, subject: NonClosureSubject) -> NonClosureResult:
        """Apply the same rule to a rule representation recursively."""

        if subject.kind is not SubjectKind.RULE:
            raise ValueError("evaluate_rule requires a rule subject.")
        return self.evaluate(subject)

    def evaluate_test(self, subject: NonClosureSubject) -> NonClosureResult:
        """Apply the same rule to a test representation recursively."""

        if subject.kind is not SubjectKind.TEST:
            raise ValueError("evaluate_test requires a test subject.")
        return self.evaluate(subject)