"""Append-only receipts for the non-authoritative A/B/C experiment."""

from __future__ import annotations

from dataclasses import dataclass

from .model import canonical_json, digest_wire


NON_AUTHORITATIVE_SOURCE = "experimental_abc_runtime"


@dataclass(frozen=True, slots=True)
class ABCReceipt:
    receipt_id: str
    operation_name: str
    cycle: int
    parent_receipt_ids: tuple[str, ...]
    subject_digest: str
    provenance: tuple[str, ...]
    status: str
    digest: str


def create_receipt(
    *,
    operation_name: str,
    cycle: int,
    parent_receipt_ids: tuple[str, ...] = (),
    subject_digest: str,
    provenance: tuple[str, ...],
    status: str = "ALLOW",
) -> ABCReceipt:
    if not provenance:
        raise ValueError("A receipt requires provenance.")
    payload = {
        "operation_name": operation_name,
        "cycle": cycle,
        "parent_receipt_ids": list(parent_receipt_ids),
        "subject_digest": subject_digest,
        "provenance": list(provenance),
        "status": status,
        "source": NON_AUTHORITATIVE_SOURCE,
    }
    digest = digest_wire(canonical_json(payload))
    return ABCReceipt(
        receipt_id=f"abc:{operation_name}:{digest[:24]}",
        operation_name=operation_name,
        cycle=cycle,
        parent_receipt_ids=tuple(parent_receipt_ids),
        subject_digest=subject_digest,
        provenance=tuple(provenance),
        status=status,
        digest=digest,
    )


def validate_receipt_genealogy(receipts: tuple[ABCReceipt, ...]) -> None:
    """Require an append-only, fully resolvable receipt chain."""

    seen: set[str] = set()
    for receipt in receipts:
        if receipt.receipt_id in seen:
            raise ValueError("Receipt genealogy contains a duplicate receipt id.")
        if receipt.status != "ALLOW":
            raise ValueError("A non-ALLOW receipt cannot enter a successful chain.")
        if any(parent not in seen for parent in receipt.parent_receipt_ids):
            raise ValueError("Receipt genealogy references a future or missing parent.")
        seen.add(receipt.receipt_id)