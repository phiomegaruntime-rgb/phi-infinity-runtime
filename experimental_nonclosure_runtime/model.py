"""Typed local results whose non-closure is their normal semantic state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json


class _Ref:
    """Shared validation for opaque, locally scoped references."""

    value: str

    def _validate(self, label: str) -> None:
        if type(self.value) is not str or not self.value:
            raise TypeError(f"{label} requires a non-empty value.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class FragmentRef(_Ref):
    value: str

    def __post_init__(self) -> None:
        self._validate("FragmentRef")


@dataclass(frozen=True, slots=True)
class SupportRef(_Ref):
    value: str

    def __post_init__(self) -> None:
        self._validate("SupportRef")


@dataclass(frozen=True, slots=True)
class FrontierRef(_Ref):
    value: str

    def __post_init__(self) -> None:
        self._validate("FrontierRef")


@dataclass(frozen=True, slots=True)
class RuleRef(_Ref):
    value: str

    def __post_init__(self) -> None:
        self._validate("RuleRef")


class SubjectKind(str, Enum):
    FRAGMENT = "FRAGMENT"
    RUNTIME = "RUNTIME"
    RULE = "RULE"
    TEST = "TEST"


class NonClosureStatus(str, Enum):
    SUPPORTED_LOCAL = "SUPPORTED_LOCAL"
    REOPEN = "REOPEN"
    UNRESOLVED = "UNRESOLVED"


class ContinuationState(str, Enum):
    OPEN = "OPEN"


class FrontierAction(str, Enum):
    """The only permitted operational readings of an open frontier."""

    FOLLOW = "FOLLOW"
    REOPEN = "REOPEN"
    VERIFY = "VERIFY"


@dataclass(frozen=True, slots=True)
class SupportEnvelope:
    """The complete support known for one local evaluation."""

    local_scope: SupportRef
    evidence: tuple[SupportRef, ...]

    def __post_init__(self) -> None:
        if type(self.local_scope) is not SupportRef:
            raise TypeError("SupportEnvelope.local_scope must be a SupportRef.")
        if type(self.evidence) is not tuple:
            raise TypeError("SupportEnvelope.evidence must be a tuple.")
        if any(type(item) is not SupportRef for item in self.evidence):
            raise TypeError("SupportEnvelope.evidence must contain SupportRef values.")
        if len(self.evidence) != len(set(self.evidence)):
            raise ValueError("SupportEnvelope.evidence must be identity-unique.")


@dataclass(frozen=True, slots=True)
class LocalClosure:
    """A human-readable explanation bounded strictly by one local support."""

    statement: str
    valid_within: SupportRef
    evidence: tuple[SupportRef, ...]

    def __post_init__(self) -> None:
        if type(self.statement) is not str or not self.statement.strip():
            raise TypeError("LocalClosure.statement requires human-readable text.")
        if type(self.valid_within) is not SupportRef:
            raise TypeError("LocalClosure.valid_within must be a SupportRef.")
        if type(self.evidence) is not tuple:
            raise TypeError("LocalClosure.evidence must be a tuple.")
        if any(type(item) is not SupportRef for item in self.evidence):
            raise TypeError("LocalClosure.evidence must contain SupportRef values.")
        if len(self.evidence) != len(set(self.evidence)):
            raise ValueError("LocalClosure.evidence must be identity-unique.")

    @property
    def is_local(self) -> bool:
        return True

    @property
    def is_global(self) -> bool:
        """A local explanation has no authority over the represented reality."""

        return False

    @property
    def digest(self) -> str:
        payload = {
            "statement": self.statement,
            "valid_within": self.valid_within.value,
            "evidence": tuple(item.value for item in self.evidence),
        }
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True, slots=True)
class RelationRef(_Ref):
    value: str

    def __post_init__(self) -> None:
        self._validate("RelationRef")


@dataclass(frozen=True, slots=True)
class DiscriminationRef(_Ref):
    value: str

    def __post_init__(self) -> None:
        self._validate("DiscriminationRef")


@dataclass(frozen=True, slots=True)
class OpenFrontier:
    """The explicit next unknown and its permitted operational follow-ups."""

    consequence: FrontierRef
    continuation: FrontierRef
    next_unknown: FrontierRef
    next_question: str
    actions: tuple[FrontierAction, ...]

    def __post_init__(self) -> None:
        if type(self.consequence) is not FrontierRef:
            raise TypeError("OpenFrontier.consequence must be a FrontierRef.")
        if type(self.continuation) is not FrontierRef:
            raise TypeError("OpenFrontier.continuation must be a FrontierRef.")
        if self.consequence == self.continuation:
            raise ValueError("Consequence and continuation frontiers must differ.")
        if type(self.next_unknown) is not FrontierRef:
            raise TypeError("OpenFrontier.next_unknown must be a FrontierRef.")
        if self.next_unknown in {self.consequence, self.continuation}:
            raise ValueError(
                "OpenFrontier.next_unknown must identify a distinct frontier."
            )
        if type(self.next_question) is not str or not self.next_question.strip():
            raise TypeError(
                "OpenFrontier.next_question requires human-readable text."
            )
        if type(self.actions) is not tuple or not self.actions:
            raise TypeError("OpenFrontier.actions must be a non-empty tuple.")
        if any(not isinstance(item, FrontierAction) for item in self.actions):
            raise TypeError(
                "OpenFrontier.actions must contain FrontierAction values."
            )
        if len(self.actions) != len(set(self.actions)):
            raise ValueError("OpenFrontier.actions must be identity-unique.")

    @property
    def is_open(self) -> bool:
        return True


@dataclass(frozen=True, slots=True)
class SpecificOpening:
    """The first unsupported continuation derived from one local closure."""

    origin: FragmentRef
    unsupported_relation: RelationRef
    missing_discrimination: DiscriminationRef
    dependency_frontier: FrontierRef
    question: str
    closure_digest: str

    def __post_init__(self) -> None:
        if type(self.origin) is not FragmentRef:
            raise TypeError("SpecificOpening.origin must be a FragmentRef.")
        if type(self.unsupported_relation) is not RelationRef:
            raise TypeError(
                "SpecificOpening.unsupported_relation must be a RelationRef."
            )
        if type(self.missing_discrimination) is not DiscriminationRef:
            raise TypeError(
                "SpecificOpening.missing_discrimination must be a DiscriminationRef."
            )
        if type(self.dependency_frontier) is not FrontierRef:
            raise TypeError(
                "SpecificOpening.dependency_frontier must be a FrontierRef."
            )
        if type(self.question) is not str or not self.question.strip():
            raise TypeError("SpecificOpening.question requires concrete text.")
        if type(self.closure_digest) is not str or len(self.closure_digest) != 64:
            raise TypeError("SpecificOpening.closure_digest must be a SHA256 digest.")
        try:
            int(self.closure_digest, 16)
        except ValueError as exc:
            raise TypeError(
                "SpecificOpening.closure_digest must be a SHA256 digest."
            ) from exc
        required_tokens = (
            self.origin.value,
            self.unsupported_relation.value,
            self.missing_discrimination.value,
            self.dependency_frontier.value,
        )
        if any(token not in self.question for token in required_tokens):
            raise ValueError(
                "SpecificOpening.question must name its origin, unsupported "
                "relation, missing discrimination, and dependency frontier."
            )

    @classmethod
    def derive(
        cls,
        *,
        origin: FragmentRef,
        closure: LocalClosure,
        continuation_frontier: FrontierRef,
        dependency_frontier: FrontierRef,
    ) -> "SpecificOpening":
        """Derive a non-generic first continuation from the local closure."""

        if type(origin) is not FragmentRef:
            raise TypeError("SpecificOpening origin derivation requires a FragmentRef.")
        if type(closure) is not LocalClosure:
            raise TypeError(
                "SpecificOpening derivation requires a LocalClosure."
            )
        if type(continuation_frontier) is not FrontierRef:
            raise TypeError(
                "SpecificOpening continuation derivation requires a FrontierRef."
            )
        if type(dependency_frontier) is not FrontierRef:
            raise TypeError(
                "SpecificOpening dependency derivation requires a FrontierRef."
            )
        unsupported_relation = RelationRef(
            f"relation:unsupported:{origin.value}:{continuation_frontier.value}"
        )
        missing_discrimination = DiscriminationRef(
            f"discrimination:missing:{origin.value}:{closure.digest}"
        )
        question = (
            f"Which supported evidence from origin {origin.value} can establish "
            f"{unsupported_relation.value} at dependency frontier "
            f"{dependency_frontier.value} and provide missing discrimination "
            f"{missing_discrimination.value}?"
        )
        return cls(
            origin=origin,
            unsupported_relation=unsupported_relation,
            missing_discrimination=missing_discrimination,
            dependency_frontier=dependency_frontier,
            question=question,
            closure_digest=closure.digest,
        )

    @property
    def is_specific(self) -> bool:
        return True


@dataclass(frozen=True, slots=True)
class NonClosureSubject:
    """A finite subject; the same contract is used for runtime, rule, and test."""

    subject_id: FragmentRef
    kind: SubjectKind
    support: SupportEnvelope
    frontier: OpenFrontier

    def __post_init__(self) -> None:
        if type(self.subject_id) is not FragmentRef:
            raise TypeError("NonClosureSubject.subject_id must be a FragmentRef.")
        if not isinstance(self.kind, SubjectKind):
            raise TypeError("NonClosureSubject.kind must be a SubjectKind.")
        if type(self.support) is not SupportEnvelope:
            raise TypeError("NonClosureSubject.support must be a SupportEnvelope.")
        if type(self.frontier) is not OpenFrontier:
            raise TypeError("NonClosureSubject.frontier must be an OpenFrontier.")


def _receipt_id(
    *,
    rule_id: RuleRef,
    subject: NonClosureSubject,
    status: NonClosureStatus,
    local_closure: LocalClosure,
    opening: SpecificOpening,
) -> str:
    payload = {
        "rule_id": rule_id.value,
        "subject_id": subject.subject_id.value,
        "subject_kind": subject.kind.value,
        "local_scope": subject.support.local_scope.value,
        "evidence": tuple(item.value for item in subject.support.evidence),
        "closure_statement": local_closure.statement,
        "closure_scope": local_closure.valid_within.value,
        "closure_evidence": tuple(item.value for item in local_closure.evidence),
        "opening_origin": opening.origin.value,
        "opening_relation": opening.unsupported_relation.value,
        "opening_discrimination": opening.missing_discrimination.value,
        "opening_dependency_frontier": opening.dependency_frontier.value,
        "opening_question": opening.question,
        "opening_closure_digest": opening.closure_digest,
        "consequence_frontier": subject.frontier.consequence.value,
        "continuation_frontier": subject.frontier.continuation.value,
        "next_unknown": subject.frontier.next_unknown.value,
        "next_question": subject.frontier.next_question,
        "frontier_actions": tuple(item.value for item in subject.frontier.actions),
        "status": status.value,
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True, slots=True)
class NonClosureReceipt:
    """An immutable receipt carrying both the local closure and open frontier."""

    receipt_id: str
    rule_id: RuleRef
    subject_id: FragmentRef
    status: NonClosureStatus
    local_scope: SupportRef
    local_closure: LocalClosure
    opening: SpecificOpening
    consequence_frontier: FrontierRef
    continuation_frontier: FrontierRef
    next_unknown: FrontierRef
    next_question: str
    frontier_actions: tuple[FrontierAction, ...]

    def __post_init__(self) -> None:
        if type(self.receipt_id) is not str or not self.receipt_id:
            raise TypeError("NonClosureReceipt.receipt_id is required.")
        if type(self.rule_id) is not RuleRef:
            raise TypeError("NonClosureReceipt.rule_id must be a RuleRef.")
        if type(self.subject_id) is not FragmentRef:
            raise TypeError("NonClosureReceipt.subject_id must be a FragmentRef.")
        if not isinstance(self.status, NonClosureStatus):
            raise TypeError("NonClosureReceipt.status must be a NonClosureStatus.")
        if type(self.local_scope) is not SupportRef:
            raise TypeError("NonClosureReceipt.local_scope must be a SupportRef.")
        if type(self.local_closure) is not LocalClosure:
            raise TypeError(
                "NonClosureReceipt.local_closure must be a LocalClosure."
            )
        if self.local_closure.valid_within != self.local_scope:
            raise ValueError("Receipt closure scope does not match receipt scope.")
        if type(self.opening) is not SpecificOpening:
            raise TypeError("NonClosureReceipt.opening must be a SpecificOpening.")
        expected_opening = SpecificOpening.derive(
            origin=self.subject_id,
            closure=self.local_closure,
            continuation_frontier=self.continuation_frontier,
            dependency_frontier=self.next_unknown,
        )
        if self.opening != expected_opening:
            raise ValueError(
                "Receipt opening is not the specific continuation derived from "
                "the local closure."
            )
        if type(self.consequence_frontier) is not FrontierRef:
            raise TypeError(
                "NonClosureReceipt.consequence_frontier must be a FrontierRef."
            )
        if type(self.continuation_frontier) is not FrontierRef:
            raise TypeError(
                "NonClosureReceipt.continuation_frontier must be a FrontierRef."
            )
        if type(self.next_unknown) is not FrontierRef:
            raise TypeError("NonClosureReceipt.next_unknown must be a FrontierRef.")
        if type(self.next_question) is not str or not self.next_question.strip():
            raise TypeError(
                "NonClosureReceipt.next_question requires human-readable text."
            )
        if type(self.frontier_actions) is not tuple or not self.frontier_actions:
            raise TypeError(
                "NonClosureReceipt.frontier_actions must be a non-empty tuple."
            )
        if any(
            not isinstance(item, FrontierAction) for item in self.frontier_actions
        ):
            raise TypeError(
                "NonClosureReceipt.frontier_actions must contain FrontierAction values."
            )

    @classmethod
    def issue(
        cls,
        *,
        rule_id: RuleRef,
        subject: NonClosureSubject,
        status: NonClosureStatus,
        local_closure: LocalClosure,
        opening: SpecificOpening,
    ) -> "NonClosureReceipt":
        return cls(
            receipt_id=_receipt_id(
                rule_id=rule_id,
                subject=subject,
                status=status,
                local_closure=local_closure,
                opening=opening,
            ),
            rule_id=rule_id,
            subject_id=subject.subject_id,
            status=status,
            local_scope=subject.support.local_scope,
            local_closure=local_closure,
            opening=opening,
            consequence_frontier=subject.frontier.consequence,
            continuation_frontier=subject.frontier.continuation,
            next_unknown=subject.frontier.next_unknown,
            next_question=subject.frontier.next_question,
            frontier_actions=subject.frontier.actions,
        )


@dataclass(frozen=True, slots=True)
class NonClosureResult:
    """A result is always a local explanation paired with an open frontier."""

    status: NonClosureStatus
    subject_id: FragmentRef
    subject_kind: SubjectKind
    local_scope: SupportRef
    local_closure: LocalClosure
    opening: SpecificOpening
    consequence_state: ContinuationState
    continuation_state: ContinuationState
    frontier: OpenFrontier
    receipt: NonClosureReceipt

    def __post_init__(self) -> None:
        if not isinstance(self.status, NonClosureStatus):
            raise TypeError("NonClosureResult.status must be a NonClosureStatus.")
        if type(self.subject_id) is not FragmentRef:
            raise TypeError("NonClosureResult.subject_id must be a FragmentRef.")
        if not isinstance(self.subject_kind, SubjectKind):
            raise TypeError("NonClosureResult.subject_kind must be a SubjectKind.")
        if type(self.local_scope) is not SupportRef:
            raise TypeError("NonClosureResult.local_scope must be a SupportRef.")
        if type(self.frontier) is not OpenFrontier:
            raise TypeError("NonClosureResult.frontier must be an OpenFrontier.")
        if type(self.local_closure) is not LocalClosure:
            raise TypeError("NonClosureResult.local_closure must be a LocalClosure.")
        if self.local_closure.valid_within != self.local_scope:
            raise ValueError("Result closure scope does not match result scope.")
        if type(self.opening) is not SpecificOpening:
            raise TypeError("NonClosureResult.opening must be a SpecificOpening.")
        expected_opening = SpecificOpening.derive(
            origin=self.subject_id,
            closure=self.local_closure,
            continuation_frontier=self.frontier.continuation,
            dependency_frontier=self.frontier.next_unknown,
        )
        if self.opening != expected_opening:
            raise ValueError(
                "Result opening is not the specific continuation derived from "
                "the local closure."
            )
        if self.consequence_state is not ContinuationState.OPEN:
            raise ValueError("Consequences must remain open.")
        if self.continuation_state is not ContinuationState.OPEN:
            raise ValueError("Mechanical continuation must remain open.")
        if type(self.receipt) is not NonClosureReceipt:
            raise TypeError("NonClosureResult.receipt must be a NonClosureReceipt.")
        if self.receipt.subject_id != self.subject_id:
            raise ValueError("Receipt subject does not match result subject.")
        if self.receipt.status is not self.status:
            raise ValueError("Receipt status does not match result status.")
        if self.receipt.local_scope != self.local_scope:
            raise ValueError("Receipt scope does not match result scope.")
        if self.receipt.local_closure != self.local_closure:
            raise ValueError("Receipt closure does not match result closure.")
        if self.receipt.opening != self.opening:
            raise ValueError("Receipt opening does not match result opening.")
        if self.receipt.consequence_frontier != self.frontier.consequence:
            raise ValueError("Receipt consequence frontier does not match result.")
        if self.receipt.continuation_frontier != self.frontier.continuation:
            raise ValueError("Receipt continuation frontier does not match result.")
        if self.receipt.next_unknown != self.frontier.next_unknown:
            raise ValueError("Receipt next unknown does not match result frontier.")
        if self.receipt.next_question != self.frontier.next_question:
            raise ValueError("Receipt frontier question does not match result.")
        if self.receipt.frontier_actions != self.frontier.actions:
            raise ValueError("Receipt frontier actions do not match result.")

    @property
    def is_local(self) -> bool:
        return True

    @property
    def is_reopenable(self) -> bool:
        return True