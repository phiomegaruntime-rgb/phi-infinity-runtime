"""Pre-dataset structural evaluator for the glassy-dilemma experiment.

This evaluator is intentionally not a scientific model.  It verifies the
frozen bridge, provenance, lossless anonymous representation, exact values and
order, exact repetitions and differences, missing information, access scope,
and the frozen reopen dimensions.  It never smooths, imputes, thresholds,
fits, interprets, or emits a positive data verdict while the bridge has an
unresolved definition.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from math import isfinite
from pathlib import Path
from typing import Any, TypeAlias

from .authority import REOPEN_DIMENSIONS
from .bridge_authority import BridgeAuthorityError
from .operational_bridge import OperationalBridge, load_operational_bridge


JSONValue: TypeAlias = (
    None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]
)
ALLOWED_VERDICTS = ("COMPATIBLE", "INCOMPATIBLE", "INSUFFICIENT")
_ENVELOPE_FIELDS = {
    "dataset_id",
    "records",
    "provenance",
    "anonymization",
    "access",
    "missing_paths",
}
_ANONYMIZATION_FIELDS = {
    "names_removed",
    "semantic_labels_removed",
    "values_preserved",
    "order_preserved",
}
_PROVENANCE_FIELDS = {"source_digest", "chain"}
_ACCESS_FIELDS = {"supplied_domains", "unresolved_domains"}


class StructuralEvaluationError(ValueError):
    """Raised only for invalid evaluator construction, not data verdicts."""


def canonical_json(value: Any) -> str:
    """Serialize finite JSON-compatible data deterministically."""

    try:
        wire = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise StructuralEvaluationError(
            "Structural inputs must be finite JSON-compatible data."
        ) from exc
    return wire


def digest_wire(wire: str) -> str:
    return hashlib.sha256(wire.encode("utf-8")).hexdigest()


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


@dataclass(frozen=True, slots=True)
class DatasetEnvelope:
    """An immutable, anonymous, lossless structural input package."""

    wire: str
    digest: str

    @classmethod
    def create(
        cls,
        *,
        dataset_id: str,
        records: tuple[JSONValue, ...],
        source_digest: str,
        provenance_chain: tuple[str, ...],
        names_removed: bool,
        semantic_labels_removed: bool,
        values_preserved: bool,
        order_preserved: bool,
        supplied_domains: tuple[str, ...],
        unresolved_domains: tuple[str, ...] = (),
        missing_paths: tuple[str, ...] = (),
    ) -> "DatasetEnvelope":
        payload = {
            "dataset_id": dataset_id,
            "records": list(records),
            "provenance": {
                "source_digest": source_digest,
                "chain": list(provenance_chain),
            },
            "anonymization": {
                "names_removed": names_removed,
                "semantic_labels_removed": semantic_labels_removed,
                "values_preserved": values_preserved,
                "order_preserved": order_preserved,
            },
            "access": {
                "supplied_domains": list(supplied_domains),
                "unresolved_domains": list(unresolved_domains),
            },
            "missing_paths": list(missing_paths),
        }
        wire = canonical_json(payload)
        return cls(wire=wire, digest=digest_wire(wire))

    @property
    def payload(self) -> dict[str, JSONValue]:
        value = json.loads(self.wire)
        if not isinstance(value, dict):
            raise StructuralEvaluationError("Dataset envelope is not an object.")
        return value


@dataclass(frozen=True, slots=True)
class ExactDifference:
    left_index: int
    right_index: int
    left_digest: str
    right_digest: str


@dataclass(frozen=True, slots=True)
class StructuralEvaluation:
    """The complete fail-closed structural result."""

    verdict: str
    failed_closed: bool
    reasons: tuple[str, ...]
    dataset_digest: str | None
    provenance_digest: str | None
    cardinality: int
    value_digests: tuple[str, ...]
    exact_repetitions: tuple[tuple[int, ...], ...]
    exact_differences: tuple[ExactDifference, ...]
    missing_paths: tuple[str, ...]
    supplied_domains: tuple[str, ...]
    unresolved_domains: tuple[str, ...]
    reopen_dimensions: tuple[str, ...]
    unresolved_definitions: tuple[str, ...]
    bridge_manifest_sha256: str | None


def _closed_result(
    *,
    reasons: tuple[str, ...],
    dataset_digest: str | None = None,
    bridge_manifest_sha256: str | None = None,
    cardinality: int = 0,
    missing_paths: tuple[str, ...] = (),
    supplied_domains: tuple[str, ...] = (),
    unresolved_domains: tuple[str, ...] = (),
    reopen_dimensions: tuple[str, ...] = (),
    unresolved_definitions: tuple[str, ...] = (),
) -> StructuralEvaluation:
    return StructuralEvaluation(
        verdict="INSUFFICIENT",
        failed_closed=True,
        reasons=reasons,
        dataset_digest=dataset_digest,
        provenance_digest=None,
        cardinality=cardinality,
        value_digests=(),
        exact_repetitions=(),
        exact_differences=(),
        missing_paths=missing_paths,
        supplied_domains=supplied_domains,
        unresolved_domains=unresolved_domains,
        reopen_dimensions=reopen_dimensions,
        unresolved_definitions=unresolved_definitions,
        bridge_manifest_sha256=bridge_manifest_sha256,
    )


def _validate_envelope(
    envelope: DatasetEnvelope,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    errors: list[str] = []
    if not _is_sha256(envelope.digest):
        errors.append("dataset envelope digest is not a SHA-256 value")
    if digest_wire(envelope.wire) != envelope.digest:
        errors.append("dataset envelope digest mismatch")
    try:
        payload = json.loads(envelope.wire)
    except (TypeError, json.JSONDecodeError):
        return None, tuple(errors + ["dataset envelope wire is not valid JSON"])
    if not isinstance(payload, dict):
        return None, tuple(errors + ["dataset envelope is not an object"])
    if set(payload) != _ENVELOPE_FIELDS:
        errors.append("dataset envelope fields are incomplete or unexpected")

    if not isinstance(payload.get("dataset_id"), str) or not payload["dataset_id"]:
        errors.append("dataset id is missing")
    records = payload.get("records")
    if not isinstance(records, list):
        errors.append("records are missing or not ordered as a list")

    provenance = payload.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) != _PROVENANCE_FIELDS:
        errors.append("provenance is incomplete")
    else:
        if not _is_sha256(provenance.get("source_digest")):
            errors.append("source provenance digest is invalid")
        if (
            not isinstance(provenance.get("chain"), list)
            or not provenance["chain"]
            or not all(isinstance(item, str) and item for item in provenance["chain"])
        ):
            errors.append("provenance chain is missing")

    anonymization = payload.get("anonymization")
    if (
        not isinstance(anonymization, dict)
        or set(anonymization) != _ANONYMIZATION_FIELDS
        or not all(isinstance(value, bool) for value in anonymization.values())
    ):
        errors.append("lossless anonymization receipt is incomplete")
    elif not all(anonymization.values()):
        errors.append("lossless anonymization or order preservation is unverified")

    access = payload.get("access")
    if not isinstance(access, dict) or set(access) != _ACCESS_FIELDS:
        errors.append("access declaration is incomplete")
    else:
        for field_name in _ACCESS_FIELDS:
            value = access[field_name]
            if not isinstance(value, list) or not all(
                isinstance(item, str) for item in value
            ):
                errors.append(f"access field {field_name!r} is invalid")
        if isinstance(access.get("supplied_domains"), list):
            invalid = set(access["supplied_domains"]) - set(REOPEN_DIMENSIONS)
            if invalid:
                errors.append("access declares an unknown reopen domain")
        if isinstance(access.get("unresolved_domains"), list):
            invalid = set(access["unresolved_domains"]) - set(REOPEN_DIMENSIONS)
            if invalid:
                errors.append("access declares an unknown unresolved domain")

    missing_paths = payload.get("missing_paths")
    if not isinstance(missing_paths, list) or not all(
        isinstance(item, str) and item for item in missing_paths
    ):
        errors.append("missing-path declaration is invalid")
    return payload, tuple(errors)


def _structural_observations(
    records: list[JSONValue],
) -> tuple[
    tuple[str, ...],
    tuple[tuple[int, ...], ...],
    tuple[ExactDifference, ...],
]:
    value_digests = tuple(digest_wire(canonical_json(record)) for record in records)
    positions: dict[str, list[int]] = {}
    for index, value_digest in enumerate(value_digests):
        positions.setdefault(value_digest, []).append(index)
    repetitions = tuple(
        tuple(indexes)
        for _, indexes in sorted(positions.items())
        if len(indexes) > 1
    )
    differences: list[ExactDifference] = []
    for left_index in range(len(records)):
        for right_index in range(left_index + 1, len(records)):
            if value_digests[left_index] != value_digests[right_index]:
                differences.append(
                    ExactDifference(
                        left_index=left_index,
                        right_index=right_index,
                        left_digest=value_digests[left_index],
                        right_digest=value_digests[right_index],
                    )
                )
    return value_digests, repetitions, tuple(differences)


def evaluate_dataset(
    repository_root: str | Path,
    envelope: DatasetEnvelope,
) -> StructuralEvaluation:
    """Evaluate one anonymous package without adding a scientific criterion."""

    try:
        bridge: OperationalBridge = load_operational_bridge(str(repository_root))
    except (BridgeAuthorityError, OSError, ValueError) as exc:
        return _closed_result(reasons=(f"authority failure: {exc}",))

    payload, validation_errors = _validate_envelope(envelope)
    if validation_errors or payload is None:
        return _closed_result(
            reasons=validation_errors or ("dataset envelope is unresolved",),
            dataset_digest=envelope.digest,
            bridge_manifest_sha256=bridge.manifest.manifest_sha256,
        )

    records = payload["records"]
    assert isinstance(records, list)
    value_digests, repetitions, differences = _structural_observations(records)
    provenance = payload["provenance"]
    assert isinstance(provenance, dict)
    provenance_digest = digest_wire(canonical_json(provenance))
    access = payload["access"]
    assert isinstance(access, dict)
    supplied_domains = tuple(access["supplied_domains"])
    declared_unresolved = tuple(access["unresolved_domains"])
    missing_paths = tuple(payload["missing_paths"])

    reopen: list[str] = []
    for dimension in REOPEN_DIMENSIONS:
        if dimension in declared_unresolved or dimension not in supplied_domains:
            reopen.append(dimension)
    if missing_paths and "field" not in reopen:
        reopen.append("field")

    reasons: list[str] = []
    if bridge.unresolved_definitions:
        reasons.append(
            "pre-dataset operational definitions remain unresolved: "
            + ", ".join(bridge.unresolved_definitions)
        )
    if missing_paths:
        reasons.append("dataset declares missing values or paths")
    if reopen:
        reasons.append("required access domains remain unresolved")
    if reasons:
        return StructuralEvaluation(
            verdict="INSUFFICIENT",
            failed_closed=True,
            reasons=tuple(reasons),
            dataset_digest=envelope.digest,
            provenance_digest=provenance_digest,
            cardinality=len(records),
            value_digests=value_digests,
            exact_repetitions=repetitions,
            exact_differences=differences,
            missing_paths=missing_paths,
            supplied_domains=supplied_domains,
            unresolved_domains=declared_unresolved,
            reopen_dimensions=tuple(reopen),
            unresolved_definitions=bridge.unresolved_definitions,
            bridge_manifest_sha256=bridge.manifest.manifest_sha256,
        )

    # This branch is intentionally unreachable for the current frozen bridge.
    # A future positive or negative verdict needs a separately frozen rule.
    return StructuralEvaluation(
        verdict="INSUFFICIENT",
        failed_closed=True,
        reasons=(
            "no authorized pre-dataset compatibility rule exists; "
            "positive or negative classification is blocked",
        ),
        dataset_digest=envelope.digest,
        provenance_digest=provenance_digest,
        cardinality=len(records),
        value_digests=value_digests,
        exact_repetitions=repetitions,
        exact_differences=differences,
        missing_paths=missing_paths,
        supplied_domains=supplied_domains,
        unresolved_domains=declared_unresolved,
        reopen_dimensions=tuple(reopen),
        unresolved_definitions=bridge.unresolved_definitions,
        bridge_manifest_sha256=bridge.manifest.manifest_sha256,
    )