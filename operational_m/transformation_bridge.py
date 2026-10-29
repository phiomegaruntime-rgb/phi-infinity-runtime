"""Candidate-only transformation-to-difference operation.

This module is deliberately independent of ``m_machine``.  Importing it does
not register a proposition, rule, constructor, receipt, or authority in the
frozen kernel.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Literal


OPERATIONAL_BRIDGE_VERSION = "1"
AUTHORITY_SOURCE = "docs/operational/TRANSFORMATION_DIFFERENCE_BRIDGE_V1.md"
AUTHORITY_RANGE = (1, 23)
AUTHORITY_ID = "OPERATIONAL_TRANSFORMATION_DIFFERENCE_BRIDGE_V1"
OPERATIONAL_RULE_ID = (
    "OPERATIONAL_RULE_REAL_TRANSFORMATION_IMPLIES_DIFFERENCE_V1"
)
AUTHORITY_HASH = (
    "81a48a85604dad9a29fbced6fd718233ff87fa6afb59c04b1e2a34549790e6b4"
)

_REQUIRED_SCOPE_KEYS = (
    "access_snapshot",
    "mechanical_configuration",
    "field_context",
    "scale",
    "genealogy",
    "execution_lineage",
)
_FORBIDDEN_SCOPE_KEYS = frozenset({"pair_scope"})
_PROVENANCE_PREFIXES = ("receipt:", "attestation:")
_ANCESTRY_PREFIXES = ("trust-root:", "contract:", "assertion:")


OperationalScope = tuple[tuple[str, str], ...]
OperationalDecision = Literal["CANDIDATE", "UNRESOLVED", "BLOCK"]


class OperationalPropositionType(str, Enum):
    REAL_TRANSFORMATION_EXISTS = "REAL_TRANSFORMATION_EXISTS"
    REAL_DIFFERENCE_EXISTS = "REAL_DIFFERENCE_EXISTS"


class OptInRequired(RuntimeError):
    """Raised when the operational extension is requested without opt-in."""


class OperationalAuthorityError(ValueError):
    """Raised when the extension's own authority is unavailable or altered."""


@dataclass(frozen=True, slots=True)
class TransformationGrounding:
    """External grounding metadata; no source meaning is inferred."""

    grounding_id: str
    authority: str
    provenance: tuple[str, ...]
    ancestry: tuple[str, ...]
    historically_valid: bool = True
    currently_applicable: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "ancestry", tuple(self.ancestry))


@dataclass(frozen=True, slots=True)
class OperationalReceipt:
    receipt_id: str
    rule_id: str
    premise_receipt_ids: tuple[str, ...]
    resulting_proposition_id: str
    authority_id: str
    authority_hash: str
    status: Literal["DERIVED_OPERATIONAL"]


@dataclass(frozen=True, slots=True)
class DifferenceCandidate:
    proposition_id: str
    proposition_type: OperationalPropositionType
    scope: OperationalScope
    parent_receipt_ids: tuple[str, ...]
    grounding_id: str
    provenance: tuple[str, ...]
    ancestry: tuple[str, ...]
    rule_id: str
    rule_version: str
    witness_status: Literal["WITNESS_FREE"]
    auto_promoted: bool = False


@dataclass(frozen=True, slots=True)
class BridgeResult:
    decision: OperationalDecision
    reason: str
    candidate: DifferenceCandidate | None = None
    receipt: OperationalReceipt | None = None


def _digest(value: object) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def verify_operational_authority(
    repository_root: Path | str = Path("."),
) -> str:
    path = Path(repository_root).resolve() / AUTHORITY_SOURCE
    if not path.is_file():
        raise OperationalAuthorityError(
            f"Operational authority source is missing: {AUTHORITY_SOURCE}"
        )
    lines = path.read_bytes().splitlines(keepends=True)
    start, end = AUTHORITY_RANGE
    selected = lines[start - 1 : end]
    if len(selected) != end - start + 1:
        raise OperationalAuthorityError(
            "Operational authority range is incomplete."
        )
    actual = hashlib.sha256(b"".join(selected)).hexdigest()
    if actual != AUTHORITY_HASH:
        raise OperationalAuthorityError(
            "Operational authority hash mismatch."
        )
    return actual


def _normalize_scope(scope: object) -> OperationalScope | None:
    if not isinstance(scope, (tuple, list)):
        return None
    try:
        pairs = tuple((str(name), str(value)) for name, value in scope)
    except (TypeError, ValueError):
        return None
    names = tuple(name for name, _ in pairs)
    if len(names) != len(set(names)):
        return None
    if _FORBIDDEN_SCOPE_KEYS.intersection(names):
        return None
    if set(names) != set(_REQUIRED_SCOPE_KEYS):
        return None
    if any(not name or not value for name, value in pairs):
        return None
    return tuple(pairs)


