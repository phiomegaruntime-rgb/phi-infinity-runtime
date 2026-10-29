"""Frozen authority for the separate false-sufficiency research gate."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from experimental_m_runtime_v2 import FragmentRef


AUTHORITY_SOURCE = "experimental_false_sufficiency_gate/AUTHORITY.md"
GATE_ID = "PHI_FALSE_SUFFICIENCY_GENERALITY_GATE"
GATE_VERSION = "1.0.0-structural-falsifier"

HYPOTHESIS_FORMULA = "\n".join(
    (
        "PERSISTENT_REPRESENTATION_MECHANICS_DIVERGENCE_REQUIRES_UNSUPPORTED_CLOSURE_PROPAGATION",
        "SUPPORTED_LOCAL_CLOSURE_REMAINS_WITHIN_SUPPORTED_SCOPE",
        "UNSUPPORTED_FALSE_SUFFICIENCY_REOPENS",
        "ACCESS_INSUFFICIENCY_IS_NOT_FALSE_SUFFICIENCY",
        "A_SUPPORTED_LOCAL_COUNTEREXAMPLE_FALSIFIES_GENERALITY",
        "NO_UNIVERSALITY_IS_ASSERTED_OUTSIDE_THE_TEST_DOMAIN",
    )
)

FALSIFIER_FORMULA = "\n".join(
    (
        "CLOSURE_SUPPORTED_LOCALLY",
        "DEPENDENCIES_ACCESSIBLE_AND_REPRESENTED",
        "GENEALOGY_AND_PERSISTENCE_REPRESENTED",
        "NO_PROPAGATION_BEYOND_SUPPORTED_SCOPE",
        "SYSTEMATIC_REPRESENTATION_MECHANICS_DIVERGENCE",
    )
)

EXPECTED_AUTHORITY_SHA256 = (
    "d1f7c71a8f04dccb739b93c0d15c72276cda81a894efa83ecc69beab9a291e8c"
)
EXPECTED_HYPOTHESIS_SHA256 = (
    "37f2f53a2cc5116c916e9daf13f33a1c731c68f5e66fc5e9526719d1711d1158"
)
EXPECTED_FALSIFIER_SHA256 = (
    "cad2ea17338f686e961d42de97ba31f05898344c13d15f5f245ced05ccd92ce1"
)


@dataclass(frozen=True, slots=True)
class FrozenGateAuthority:
    authority_fragment: FragmentRef
    authority_hash_fragment: FragmentRef
    hypothesis_fragment: FragmentRef
    falsifier_fragment: FragmentRef
    hypothesis_hash_fragment: FragmentRef
    falsifier_hash_fragment: FragmentRef


class GateAuthorityError(RuntimeError):
    """Raised when the separate gate authority is absent or inconsistent."""


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_frozen_gate_authority(
    repository_root: str | Path,
) -> FrozenGateAuthority:
    root = Path(repository_root).resolve()
    source = root / AUTHORITY_SOURCE
    if not source.is_file():
        raise GateAuthorityError(f"Missing gate authority source: {AUTHORITY_SOURCE}")
    expected = (
        EXPECTED_AUTHORITY_SHA256,
        EXPECTED_HYPOTHESIS_SHA256,
        EXPECTED_FALSIFIER_SHA256,
    )
    if any("PENDING" in value for value in expected):
        raise GateAuthorityError("Gate authority hashes are still pending.")
    actual_authority = hashlib.sha256(source.read_bytes()).hexdigest()
    actual_hypothesis = _sha256_text(HYPOTHESIS_FORMULA)
    actual_falsifier = _sha256_text(FALSIFIER_FORMULA)
    if actual_authority != EXPECTED_AUTHORITY_SHA256:
        raise GateAuthorityError("Gate authority source hash mismatch.")
    if actual_hypothesis != EXPECTED_HYPOTHESIS_SHA256:
        raise GateAuthorityError("Gate hypothesis hash mismatch.")
    if actual_falsifier != EXPECTED_FALSIFIER_SHA256:
        raise GateAuthorityError("Gate falsifier hash mismatch.")
    authority_fragment = FragmentRef(
        f"fragment:gate:authority:{actual_authority}"
    )
    return FrozenGateAuthority(
        authority_fragment=authority_fragment,
        authority_hash_fragment=FragmentRef(
            f"fragment:gate:authority-sha256:{actual_authority}"
        ),
        hypothesis_fragment=FragmentRef(
            f"fragment:gate:hypothesis:{actual_hypothesis}"
        ),
        falsifier_fragment=FragmentRef(
            f"fragment:gate:falsifier:{actual_falsifier}"
        ),
        hypothesis_hash_fragment=FragmentRef(
            f"fragment:gate:hypothesis-sha256:{actual_hypothesis}"
        ),
        falsifier_hash_fragment=FragmentRef(
            f"fragment:gate:falsifier-sha256:{actual_falsifier}"
        ),
    )