"""Frozen conceptual authority for the independent experimental runtime v2."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from .model import FragmentRef


RUNTIME_ID = "PHI_EXPERIMENTAL_FRAGMENT_RUNTIME_V2"
RUNTIME_VERSION = "1.0.0-closed-fragment-admission"
AUTHORITY_SOURCE = "experimental_m_runtime_v2/AUTHORITY.md"

SEMANTIC_FORMULA = "\n".join(
    (
        "EVERY_SEMANTICALLY_RELEVANT_VALUE_IS_A_FRAGMENT",
        "NO_SEMANTICALLY_USED_VALUE_IS_EXTERNAL_TO_THE_CLOSED_GRAPH",
        "INFINITO_IS_THE_ROOT_FRAGMENT",
        "UNSUPPORTED_FALSE_SUFFICIENCY_REOPENS",
        "CLOSURE_CANNOT_EXCEED_SUPPORTED_GENEALOGY",
        "ANTI_FALSE_SUFFICIENCY_IS_ITSELF_A_VERIFIED_FRAGMENT",
        "ONLY_ONE_PUBLIC_ADMISSION_BOUNDARY_MAY_EMIT_ALLOW",
        "INPUT_AND_OUTPUT_CLOSURE_ARE_BOTH_REQUIRED",
    )
)

EXPECTED_AUTHORITY_SHA256 = (
    "521ae0e3867206e166d5694894e8daf3c623a1a2858676f18fd0ba92117a9af8"
)
EXPECTED_SEMANTIC_SHA256 = (
    "887e3f0e68808fb6228e0a333ba78fddbffeca370d2dcd7286c1a6bfacd15e62"
)
EXPECTED_RUNTIME_SHA256 = (
    "29de4313915cf47dc7afc6a21acc751cc707d8b445547dc2262eb9ce0da40196"
)

MACHINE_FRAGMENT = FragmentRef("fragment:operator:m-only-v2")
PATH_FRAGMENTS = (
    FragmentRef("fragment:solution:m-only"),
    FragmentRef("fragment:freeze:solution"),
    FragmentRef("fragment:path:exact"),
    FragmentRef("fragment:formalization"),
    FragmentRef("fragment:rule:anti-false-sufficiency"),
)
ANTI_FALSE_SUFFICIENCY_RULE = PATH_FRAGMENTS[-1]


@dataclass(frozen=True, slots=True)
class FrozenAuthority:
    authority_fragment: FragmentRef
    authority_hash_fragment: FragmentRef
    semantic_hash_fragment: FragmentRef
    runtime_hash_fragment: FragmentRef
    freeze_receipt_fragment: FragmentRef
    machine_fragment: FragmentRef
    path_fragments: tuple[FragmentRef, ...]
    anti_false_sufficiency_rule: FragmentRef


class AuthorityError(RuntimeError):
    """Raised when v2 authority is missing, pending, or inconsistent."""


def _runtime_hash(authority_hash: str, semantic_hash: str) -> str:
    payload = f"{RUNTIME_ID}:{RUNTIME_VERSION}:{authority_hash}:{semantic_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_frozen_authority(repository_root: str | Path) -> FrozenAuthority:
    root = Path(repository_root).resolve()
    source = root / AUTHORITY_SOURCE
    if not source.is_file():
        raise AuthorityError(f"Missing v2 authority source: {AUTHORITY_SOURCE}")
    if "PENDING" in (
        EXPECTED_AUTHORITY_SHA256,
        EXPECTED_SEMANTIC_SHA256,
        EXPECTED_RUNTIME_SHA256,
    ):
        raise AuthorityError("v2 authority hashes are still pending.")

    actual_authority = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual_authority != EXPECTED_AUTHORITY_SHA256:
        raise AuthorityError("v2 authority source hash mismatch.")

    actual_semantic = hashlib.sha256(
        SEMANTIC_FORMULA.encode("utf-8")
    ).hexdigest()
    if actual_semantic != EXPECTED_SEMANTIC_SHA256:
        raise AuthorityError("v2 semantic hash mismatch.")

    actual_runtime = _runtime_hash(actual_authority, actual_semantic)
    if actual_runtime != EXPECTED_RUNTIME_SHA256:
        raise AuthorityError("v2 runtime identity hash mismatch.")

    authority_fragment = FragmentRef(
        f"fragment:authority:source:{actual_authority}"
    )
    authority_hash_fragment = FragmentRef(
        f"fragment:authority:sha256:{actual_authority}"
    )
    semantic_hash_fragment = FragmentRef(
        f"fragment:semantic:sha256:{actual_semantic}"
    )
    runtime_hash_fragment = FragmentRef(
        f"fragment:runtime:sha256:{actual_runtime}"
    )
    freeze_receipt_fragment = FragmentRef(
        f"fragment:receipt:freeze:{actual_authority}:{actual_semantic}"
    )
    return FrozenAuthority(
        authority_fragment=authority_fragment,
        authority_hash_fragment=authority_hash_fragment,
        semantic_hash_fragment=semantic_hash_fragment,
        runtime_hash_fragment=runtime_hash_fragment,
        freeze_receipt_fragment=freeze_receipt_fragment,
        machine_fragment=MACHINE_FRAGMENT,
        path_fragments=PATH_FRAGMENTS,
        anti_false_sufficiency_rule=ANTI_FALSE_SUFFICIENCY_RULE,
    )