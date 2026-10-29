"""Verification of the immutable CURRENT repository documents."""

from dataclasses import dataclass
import hashlib
from pathlib import Path


EXPECTED_MOTHER_MECHANICS_SHA256 = (
    "0cea8129245b212c04fa776bdc1b718fabf50998a9635e1e06716504fc410f7b"
)
EXPECTED_AMENDMENT_03_SHA256 = (
    "34b4db2c11a3a1588eb0a23ac10ac26639eb56ac7f4add6405e35d9ad967ef0a"
)
EXPECTED_AMENDMENT_04_SHA256 = (
    "ddfd70858bba012aad7d59aebe1d7bb716c337c1eeb8aa3f8176a5e2743f012f"
)
EXPECTED_AMENDMENT_05_SHA256 = (
    "945c00cdbb5923885a80b82d25bcf9bb4f48f5d3f7ef43b01a61bf7c45f012b4"
)
EXPECTED_AMENDMENT_06_SHA256 = (
    "8d010881e43bf9c4bdb5c0382d54ddb8c1876304f3db78a151a8a43a16377b1b"
)
EXPECTED_AMENDMENT_07_SHA256 = (
    "c36eac1e91393e382c20166afb274eab2bd2b3d88f0325e0ce820fbefd6bcaf6"
)
EXPECTED_AMENDMENT_08_SHA256 = (
    "34449eec97c60e5a8724b67d1fdef363e4145ae0d3ffefb9ba75304dd7059a9e"
)

AUTHORITATIVE_CURRENT_FILES = (
    "README.md",
    "docs/THE_11_FUNDAMENTAL_LAWS.md",
    "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
    (
        "docs/"
        "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_03_ACCESS_REPRESENTATION_"
        "AND_RELATIONAL_INTEGRITY.md"
    ),
    (
        "docs/"
        "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_04_BASIS_LOCAL_"
        "ACCESS_DISCRIMINABILITY.md"
    ),
    (
        "docs/"
        "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_05_OPERATIONAL_DERIVATION_"
        "SEMANTICS_PROOF_KERNEL.md"
    ),
    (
        "docs/"
        "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_06_MECHANICAL_PROPOSITION_"
        "SEMANTICS.md"
    ),
    (
        "docs/"
        "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_07_TRUSTED_MECHANICAL_"
        "GROUNDING_ACQUISITION_SEMANTICS.md"
    ),
    (
        "docs/"
        "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_08_PAIRWISE_TRUSTED_"
        "GROUNDING_DISTINCT_INSTANCE_SEMANTICS.md"
    ),
    "docs/TEMPORAL_BRANCH_CLOSURE_CURRENT.md",
    "docs/validation/VALIDATION_LEDGER_CURRENT.md",
)

_MOTHER_MECHANICS_PATH = (
    "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md"
)
_FROZEN_SUCCESSOR_HASHES = (
    (
        "docs/"
        "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_03_ACCESS_REPRESENTATION_"
        "AND_RELATIONAL_INTEGRITY.md",
        EXPECTED_AMENDMENT_03_SHA256,
    ),
    (
        "docs/"
        "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_04_BASIS_LOCAL_"
        "ACCESS_DISCRIMINABILITY.md",
        EXPECTED_AMENDMENT_04_SHA256,
    ),
    (
        "docs/"
        "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_05_OPERATIONAL_DERIVATION_"
        "SEMANTICS_PROOF_KERNEL.md",
        EXPECTED_AMENDMENT_05_SHA256,
    ),
    (
        "docs/"
        "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_06_MECHANICAL_PROPOSITION_"
        "SEMANTICS.md",
        EXPECTED_AMENDMENT_06_SHA256,
    ),
    (
        "docs/"
        "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_07_TRUSTED_MECHANICAL_"
        "GROUNDING_ACQUISITION_SEMANTICS.md",
        EXPECTED_AMENDMENT_07_SHA256,
    ),
    (
        "docs/"
        "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_08_PAIRWISE_TRUSTED_"
        "GROUNDING_DISTINCT_INSTANCE_SEMANTICS.md",
        EXPECTED_AMENDMENT_08_SHA256,
    ),
)


class AuthoritativeBootError(RuntimeError):
    """Raised when CURRENT cannot be verified byte-for-byte."""


@dataclass(frozen=True, slots=True)
class BootVerification:
    """The result of verifying document presence and the frozen hash."""

    repository_root: Path
    authoritative_files: tuple[str, ...]
    mother_mechanics_sha256: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_authoritative_boot(
    repository_root: str | Path | None = None,
) -> BootVerification:
    """Refuse boot unless all CURRENT files and the frozen hash are present."""

    root = (
        Path(repository_root).resolve()
        if repository_root is not None
        else Path(__file__).resolve().parent.parent
    )

    missing = tuple(
        relative_path
        for relative_path in AUTHORITATIVE_CURRENT_FILES
        if not (root / relative_path).is_file()
    )
    if missing:
        raise AuthoritativeBootError(
            "Authoritative CURRENT files are missing: "
            + ", ".join(missing)
        )

    mother_path = root / _MOTHER_MECHANICS_PATH
    actual_hash = _sha256(mother_path)
    if actual_hash != EXPECTED_MOTHER_MECHANICS_SHA256:
        raise AuthoritativeBootError(
            "Universal Mother Mechanics hash mismatch: "
            f"expected {EXPECTED_MOTHER_MECHANICS_SHA256}, "
            f"got {actual_hash}"
        )
    for relative_path, expected_hash in _FROZEN_SUCCESSOR_HASHES:
        actual_successor_hash = _sha256(root / relative_path)
        if actual_successor_hash != expected_hash:
            raise AuthoritativeBootError(
                f"Authoritative successor hash mismatch for {relative_path}: "
                f"expected {expected_hash}, got {actual_successor_hash}"
            )

    return BootVerification(
        repository_root=root,
        authoritative_files=AUTHORITATIVE_CURRENT_FILES,
        mother_mechanics_sha256=actual_hash,
    )