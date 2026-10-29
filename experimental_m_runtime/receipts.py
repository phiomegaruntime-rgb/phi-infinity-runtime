"""Append-only receipt creation for the isolated experimental runtime."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json

from .authority import AUTHORITY_SOURCE, EXPECTED_AUTHORITY_SHA256
from .model import Decision, ExperimentalReceipt


def create_receipt(
    *,
    operation_name: str,
    input_receipt_ids: tuple[str, ...] = (),
    accessible_evidence: tuple[str, ...] = (),
    status: Decision | str = Decision.ALLOW,
    operation_performed: str = "",
) -> ExperimentalReceipt:
    payload = {
        "operation_name": operation_name,
        "input_receipt_ids": tuple(input_receipt_ids),
        "accessible_evidence": tuple(accessible_evidence),
        "status": str(status),
        "authority_source": AUTHORITY_SOURCE,
        "authority_hash": EXPECTED_AUTHORITY_SHA256,
        "operation_performed": operation_performed,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return ExperimentalReceipt(
        receipt_id=f"experimental:{operation_name}:{digest[:24]}",
        operation_name=operation_name,
        input_receipt_ids=tuple(input_receipt_ids),
        accessible_evidence=tuple(accessible_evidence),
        status=status,
        authority_source=AUTHORITY_SOURCE,
        authority_hash=EXPECTED_AUTHORITY_SHA256,
        digest=digest,
    )


def receipt_map(receipts: tuple[ExperimentalReceipt, ...]) -> dict[str, ExperimentalReceipt]:
    return {receipt.receipt_id: receipt for receipt in receipts}