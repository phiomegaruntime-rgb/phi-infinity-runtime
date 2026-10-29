"""Fail-closed loader for the separate glassy-dilemma conceptual freeze."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path


EXPERIMENT_ID = "PHI_GLASSY_DILEMMA"
EXPERIMENT_VERSION = "1.0.0-conceptual-freeze"
FROZEN_SOLUTION_SOURCE = "experimental_glassy_dilemma/FROZEN_SOLUTION.md"
FREEZE_STATUS = "FROZEN BEFORE DATA"
PHASE = "CONCEPTUAL_FREEZE_ONLY"
DATA_VERDICTS = ("COMPATIBLE", "INCOMPATIBLE", "INSUFFICIENT")
REOPEN_DIMENSIONS = (
    "field",
    "dependencies",
    "genealogy",
    "scale",
    "access",
)

_BEGIN_MARKER = "<!-- FROZEN_STATEMENT_BEGIN -->"
_END_MARKER = "<!-- FROZEN_STATEMENT_END -->"

EXPECTED_FROZEN_SOLUTION_SHA256 = (
    "963c77685b8d91069103d45d12e04d39fa6da7fd6e49d88e2dddcdbd5caf60a0"
)
EXPECTED_FROZEN_STATEMENT_SHA256 = (
    "ae7083206582328128af186899cd19ff616156e2e26970f67f3164a4ed5d31c1"
)


@dataclass(frozen=True, slots=True)
class FrozenSolution:
    """The exact conceptual input admitted by this experiment's phase 1."""

    experiment_id: str
    version: str
    phase: str
    freeze_status: str
    source: str
    source_sha256: str
    statement: str
    statement_sha256: str
    reopen_dimensions: tuple[str, ...]
    allowed_data_verdicts: tuple[str, ...]


class GlassyDilemmaAuthorityError(RuntimeError):
    """Raised when the separate frozen source is absent or inconsistent."""


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _extract_statement(source_text: str) -> str:
    if source_text.count(_BEGIN_MARKER) != 1:
        raise GlassyDilemmaAuthorityError(
            "Frozen statement begin marker is missing or duplicated."
        )
    if source_text.count(_END_MARKER) != 1:
        raise GlassyDilemmaAuthorityError(
            "Frozen statement end marker is missing or duplicated."
        )
    statement = source_text.split(_BEGIN_MARKER, 1)[1].split(_END_MARKER, 1)[0]
    statement = statement.strip()
    if not statement:
        raise GlassyDilemmaAuthorityError("Frozen statement is empty.")
    return statement


def load_frozen_solution(repository_root: str | Path) -> FrozenSolution:
    """Load phase 1 only, rejecting any source or digest drift."""

    root = Path(repository_root).resolve()
    source_path = root / FROZEN_SOLUTION_SOURCE
    if not source_path.is_file():
        raise GlassyDilemmaAuthorityError(
            f"Missing frozen solution source: {FROZEN_SOLUTION_SOURCE}"
        )
    if "PENDING" in {
        EXPECTED_FROZEN_SOLUTION_SHA256,
        EXPECTED_FROZEN_STATEMENT_SHA256,
    }:
        raise GlassyDilemmaAuthorityError("Frozen solution digests are pending.")

    source_bytes = source_path.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if source_sha256 != EXPECTED_FROZEN_SOLUTION_SHA256:
        raise GlassyDilemmaAuthorityError("Frozen solution source hash mismatch.")

    source_text = source_bytes.decode("utf-8")
    statement = _extract_statement(source_text)
    statement_sha256 = _sha256_text(statement)
    if statement_sha256 != EXPECTED_FROZEN_STATEMENT_SHA256:
        raise GlassyDilemmaAuthorityError("Frozen statement hash mismatch.")

    return FrozenSolution(
        experiment_id=EXPERIMENT_ID,
        version=EXPERIMENT_VERSION,
        phase=PHASE,
        freeze_status=FREEZE_STATUS,
        source=FROZEN_SOLUTION_SOURCE,
        source_sha256=source_sha256,
        statement=statement,
        statement_sha256=statement_sha256,
        reopen_dimensions=REOPEN_DIMENSIONS,
        allowed_data_verdicts=DATA_VERDICTS,
    )