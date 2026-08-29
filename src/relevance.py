
"""
PHI-INFINITY
Consequence-Preserving Fragment Controller

Fundamental rule:

    every represented real difference is preserved.

No numerical magnitude threshold is allowed to become an
ontological relevance rule.

For every accessible exterior fragment:

    - represented consequence
        -> preserve and compose;

    - real source present but consequence below current
      numerical representation
        -> preserve the unresolved distinguishability fact;

    - unresolved consequence
        -> require more access.

All accessible represented consequences are composed before
the focal continuation is evaluated.

Author: Massimiliano Brighindi (2026)
"""

from dataclasses import dataclass

import numpy as np

from src.core import PhiSubstrateEngine

from src.boundary import (
    BoundaryEffectReceipt,
    boundary_receipt_from_parent,
    combine_boundary_receipts,
)


# ============================================================
# CONSEQUENCE DECISION
# ============================================================

@dataclass(frozen=True)
class ConsequenceDecision:

    status: str

    represented_magnitude: float

    source_present: bool

    reason: str


# ============================================================
# ENGINE COPY
# ============================================================

def clone_engine(
    engine,
):
    """
    Exact runtime-state copy.

    No new dynamics are introduced.
    """

    clone = PhiSubstrateEngine(
        n_nodes=
            engine.N,

        sigma=
            engine.sigma,

        alpha=
            engine.alpha,

        beta=
            engine.beta,

        lmbda=
            engine.lmbda,

        gamma=
            engine.gamma,

        mu=
            engine.mu,

        eta=
            engine.eta,

        seed=
            1,
    )

    clone.pos = np.copy(
        engine.pos
    )

    clone.S = np.copy(
        engine.S
    )

    clone.R = np.copy(
        engine.R
    )

    return clone


# ============================================================
# SAME REAL RELATION — BOTH DIRECTIONS
# ============================================================

def bidirectional_exchange(
    parent_engine,
    focal_indices,
    other_indices,
):
    """
    incoming:
        consequences produced outside that reach the focal fragment

    outgoing:
        consequences produced by the focal fragment that reach outside
    """

    incoming = (
        boundary_receipt_from_parent(
            parent_engine,
            focal_indices,
            other_indices,
        )
    )

    outgoing = (
        boundary_receipt_from_parent(
            parent_engine,
            other_indices,
            focal_indices,
        )
    )

    return {
        "incoming":
            incoming,

        "outgoing":
            outgoing,
    }


# ============================================================
# REPRESENTED MAGNITUDE
# ============================================================

def _receipt_magnitude(
    receipt,
):

    arrays = [
        np.asarray(
            receipt.flow_e,
            dtype=np.float64,
        ),

        np.asarray(
            receipt.flow_r,
            dtype=np.float64,
        ),

        np.asarray(
            receipt.geometry,
            dtype=np.float64,
        ),

        np.asarray(
            receipt.coupling_mass,
            dtype=np.float64,
        ),
    ]

    maxima = [
        float(
            np.max(
                np.abs(
                    array
                )
            )
        )
        if array.size
        else 0.0
        for array
        in arrays
    ]

    return max(
        maxima,
        default=0.0,
    )


# ============================================================
# CONSEQUENCE PRESERVATION
# ============================================================

def assess_boundary_consequence(
    candidate_receipt,
    source_present=True,
):
    """
    No significance threshold is applied.

    A represented non-zero consequence is preserved regardless
    of magnitude.

    If a real exterior source is known to exist but the current
    floating-point representation produces zero, the source is
    NOT declared irrelevant.

    It is explicitly marked as below current numerical resolution.
    """

    if not candidate_receipt.resolved:

        return ConsequenceDecision(
            status=
                "REQUIRE_MORE_ACCESS",

            represented_magnitude=
                float("nan"),

            source_present=
                bool(
                    source_present
                ),

            reason=
                (
                    "The exterior consequence is unresolved "
                    "and is not replaced by zero."
                ),
        )


    magnitude = (
        _receipt_magnitude(
            candidate_receipt
        )
    )


    # ========================================================
    # REAL SOURCE PRESENT
    # ========================================================

    if source_present:

        if magnitude == 0.0:

            return ConsequenceDecision(
                status=
                    (
                        "PRESERVE_BELOW_CURRENT_"
                        "NUMERICAL_RESOLUTION"
                    ),

                represented_magnitude=
                    0.0,

                source_present=
                    True,

                reason=
                    (
                        "A real exterior source is present, "
                        "but its consequence is not numerically "
                        "distinguishable in the current "
                        "representation. It is not declared "
                        "irrelevant."
                    ),
            )


        return ConsequenceDecision(
            status=
                "PROPAGATE_REPRESENTED_CONSEQUENCE",

            represented_magnitude=
                magnitude,

            source_present=
                True,

            reason=
                (
                    "The represented exterior consequence is "
                    "preserved regardless of magnitude."
                ),
        )


    # ========================================================
    # NO SOURCE MATERIALIZED IN THIS RESOLVED SCOPE
    #
    # This is NOT a statement that nothing exists outside.
    # ========================================================

    return ConsequenceDecision(
        status=
            "NO_SOURCE_IN_THIS_RESOLVED_SCOPE",

        represented_magnitude=
            magnitude,

        source_present=
            False,

        reason=
            (
                "No exterior source was supplied for this "
                "resolved computational scope. This is not "
                "a claim about the absence of surrounding reality."
            ),
    )


