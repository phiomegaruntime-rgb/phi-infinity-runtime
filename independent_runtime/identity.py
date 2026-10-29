from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = "docs/operational/PHASE2_COMPLETION_CONTRACT.md"
CONTRACT_SHA256 = (
    "7a66f7bc62a36035da6b39ca4c86f5755155f635124d037cffcd0ad7cc354ceb"
)

FROZEN_SOURCE_HASHES = {
    "docs/PHASE0_CANDIDATE_SCOPE.md":
        "f0cf6e7d126946c67835101476746699aff4bc8d4645e3a203091286d206b4a6",
    "docs/UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_05_OPERATIONAL_DERIVATION_SEMANTICS_PROOF_KERNEL.md":
        "945c00cdbb5923885a80b82d25bcf9bb4f48f5d3f7ef43b01a61bf7c45f012b4",
    "docs/UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_06_MECHANICAL_PROPOSITION_SEMANTICS.md":
        "8d010881e43bf9c4bdb5c0382d54ddb8c1876304f3db78a151a8a43a16377b1b",
    "docs/UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_07_TRUSTED_MECHANICAL_GROUNDING_ACQUISITION_SEMANTICS.md":
        "c36eac1e91393e382c20166afb274eab2bd2b3d88f0325e0ce820fbefd6bcaf6",
    "docs/UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_08_PAIRWISE_TRUSTED_GROUNDING_DISTINCT_INSTANCE_SEMANTICS.md":
        "34449eec97c60e5a8724b67d1fdef363e4145ae0d3ffefb9ba75304dd7059a9e",
    "docs/operational/TRANSFORMATION_DIFFERENCE_BRIDGE_V1.md":
        "01031a1d49bfda5c197511924691ad44dd7aa597f280b3e826388bb16bc9051d",
}


class IdentityMismatch(RuntimeError):
    pass


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def compute_runtime_identity() -> dict[str, object]:
    for relative, expected in FROZEN_SOURCE_HASHES.items():
        actual = _sha_file(ROOT / relative)
        if actual != expected:
            raise IdentityMismatch(f"frozen authority hash mismatch: {relative}")

    actual_contract = _sha_file(ROOT / CONTRACT_PATH)
    if actual_contract != CONTRACT_SHA256:
        raise IdentityMismatch("completion contract hash mismatch")

    source_paths = {
        *FROZEN_SOURCE_HASHES,
        CONTRACT_PATH,
    }
    for package in (
        "src", "m_machine", "experimental_m_runtime_v2",
        "operational_m", "independent_runtime",
    ):
        source_paths.update(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / package).rglob("*.py")
        )
    file_hashes = {
        relative: _sha_file(ROOT / relative)
        for relative in sorted(source_paths)
    }

    executable = Path(sys.executable).resolve()
    executable_hash = _sha_file(executable)
    manifest = {
        "format": "phi-independent-runtime-identity-v1",
        "python_executable_sha256": executable_hash,
        "sources": file_hashes,
    }
    return {
        **manifest,
        "runtime_sha256": sha256(canonical_json(manifest)).hexdigest(),
    }

