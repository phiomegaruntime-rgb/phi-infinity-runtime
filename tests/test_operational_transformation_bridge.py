import hashlib
from pathlib import Path

import pytest

from m_machine import (
    ConstructorPolicy,
    PropositionType,
    MExecutionMachine,
    default_mechanical_rule_registry,
    default_proposition_type_registry,
)
from operational_m import (
    AUTHORITY_HASH,
    AUTHORITY_SOURCE,
    BridgeResult,
    OperationalAuthorityError,
    OperationalPropositionType,
    OptInRequired,
    TransformationGrounding,
    create_operational_bridge,
    verify_operational_authority,
)


ROOT = Path(__file__).resolve().parents[1]

_FROZEN_MODULE_HASHES = {
    "m_machine/guardrail.py": (
        "dcc8c100f557f6a1dd5cf5b880d2a1e687fcedc0680bdbe521732efabd9fc33e"
    ),
    "m_machine/mechanical_propositions.py": (
        "06e2625b2a5f2dd62329c4fb0a13c218ae18f39e85debfa097aa8075736d4ede"
    ),
    "m_machine/mechanical_rules.py": (
        "2af4e4dfceef1d544d399eeb51a00b446d001ce3f3028774a64ea1d448040252"
    ),
    "m_machine/grounding.py": (
        "7ed2e1b2462c9eb2321474fa89e160297b7cd8a8686c542947c106f0713a5b37"
    ),
    "m_machine/proof_kernel.py": (
        "50c93d5f08acda93e51e866cb27cb0a7386fba2e82b0b4998e85363aa7f85162"
    ),
    "m_machine/boot.py": (
        "c04c34da18ff55842427eaa24376c243ed4303f9cbcf46ed2f8d5cedd78dff86"
    ),
    "m_machine/__init__.py": (
        "2ee05ab8941440f8a5c560790bde34da354f94725d2667d9bfbbb0fd3110dcf4"
    ),
}


def _scope() -> tuple[tuple[str, str], ...]:
    return (
        ("access_snapshot", "access-1"),
        ("mechanical_configuration", "configuration-1"),
        ("field_context", "field-1"),
        ("scale", "scale-1"),
        ("genealogy", "genealogy-1"),
        ("execution_lineage", "execution-1"),
    )


def _grounding() -> TransformationGrounding:
    return TransformationGrounding(
        grounding_id="grounding-1",
        authority="external:attestation-1",
        provenance=("receipt:grounding-1", "attestation:external-1"),
        ancestry=("trust-root:root-1", "contract:contract-1"),
    )


def test_frozen_modules_remain_byte_identical_with_extension_present():
    for path, expected in _FROZEN_MODULE_HASHES.items():
        actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        assert actual == expected


def test_extension_does_not_change_frozen_counts_policies_or_raw_behavior():
    assert len(tuple(PropositionType)) == 6
    assert not hasattr(PropositionType, "REAL_TRANSFORMATION_EXISTS")
    assert default_proposition_type_registry(ROOT).type_count == 6
    assert (
        default_proposition_type_registry(ROOT)
        .get(PropositionType.REAL_DIFFERENCE_EXISTS)
        .constructor_policy
        == ConstructorPolicy.NO_CONSTRUCTOR_CURRENTLY_AUTHORIZED
    )
    assert default_mechanical_rule_registry(ROOT).mechanical_rule_count == 1
    assert MExecutionMachine().raw_fireable_positive_mechanical_rule_count == 0


def test_extension_requires_explicit_opt_in():
    with pytest.raises(OptInRequired):
        create_operational_bridge(repository_root=ROOT)


def test_authority_is_owned_and_verified_by_the_operational_extension():
    actual = verify_operational_authority(ROOT)
    assert actual == AUTHORITY_HASH
    assert AUTHORITY_SOURCE.startswith("docs/operational/")


def test_valid_grounding_produces_a_non_promoted_difference_candidate():
    bridge = create_operational_bridge(opt_in=True, repository_root=ROOT)
    result = bridge.derive(
        transformation_scope=_scope(),
        grounding=_grounding(),
        premise_receipt_ids=("receipt:grounding-1",),
    )
    assert result.decision == "CANDIDATE"
    assert result.candidate is not None
    assert result.receipt is not None
    assert (
        result.candidate.proposition_type
        == OperationalPropositionType.REAL_DIFFERENCE_EXISTS
    )
    assert result.candidate.scope == _scope()
    assert result.candidate.grounding_id == "grounding-1"
    assert result.candidate.provenance == _grounding().provenance
    assert result.candidate.ancestry == _grounding().ancestry
    assert result.candidate.auto_promoted is False
    assert result.receipt.status == "DERIVED_OPERATIONAL"


@pytest.mark.parametrize(
    "scope, grounding, receipts",
    [
        (_scope()[:-1], _grounding(), ("receipt:grounding-1",)),
        (_scope(), None, ("receipt:grounding-1",)),
        (_scope(), _grounding(), ()),
        (
            _scope(),
            TransformationGrounding(
                grounding_id="grounding-1",
                authority="external:attestation-1",
                provenance=("receipt:grounding-1",),
                ancestry=(),
            ),
            ("receipt:grounding-1",),
        ),
    ],
)
def test_insufficient_grounding_or_scope_is_unresolved(scope, grounding, receipts):
    bridge = create_operational_bridge(opt_in=True, repository_root=ROOT)
    result = bridge.derive(
        transformation_scope=scope,
        grounding=grounding,
        premise_receipt_ids=receipts,
    )
    assert result.decision == "UNRESOLVED"
    assert result.candidate is None
    assert result.receipt is None


@pytest.mark.parametrize(
    "grounding",
    [
        TransformationGrounding(
            grounding_id="grounding-1",
            authority="model:guess",
            provenance=("receipt:grounding-1",),
            ancestry=("trust-root:root-1",),
        ),
        TransformationGrounding(
            grounding_id="grounding-1",
            authority="external:attestation-1",
            provenance=("label:changed",),
            ancestry=("trust-root:root-1",),
        ),
        TransformationGrounding(
            grounding_id="grounding-1",
            authority="external:attestation-1",
            provenance=("receipt:grounding-1",),
            ancestry=("model:plausible",),
        ),
    ],
)
def test_invalid_authority_or_provenance_is_blocked(grounding):
    bridge = create_operational_bridge(opt_in=True, repository_root=ROOT)
    result = bridge.derive(
        transformation_scope=_scope(),
        grounding=grounding,
        premise_receipt_ids=("receipt:grounding-1",),
    )
    assert result.decision == "BLOCK"
    assert result.candidate is None


def test_pair_scope_and_label_only_change_do_not_establish_transformation():
    bridge = create_operational_bridge(opt_in=True, repository_root=ROOT)
    pair_scope = _scope() + (("pair_scope", "pair-1"),)
    result = bridge.derive(
        transformation_scope=pair_scope,
        grounding=None,
        premise_receipt_ids=(),
    )
    assert result.decision == "UNRESOLVED"


def test_identical_inputs_are_deterministic():
    bridge = create_operational_bridge(opt_in=True, repository_root=ROOT)
    first = bridge.derive(
        transformation_scope=_scope(),
        grounding=_grounding(),
        premise_receipt_ids=("receipt:grounding-1",),
    )
    second = bridge.derive(
        transformation_scope=_scope(),
        grounding=_grounding(),
        premise_receipt_ids=("receipt:grounding-1",),
    )
    assert isinstance(first, BridgeResult)
    assert first == second