# ============================================================
# BACKWARD-COMPATIBLE ENTRY POINT
# ============================================================

def assess_boundary_relevance(
    local_engine,
    candidate_receipt,
    context_receipt=None,
    cluster_indices=None,
    tolerance=None,
    source_present=True,
):
    """
    Compatibility wrapper for the previous API.

    IMPORTANT:

        tolerance is intentionally ignored.

    A numerical tolerance may describe computational
    distinguishability, but it must never determine whether
    a real consequence exists.
    """

    return assess_boundary_consequence(
        candidate_receipt=
            candidate_receipt,

        source_present=
            source_present,
    )


# ============================================================
# COMPOSE ALL ACCESSIBLE CONSEQUENCES
# ============================================================

def compose_accessible_consequences(
    receipts,
):
    """
    Preserve composition.

    No consequence is removed because it is individually small.

    If even one required consequence is unresolved, the aggregate
    remains unresolved.
    """

    receipts = list(
        receipts
    )

    if not receipts:

        raise ValueError(
            "At least one accessible consequence is required."
        )


    if any(
        not receipt.resolved
        for receipt
        in receipts
    ):

        n_local = len(
            np.asarray(
                receipts[
                    0
                ].flow_e
            )
        )

        return (
            BoundaryEffectReceipt
            .unresolved(
                n_local
            )
        )


    return (
        combine_boundary_receipts(
            *receipts
        )
    )


# ============================================================
# SCAN ACCESSIBLE SURROUNDINGS
# ============================================================

def scan_accessible_environment(
    parent_engine,
    focal_indices,
    context_indices=None,
    candidate_indices=None,
    tolerance=None,
):
    """
    Inspect the currently accessible surrounding fragments.

    NO branch is stopped because its consequence is small.

    Every represented incoming consequence is retained in the
    aggregate.

    A branch that numerically collapses to zero while a real source
    is present remains explicitly represented as below the current
    numerical resolution.

    tolerance is accepted only for backward API compatibility
    and is intentionally unused.
    """

    focal_indices = list(
        focal_indices
    )

    focal_set = set(
        focal_indices
    )


    if context_indices is None:

        context_indices = []

    else:

        context_indices = list(
            context_indices
        )


    context_set = set(
        context_indices
    )


    if candidate_indices is None:

        candidate_indices = [
            index
            for index
            in range(
                parent_engine.N
            )
            if (
                index
                not in focal_set
                and
                index
                not in context_set
            )
        ]

    else:

        candidate_indices = list(
            candidate_indices
        )


    # ========================================================
    # ALREADY ACCESSIBLE CONTEXT
    # ========================================================

    if context_indices:

        context_receipt = (
            boundary_receipt_from_parent(
                parent_engine,
                focal_indices,
                context_indices,
            )
        )

    else:

        # ----------------------------------------------------
        # Arithmetic identity only.
        #
        # NOT an ontological claim that reality outside is zero.
        # ----------------------------------------------------

        context_receipt = (
            BoundaryEffectReceipt
            .resolved_zero(
                len(
                    focal_indices
                )
            )
        )


    branches = []

    incoming_receipts = [
        context_receipt
    ]


    # ========================================================
    # EVERY ACCESSIBLE SOURCE IS PRESERVED
    # ========================================================

    for candidate_index in (
        candidate_indices
    ):

        exchange = (
            bidirectional_exchange(
                parent_engine,
                focal_indices,
                [
                    candidate_index
                ],
            )
        )


        decision = (
            assess_boundary_consequence(
                exchange[
                    "incoming"
                ],
                source_present=True,
            )
        )


        incoming_receipts.append(
            exchange[
                "incoming"
            ]
        )


        branches.append(
            {
                "candidate_index":
                    candidate_index,

                "decision":
                    decision,

                "incoming":
                    exchange[
                        "incoming"
                    ],

                "outgoing":
                    exchange[
                        "outgoing"
                    ],
            }
        )


    # ========================================================
    # ALL REPRESENTED CONSEQUENCES ARE COMPOSED
    # BEFORE THE CONTINUATION IS EVALUATED.
    # ========================================================

    aggregate_incoming = (
        compose_accessible_consequences(
            incoming_receipts
        )
    )


    return {
        "branches":
            branches,

        "aggregate_incoming":
            aggregate_incoming,
    }
