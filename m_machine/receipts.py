"""Immutable derivation receipts used to gate mechanically generative work."""

from dataclasses import dataclass
import hashlib
import json
from typing import Literal


ReceiptStatus = Literal[
    "DERIVED_M",
    "GROUNDED_EXTERNAL",
    "ACCESS_INTEGRITY",
    "ACCESS_DISCRIMINABILITY",
    "EXECUTION_CONTROL",
    "FALSIFICATION_RESULT",
    "UNRESOLVED",
    "REOPEN",
    "BLOCKED_EXTERNAL",
]

_VALID_STATUSES = frozenset(
    {
        "DERIVED_M",
        "GROUNDED_EXTERNAL",
        "ACCESS_INTEGRITY",
        "ACCESS_DISCRIMINABILITY",
        "EXECUTION_CONTROL",
        "FALSIFICATION_RESULT",
        "UNRESOLVED",
        "REOPEN",
        "BLOCKED_EXTERNAL",
    }
)


@dataclass(frozen=True, slots=True)
class DerivationReceipt:
    """A complete, immutable record for one generative operation."""

    receipt_id: str
    operation_name: str
    authoritative_source_file: str
    authoritative_clause: str
    input_receipt_ids: tuple[str, ...]
    accessible_evidence: tuple[str, ...]
    operation_performed: str
    resulting_difference_or_consequence: str
    status: ReceiptStatus
    implementation_source: str = ""
    clause_id: str = ""

    def __post_init__(self) -> None:
        if self.status not in _VALID_STATUSES:
            raise ValueError(f"Unsupported receipt status: {self.status}")
        if not self.operation_name:
            raise ValueError("operation_name is required")
        if not self.authoritative_source_file:
            raise ValueError("authoritative_source_file is required")
        if not self.authoritative_clause:
            raise ValueError("authoritative_clause is required")

    @classmethod
    def create(
        cls,
        *,
        operation_name: str,
        authoritative_source_file: str,
        authoritative_clause: str,
        input_receipt_ids: tuple[str, ...] = (),
        accessible_evidence: tuple[str, ...] = (),
        operation_performed: str,
        resulting_difference_or_consequence: str,
        status: ReceiptStatus,
        implementation_source: str = "",
        clause_id: str = "",
    ) -> "DerivationReceipt":
        fields = {
            "operation_name": operation_name,
            "authoritative_source_file": authoritative_source_file,
            "authoritative_clause": authoritative_clause,
            "input_receipt_ids": tuple(input_receipt_ids),
            "accessible_evidence": tuple(accessible_evidence),
            "operation_performed": operation_performed,
            "resulting_difference_or_consequence": (
                resulting_difference_or_consequence
            ),
            "status": status,
            "implementation_source": implementation_source,
            "clause_id": clause_id,
        }
        canonical = json.dumps(
            fields,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        receipt_id = hashlib.sha256(canonical).hexdigest()
        return cls(receipt_id=receipt_id, **fields)