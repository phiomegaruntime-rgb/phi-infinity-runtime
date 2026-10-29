"""Non-authoritative A/B/C echo experiment runtime.

This package is intentionally separate from ``experimental_m_runtime`` and
``m_machine``. Its results concern operational recursion and causal dependence,
not consciousness, sentience, or subjective experience.
"""

from .model import (
    ABCTestResult,
    COMPARISON_FIELDS,
    ContentSensitiveCase,
    ContentSensitiveComparison,
    ComparatorRequest,
    CycleRecord,
    FrozenArtifact,
    InputSnapshot,
    MExperimentalPlan,
    M_ONLY_EXACT_PATH,
    VariationMeasurement,
    WorkerRequest,
)
from .comparison import compare_content_sensitive
from .runtime import (
    ABCFailClosedError,
    ABCEchoRuntime,
    CONDITION_BROKEN_ECHO,
    CONDITION_FALSE_ECHO,
    CONDITION_NULL,
    CONDITION_REAL_ECHO,
    CONDITIONS,
    DEFAULT_STIMULUS,
)

__all__ = [
    "ABCTestResult",
    "ABCFailClosedError",
    "ABCEchoRuntime",
    "CONDITION_BROKEN_ECHO",
    "CONDITION_FALSE_ECHO",
    "CONDITION_NULL",
    "CONDITION_REAL_ECHO",
    "CONDITIONS",
    "COMPARISON_FIELDS",
    "ContentSensitiveCase",
    "ContentSensitiveComparison",
    "ComparatorRequest",
    "CycleRecord",
    "DEFAULT_STIMULUS",
    "FrozenArtifact",
    "InputSnapshot",
    "MExperimentalPlan",
    "M_ONLY_EXACT_PATH",
    "VariationMeasurement",
    "WorkerRequest",
    "compare_content_sensitive",
]