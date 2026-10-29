"""Separate, non-authoritative conceptual freeze for the glassy dilemma."""

from .authority import (
    DATA_VERDICTS,
    EXPERIMENT_ID,
    FROZEN_SOLUTION_SOURCE,
    FREEZE_STATUS,
    REOPEN_DIMENSIONS,
    FrozenSolution,
    GlassyDilemmaAuthorityError,
    load_frozen_solution,
)

__all__ = [
    "DATA_VERDICTS",
    "EXPERIMENT_ID",
    "FROZEN_SOLUTION_SOURCE",
    "FREEZE_STATUS",
    "REOPEN_DIMENSIONS",
    "FrozenSolution",
    "GlassyDilemmaAuthorityError",
    "load_frozen_solution",
]