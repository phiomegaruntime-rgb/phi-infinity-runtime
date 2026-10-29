import hashlib
from dataclasses import fields
from pathlib import Path

import pytest

from m_machine.boot import verify_authoritative_boot
from m_machine.continuity_structure import (
    AccessDiscrimination,
    CONTINUITY_RULE_AUTHORITY_HASH,
    CONTINUITY_RULE_AUTHORITY_RANGE,
    CONTINUITY_RULE_ID,
    CONTINUITY_RULE_SEMANTIC_HASH,
    CONTINUITY_RULE_SEMANTIC_SPECIFICATION,
    CONTINUITY_RULE_SOURCE,
    ContinuationPath,
    ContinuityEvidence,
    ContinuityOutcome,
    evaluate_continuity_structure,
    semantic_hash,
)


ROOT = Path(__file__).resolve().parents[1]


def _evidence(paths, *, access=AccessDiscrimination.COMPLETE):
    return ContinuityEvidence(
        prior_genealogy_ids=("prior-1", "prior-2"),
        continuation_paths=tuple(paths),
        access_discrimination=access,
        evidence_receipt_ids=("receipt:continuity-1",),
        provenance=("provenance:continuity-1",),
        ancestry=("ancestry:continuity-1",),
    )


def _path(
    continuation_id,
    predecessor="prior-1",
    continuation_class="class-1",
):
    return ContinuationPath(
        continuation_id=continuation_id,
        predecessor_genealogy_id=predecessor,
        successor_configuration_id="successor-1",
        continuation_class_id=continuation_class,
    )


def test_derived_rule_has_own_authority_and_preserves_frozen_boot():
    path = ROOT / CONTINUITY_RULE_SOURCE
    start, end = CONTINUITY_RULE_AUTHORITY_RANGE
    lines = path.read_bytes().splitlines(keepends=True)
    actual = hashlib.sha256(b"".join(lines[start - 1 : end])).hexdigest()
    assert actual == CONTINUITY_RULE_AUTHORITY_HASH
    assert semantic_hash(CONTINUITY_RULE_SEMANTIC_SPECIFICATION) == (
        CONTINUITY_RULE_SEMANTIC_HASH
    )
    assert CONTINUITY_RULE_ID.startswith("M_RULE_")
    assert verify_authoritative_boot(ROOT).mother_mechanics_sha256 == (
        "0cea8129245b212c04fa776bdc1b718fabf50998a9635e1e06716504fc410f7b"
    )


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        (
            (_path("continuation-1"),),
            ContinuityOutcome.CONTINUOUS_TRANSFORMATION,
        ),
        (
            (),
            ContinuityOutcome.CONTINUITY_CEASED,
        ),
        (
            (
                _path("continuation-1", continuation_class="class-1"),
                _path("continuation-2", continuation_class="class-2"),
            ),
            ContinuityOutcome.BRANCHED_OR_NON_UNIQUE_IDENTITY,
        ),
        (
            (
                _path("continuation-1", predecessor="prior-1"),
                _path("continuation-2", predecessor="prior-2"),
            ),
            ContinuityOutcome.FUSED_OR_COMPOSITE_CONTINUITY,
        ),
    ],
)
def test_complete_discriminating_genealogy_selects_only_declared_outcome(
    paths, expected
):
    result = evaluate_continuity_structure(_evidence(paths), repository_root=ROOT)
    assert result.decision == "ALLOW"
    assert result.outcome == expected
    assert result.receipt.status == "DERIVED_M"
    assert result.genealogy is not None
    assert result.genealogy.rule_id == CONTINUITY_RULE_ID


def test_insufficient_access_is_only_unresolved():
    result = evaluate_continuity_structure(
        _evidence(
            (_path("continuation-1"),),
            access=AccessDiscrimination.INSUFFICIENT,
        ),
        repository_root=ROOT,
    )
    assert result.decision == "UNRESOLVED"
    assert result.outcome == ContinuityOutcome.UNRESOLVED
    assert result.genealogy is None
    assert result.receipt.status == "UNRESOLVED"


def test_missing_access_cannot_be_converted_to_cessation():
    result = evaluate_continuity_structure(
        _evidence((), access=AccessDiscrimination.INSUFFICIENT),
        repository_root=ROOT,
    )
    assert result.decision == "UNRESOLVED"
    assert result.outcome == ContinuityOutcome.UNRESOLVED


def test_human_coding_and_forbidden_generative_criteria_are_not_rule_inputs():
    names = {field.name for field in fields(ContinuityEvidence)}
    names.update(field.name for field in fields(ContinuationPath))
    for forbidden in (
        "human_name",
        "label",
        "percentage",
        "similarity",
        "form",
        "function",
        "threshold",
        "score",
    ):
        assert forbidden not in names

    first = evaluate_continuity_structure(
        _evidence((_path("continuation-1"),)), repository_root=ROOT
    )
    second = evaluate_continuity_structure(
        _evidence((_path("continuation-1"),)), repository_root=ROOT
    )
    assert first.outcome == second.outcome
    assert first.receipt.receipt_id == second.receipt.receipt_id


@pytest.mark.parametrize(
    "bad_paths",
    [
        (_path("continuation-1", predecessor="unknown"),),
        (
            _path("continuation-1"),
            _path("continuation-1", continuation_class="class-2"),
        ),
        (
            ContinuationPath(
                continuation_id="continuation-1",
                predecessor_genealogy_id="prior-1",
                successor_configuration_id="",
                continuation_class_id="class-1",
            ),
        ),
    ],
)
def test_malformed_genealogy_is_blocked_not_repaired(bad_paths):
    result = evaluate_continuity_structure(_evidence(bad_paths), repository_root=ROOT)
    assert result.decision == "BLOCK"
    assert result.outcome is None
    assert result.receipt.status == "BLOCKED_EXTERNAL"