def _invalid_provenance(grounding: TransformationGrounding) -> bool:
    return any(
        not item
        or not item.startswith(_PROVENANCE_PREFIXES)
        or any(
            forbidden in item.lower()
            for forbidden in ("label:", "timestamp:", "payload:", "model:")
        )
        for item in grounding.provenance
    )


def _invalid_ancestry(grounding: TransformationGrounding) -> bool:
    return any(
        not item or not item.startswith(_ANCESTRY_PREFIXES)
        for item in grounding.ancestry
    )


class OperationalBridge:
    """An explicit, candidate-only operational rule."""

    version = OPERATIONAL_BRIDGE_VERSION
    rule_id = OPERATIONAL_RULE_ID

    def __init__(
        self,
        *,
        opt_in: bool,
        repository_root: Path | str = Path("."),
    ) -> None:
        if not opt_in:
            raise OptInRequired(
                "The operational transformation bridge requires explicit opt-in."
            )
        self.authority_hash = verify_operational_authority(repository_root)

    def derive(
        self,
        *,
        transformation_scope: object,
        grounding: TransformationGrounding | None,
        premise_receipt_ids: tuple[str, ...] = (),
    ) -> BridgeResult:
        scope = _normalize_scope(transformation_scope)
        if scope is None:
            return BridgeResult(
                "UNRESOLVED",
                "The transformation scope is missing or not exact.",
            )
        if grounding is None:
            return BridgeResult(
                "UNRESOLVED",
                "Transformation grounding is missing.",
            )
        if not grounding.historically_valid or not grounding.currently_applicable:
            return BridgeResult(
                "UNRESOLVED",
                "Transformation grounding is not currently valid.",
            )
        if not grounding.authority or not grounding.authority.startswith(
            "external:"
        ):
            return BridgeResult(
                "BLOCK",
                "Transformation grounding authority is invalid.",
            )
        if _invalid_provenance(grounding):
            return BridgeResult(
                "BLOCK",
                "Transformation provenance is invalid or representation-based.",
            )
        if _invalid_ancestry(grounding):
            return BridgeResult(
                "BLOCK",
                "Transformation grounding ancestry is invalid.",
            )
        premise_receipts = tuple(premise_receipt_ids)
        if (
            not grounding.grounding_id
            or not grounding.provenance
            or not grounding.ancestry
            or not premise_receipts
        ):
            return BridgeResult(
                "UNRESOLVED",
                "Grounding, provenance, ancestry, and receipts are insufficient.",
            )
        if not set(premise_receipts).issubset(set(grounding.provenance)):
            return BridgeResult(
                "UNRESOLVED",
                "Premise receipts are not preserved by the grounding provenance.",
            )
        proposition_id = _digest(
            {
                "type": OperationalPropositionType.REAL_DIFFERENCE_EXISTS.value,
                "scope": scope,
                "premise_receipts": premise_receipts,
                "grounding_id": grounding.grounding_id,
                "rule_id": self.rule_id,
                "version": self.version,
            }
        )
        receipt_fields = {
            "rule_id": self.rule_id,
            "premise_receipt_ids": premise_receipts,
            "resulting_proposition_id": proposition_id,
            "authority_id": AUTHORITY_ID,
            "authority_hash": self.authority_hash,
            "status": "DERIVED_OPERATIONAL",
        }
        receipt = OperationalReceipt(
            receipt_id=_digest(receipt_fields),
            **receipt_fields,
        )
        candidate = DifferenceCandidate(
            proposition_id=proposition_id,
            proposition_type=OperationalPropositionType.REAL_DIFFERENCE_EXISTS,
            scope=scope,
            parent_receipt_ids=premise_receipts,
            grounding_id=grounding.grounding_id,
            provenance=grounding.provenance,
            ancestry=grounding.ancestry,
            rule_id=self.rule_id,
            rule_version=self.version,
            witness_status="WITNESS_FREE",
        )
        return BridgeResult(
            "CANDIDATE",
            "Exact operational bridge candidate derived; no M promotion performed.",
            candidate,
            receipt,
        )


def create_operational_bridge(
    *,
    opt_in: bool = False,
    repository_root: Path | str = Path("."),
) -> OperationalBridge:
    """Create the extension only when the caller explicitly opts in."""

    return OperationalBridge(
        opt_in=opt_in,
        repository_root=repository_root,
    )