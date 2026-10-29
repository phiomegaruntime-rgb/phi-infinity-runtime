"""Authority and identity for the isolated experimental fragment runtime."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path


EXPERIMENTAL_RUNTIME_ID = "PHI_EXPERIMENTAL_FRAGMENT_RUNTIME"
EXPERIMENTAL_RUNTIME_VERSION = "0.2.0-categorical-fragment-foundation"
AUTHORITY_SOURCE = "experimental_m_runtime/AUTHORITY.md"
FOUNDATION_VERSION = "1.0.0-categorical-fragment-foundation"
FOUNDATION_FORMULA = "\n".join(
    (
        "FOR_EVERY(X): FRAGMENT(X)",
        "FRAGMENT(X) -> FORMED_TRAVERSED_OR_MODIFIED_BY_FRAGMENTS(X)",
        "FRAGMENT(X) -> FOLLOWS_THE_SAME_M(X)",
        "NO_ABSOLUTE_REFERENCE(X,Y)",
        "DESCRIPTION_MEASURE_CLASSIFICATION_OR_REPRESENTATION -> FRAGMENT",
        "NOTHING_EXTERNAL",
        "NOTHING_OUTSIDE_INFINITO",
        "INFINITO -> FRAGMENT_AND_COMPOSED_OF_FRAGMENTS",
    )
)
FOUNDATION_SEMANTIC_HASH = (
    "SEMANTIC_HASH_PENDING"
)
EXPECTED_AUTHORITY_SHA256 = (
    "AUTHORITY_HASH_PENDING"
)
RUNTIME_HASH = hashlib.sha256(
    f"{EXPERIMENTAL_RUNTIME_ID}:{EXPERIMENTAL_RUNTIME_VERSION}:"
    f"{EXPECTED_AUTHORITY_SHA256}:{FOUNDATION_SEMANTIC_HASH}".encode("utf-8")
).hexdigest()


@dataclass(frozen=True, slots=True)
class ExperimentalAuthority:
    runtime_id: str
    version: str
    authority_source: str
    authority_sha256: str
    runtime_sha256: str


class ExperimentalAuthorityError(RuntimeError):
    """Raised when the experimental authority is missing or changed."""


def verify_experimental_authority(
    repository_root: str | Path | None = None,
) -> ExperimentalAuthority:
    root = (
        Path(repository_root).resolve()
        if repository_root is not None
        else Path(__file__).resolve().parent.parent
    )
    path = root / AUTHORITY_SOURCE
    if not path.is_file():
        raise ExperimentalAuthorityError(
            f"Missing experimental authority source: {AUTHORITY_SOURCE}"
        )
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != EXPECTED_AUTHORITY_SHA256:
        raise ExperimentalAuthorityError(
            "Experimental authority hash mismatch: "
            f"expected {EXPECTED_AUTHORITY_SHA256}, got {actual}"
        )
    return ExperimentalAuthority(
        runtime_id=EXPERIMENTAL_RUNTIME_ID,
        version=EXPERIMENTAL_RUNTIME_VERSION,
        authority_source=AUTHORITY_SOURCE,
        authority_sha256=actual,
        runtime_sha256=RUNTIME_HASH,
    )