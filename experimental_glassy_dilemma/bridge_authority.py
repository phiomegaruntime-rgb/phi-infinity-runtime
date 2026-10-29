"""Authority loader for the pre-dataset glassy-dilemma bridge.

This authority is separate from M CURRENT.  It verifies that the bridge and
the structural evaluator still match the frozen, pre-dataset manifest.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from .authority import FrozenSolution, load_frozen_solution


BRIDGE_MANIFEST_SOURCE = (
    "experimental_glassy_dilemma/BRIDGE_EVALUATOR_FREEZE.json"
)
EXPECTED_BRIDGE_MANIFEST_SHA256 = "PENDING"
M_CURRENT_SOURCE = "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md"


class BridgeAuthorityError(RuntimeError):
    """Raised when the pre-dataset bridge authority is not exact."""


@dataclass(frozen=True, slots=True)
class BridgeFreezeManifest:
    """Validated pre-dataset manifest and its already validated freeze."""

    manifest_sha256: str
    payload: dict[str, Any]
    conceptual_freeze: FrozenSolution


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_path(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise BridgeAuthorityError(
            f"Manifest path escapes repository root: {relative_path!r}."
        ) from exc
    return candidate


def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise BridgeAuthorityError(f"Manifest field {field_name!r} is invalid.")
    return value


def load_bridge_freeze(repository_root: str | Path) -> BridgeFreezeManifest:
    """Load and verify the complete pre-dataset bridge authority."""

    root = Path(repository_root).resolve()
    conceptual_freeze = load_frozen_solution(root)
    manifest_path = _safe_path(root, BRIDGE_MANIFEST_SOURCE)
    if not manifest_path.is_file():
        raise BridgeAuthorityError("Bridge freeze manifest is missing.")
    if EXPECTED_BRIDGE_MANIFEST_SHA256 == "PENDING":
        raise BridgeAuthorityError("Bridge freeze manifest digest is pending.")

    manifest_bytes = manifest_path.read_bytes()
    manifest_sha256 = _sha256_bytes(manifest_bytes)
    if manifest_sha256 != EXPECTED_BRIDGE_MANIFEST_SHA256:
        raise BridgeAuthorityError("Bridge freeze manifest hash mismatch.")
    try:
        payload = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BridgeAuthorityError("Bridge freeze manifest is not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise BridgeAuthorityError("Bridge freeze manifest must be an object.")

    if payload.get("phase") != "PRE_DATASET":
        raise BridgeAuthorityError("Bridge freeze phase is not PRE_DATASET.")
    if payload.get("data_sources_used") != []:
        raise BridgeAuthorityError(
            "Bridge freeze manifest records unexpected data usage."
        )
    if payload.get("allowed_verdicts") != [
        "COMPATIBLE",
        "INCOMPATIBLE",
        "INSUFFICIENT",
    ]:
        raise BridgeAuthorityError("Bridge verdict contract has changed.")

    source_basis = payload.get("source_basis")
    if not isinstance(source_basis, list) or not source_basis:
        raise BridgeAuthorityError("Bridge source basis is incomplete.")
    expected_basis = {
        conceptual_freeze.source: conceptual_freeze.source_sha256,
        M_CURRENT_SOURCE: _require_string(
            next(
                (
                    item.get("sha256")
                    for item in source_basis
                    if isinstance(item, dict)
                    and item.get("path") == M_CURRENT_SOURCE
                ),
                "",
            ),
            f"source_basis[{M_CURRENT_SOURCE}].sha256",
        ),
    }
    for relative_path, expected_hash in expected_basis.items():
        source_path = _safe_path(root, relative_path)
        if not source_path.is_file():
            raise BridgeAuthorityError(f"Bridge source is missing: {relative_path}.")
        actual_hash = _sha256_bytes(source_path.read_bytes())
        if actual_hash != expected_hash:
            raise BridgeAuthorityError(
                f"Bridge source hash mismatch: {relative_path}."
            )

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise BridgeAuthorityError("Bridge artifact hashes are missing.")
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise BridgeAuthorityError("Bridge artifact entry is invalid.")
        relative_path = _require_string(artifact.get("path"), "artifact.path")
        expected_hash = _require_string(artifact.get("sha256"), "artifact.sha256")
        artifact_path = _safe_path(root, relative_path)
        if not artifact_path.is_file():
            raise BridgeAuthorityError(f"Bridge artifact is missing: {relative_path}.")
        actual_hash = _sha256_bytes(artifact_path.read_bytes())
        if actual_hash != expected_hash:
            raise BridgeAuthorityError(
                f"Bridge artifact hash mismatch: {relative_path}."
            )

    return BridgeFreezeManifest(
        manifest_sha256=manifest_sha256,
        payload=payload,
        conceptual_freeze=conceptual_freeze,
    )