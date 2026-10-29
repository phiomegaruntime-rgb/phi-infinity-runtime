"""Categorical all-fragment foundation and its fail-closed admission gate."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .authority import (
    FOUNDATION_FORMULA,
    FOUNDATION_SEMANTIC_HASH,
    FOUNDATION_VERSION,
)
from .model import (
    BoundaryVisibility,
    CategoricalFoundation,
    Decision,
    ExperimentalProposal,
    Fragment,
    FragmentClaim,
    Stage,
)


@dataclass(frozen=True, slots=True)
class CategoricalFoundationResult:
    decision: Decision
    stage: Stage
    reason: str


def semantic_hash(formula: str = FOUNDATION_FORMULA) -> str:
    return hashlib.sha256(formula.encode("utf-8")).hexdigest()


def validate_categorical_foundation(
    proposal: ExperimentalProposal,
) -> CategoricalFoundationResult:
    foundation = proposal.categorical_foundation
    if foundation is None:
        return _block("Categorical all-fragment foundation is missing.")
    if not isinstance(foundation, CategoricalFoundation):
        return _block("Categorical foundation is not typed.")
    if foundation.version != FOUNDATION_VERSION:
        return _block("Categorical foundation version is not authoritative.")
    if foundation.formula != FOUNDATION_FORMULA:
        return _block("Categorical foundation formula is not frozen.")
    if foundation.semantic_hash != FOUNDATION_SEMANTIC_HASH:
        return _block("Categorical foundation semantic hash is not authoritative.")
    if semantic_hash(foundation.formula) != foundation.semantic_hash:
        return _block("Categorical foundation semantic hash does not verify.")

    fragments = {}
    for fragment in proposal.fragments:
        if not isinstance(fragment, Fragment):
            return _block("Every supplied term must be represented as a Fragment.")
        if fragment.fragment_id in fragments:
            return _block("Fragment identities are not unique.")
        fragments[fragment.fragment_id] = fragment
    if not fragments:
        return _block("No fragment representation was supplied.")

    if proposal.unrepresented_terms:
        return _reopen(
            "An unrepresented term or meta-operator cannot be accepted as "
            "external to the same fragment mechanics."
        )

    infinito = fragments.get(foundation.infinito_fragment_id)
    if infinito is None:
        return _block("Infinito is not represented as a fragment.")
    if (
        infinito.represented_kind != "INFINITO"
        or infinito.boundary_visibility != BoundaryVisibility.NOT_VISIBLE
        or not infinito.parent_fragment_ids
    ):
        return _block(
            "Infinito must be a composed fragment with a non-visible boundary."
        )
    if not set(infinito.parent_fragment_ids).issubset(fragments):
        return _block("Infinito references an unavailable component fragment.")

    for fragment in fragments.values():
        if foundation.infinito_fragment_id not in (
            fragment.contained_by_fragment_ids
        ):
            return _reopen(
                "A supplied fragment has no explicit containment in Infinito."
            )

    role_ids = dict(foundation.role_fragment_ids)
    if len(role_ids) != len(foundation.role_fragment_ids):
        return _block("Categorical role identities are not unique.")
    required_roles = {
        "FOUNDATION",
        "M",
        "INFINITO",
        "FORMULA",
        "ALGORITHM",
        "RULE",
        "RUNTIME",
        "VERIFICATION",
    }
    if not required_roles.issubset(role_ids):
        return _block("Self-applicable foundation roles are incomplete.")
    for role, fragment_id in role_ids.items():
        if fragment_id not in fragments:
            return _reopen(
                f"Role {role!r} refers to a non-fragment external term."
            )
    if role_ids["INFINITO"] != foundation.infinito_fragment_id:
        return _block("The Infinito role does not match the foundation anchor.")

    if not foundation.path_fragment_ids:
        return _block("The exact M path has no fragment representation.")
    if len(set(foundation.path_fragment_ids)) != len(
        foundation.path_fragment_ids
    ):
        return _block("Exact path fragment identities are not unique.")
    if not set(foundation.path_fragment_ids).issubset(fragments):
        return _reopen("The exact path contains an unrepresented operation.")

    for claim in proposal.claims:
        if not isinstance(claim, FragmentClaim):
            return _reopen("A claim contains an unrepresented meta-operator.")
        if not all(
            fragment_id in fragments
            for fragment_id in (
                claim.subject_fragment_id,
                claim.relation_fragment_id,
                claim.object_fragment_id,
            )
        ):
            return _reopen(
                "A claim uses a subject, relation, or object outside fragments."
            )
    return CategoricalFoundationResult(
        decision=Decision.ALLOW,
        stage=Stage.CATEGORICAL_FOUNDATION,
        reason="Categorical all-fragment foundation passed.",
    )


def _block(reason: str) -> CategoricalFoundationResult:
    return CategoricalFoundationResult(
        decision=Decision.BLOCK,
        stage=Stage.CATEGORICAL_FOUNDATION,
        reason=reason,
    )


def _reopen(reason: str) -> CategoricalFoundationResult:
    return CategoricalFoundationResult(
        decision=Decision.REOPEN,
        stage=Stage.CATEGORICAL_FOUNDATION,
        reason=reason,
    )