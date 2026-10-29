"""A non-generative prerequisite scheduler for receipt-bearing M rules."""

from dataclasses import dataclass
from typing import Any, Callable, Literal

from .receipts import DerivationReceipt
from .registry import OperationResult


SchedulerStatus = Literal[
    "CONTINUATION",
    "UNRESOLVED",
    "REOPEN",
    "FIRST_DIVERGENCE",
    "BLOCKED_EXTERNAL",
]


RuleHandler = Callable[
    [tuple[DerivationReceipt, ...], Any],
    OperationResult,
]


@dataclass(frozen=True, slots=True)
class MRule:
    rule_id: str
    operation_name: str
    required_operations: tuple[str, ...]
    handler: RuleHandler


@dataclass(frozen=True, slots=True)
class SchedulerResult:
    status: SchedulerStatus
    values: tuple[tuple[str, Any], ...]
    receipts: tuple[DerivationReceipt, ...]
    frontier: str | None = None

    def value_map(self) -> dict[str, Any]:
        return dict(self.values)


class MOnlyScheduler:
    """Execute all currently eligible rules; never rank or choose candidates."""

    def run(
        self,
        *,
        initial_receipts: tuple[DerivationReceipt, ...],
        rules: tuple[MRule, ...],
        context: Any,
    ) -> SchedulerResult:
        receipts = list(initial_receipts)
        values: list[tuple[str, Any]] = []
        completed_operations = {
            receipt.operation_name for receipt in receipts
        }
        remaining = list(rules)

        while remaining:
            eligible = [
                rule
                for rule in remaining
                if set(rule.required_operations).issubset(
                    completed_operations
                )
            ]
            if not eligible:
                return SchedulerResult(
                    status="UNRESOLVED",
                    values=tuple(values),
                    receipts=tuple(receipts),
                    frontier="scheduler prerequisite frontier",
                )

            for rule in eligible:
                result = rule.handler(tuple(receipts), context)
                receipts.append(result.receipt)
                completed_operations.add(result.operation_name)
                remaining.remove(rule)
                if result.value is not None:
                    values.append((result.operation_name, result.value))
                if result.receipt.status != "DERIVED_M":
                    status = result.receipt.status
                    if status == "REOPEN":
                        terminal: SchedulerStatus = "REOPEN"
                    elif status == "UNRESOLVED":
                        terminal = "UNRESOLVED"
                    else:
                        terminal = "BLOCKED_EXTERNAL"
                    return SchedulerResult(
                        status=terminal,
                        values=tuple(values),
                        receipts=tuple(receipts),
                        frontier=result.operation_name,
                    )

        return SchedulerResult(
            status="CONTINUATION",
            values=tuple(values),
            receipts=tuple(receipts),
        )