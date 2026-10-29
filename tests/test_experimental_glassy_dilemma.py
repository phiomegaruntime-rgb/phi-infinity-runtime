"""Tests for the separate phase-1 conceptual freeze."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import shutil

import pytest

from experimental_glassy_dilemma import (
    DATA_VERDICTS,
    EXPERIMENT_ID,
    FREEZE_STATUS,
    REOPEN_DIMENSIONS,
    GlassyDilemmaAuthorityError,
    load_frozen_solution,
)
from experimental_glassy_dilemma.authority import FROZEN_SOLUTION_SOURCE


ROOT = Path(__file__).resolve().parents[1]


def test_phase_one_loads_as_a_separate_non_authoritative_freeze() -> None:
    solution = load_frozen_solution(ROOT)

    assert solution.experiment_id == EXPERIMENT_ID == "PHI_GLASSY_DILEMMA"
    assert solution.phase == "CONCEPTUAL_FREEZE_ONLY"
    assert solution.freeze_status == FREEZE_STATUS == "FROZEN BEFORE DATA"
    assert solution.reopen_dimensions == (
        "field",
        "dependencies",
        "genealogy",
        "scale",
        "access",
    )
    assert solution.allowed_data_verdicts == DATA_VERDICTS == (
        "COMPATIBLE",
        "INCOMPATIBLE",
        "INSUFFICIENT",
    )
    assert "absolute stoppage conclusion is not" in solution.statement
    assert "REOPEN" in solution.statement


def test_loaded_solution_is_immutable() -> None:
    solution = load_frozen_solution(ROOT)

    with pytest.raises(FrozenInstanceError):
        solution.freeze_status = "CHANGED"  # type: ignore[misc]


def test_source_mutation_is_rejected_before_any_data_phase(tmp_path: Path) -> None:
    isolated_root = tmp_path / "isolated"
    package_copy = isolated_root / "experimental_glassy_dilemma"
    package_copy.mkdir(parents=True)
    source = ROOT / FROZEN_SOLUTION_SOURCE
    mutated = source.read_text(encoding="utf-8").replace(
        "progressive loss of local sufficiency",
        "permanent local sufficiency",
    )
    (package_copy / "FROZEN_SOLUTION.md").write_text(mutated, encoding="utf-8")

    with pytest.raises(GlassyDilemmaAuthorityError, match="source hash mismatch"):
        load_frozen_solution(isolated_root)


def test_experiment_contains_no_data_phase_or_dataset() -> None:
    package_dir = ROOT / "experimental_glassy_dilemma"

    assert not (package_dir / "data").exists()
    assert not (package_dir / "datasets").exists()
    assert not (package_dir / "traces").exists()
    assert not hasattr(load_frozen_solution(ROOT), "data")