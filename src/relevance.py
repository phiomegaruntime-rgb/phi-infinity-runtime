
"""
PHI-INFINITY
Fragment-Driven Relevance Controller

A fragment does not require reconstruction of every causal
antecedent in reality.

For the current transformation, an accessible external difference
is followed only when it changes a distinguishable continuation of
the focal fragment.

The same field relation is also inspected in the opposite direction:
what reaches the fragment and what the fragment sends back.

No claim is made that a branch which is irrelevant now can never
become relevant later.

Author: Massimiliano Brighindi (2026)
"""

from dataclasses import dataclass

import numpy as np

from src.core import PhiSubstrateEngine

from src.boundary import (
    BoundaryEffectReceipt,
    boundary_receipt_from_parent,
    combine_boundary_receipts,
    step_with_boundary,
    evaluate_cluster_with_boundary,
)


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class RelevanceDecision:

    status: str

    state_delta: float

    membrane_delta: float

    membrane_status_changed: bool

    reason: str


# ============================================================
# ENGINE COPY
# ============================================================

def clone_engine(
    engine,
):
    """
    Exact local runtime copy.

    No new dynamics are introduced.
    """

    clone = PhiSubstrateEngine(
        n_nodes=engine.N,
        sigma=engine.sigma,
        alpha=engine.alpha,
        beta=engine.beta,
        lmbda=engine.lmbda,
        gamma=engine.gamma,
        mu=engine.mu,
        eta=engine.eta,
        seed=1,
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
# BIDIRECTIONAL REAL EXCHANGE
# ============================================================

def bidirectional_exchange(
    parent_engine,
    focal_indices,
    other_indices,
):
    """
    Inspect the same relation in both directions.

    incoming:
        consequences produced by the surrounding fragment
        that reach the focal fragment.

    outgoing:
        consequences produced by the focal fragment
        that reach the surrounding fragment.
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
# DISTINGUISHABILITY
# ============================================================

def _maximum_state_difference(
    engine_a,
    engine_b,
):

    return float(
        max(
            np.max(
                np.abs(
                    engine_a.pos
                    -
                    engine_b.pos
                )
            ),

            np.max(
                np.abs(
                    engine_a.S
                    -
                    engine_b.S
                )
            ),

            np.max(
                np.abs(
                    engine_a.R
                    -
                    engine_b.R
                )
            ),
        )
    )


# ============================================================
# RELEVANCE OF ONE EXTERNAL DIFFERENCE
# ============================================================

def assess_boundary_relevance(
    local_engine,
    candidate_receipt,
    context_receipt=None,
    cluster_indices=None,
    tolerance=1e-12,
):
    """
    Ask only:

        Does this additional exterior difference change the
        next distinguishable continuation of the fragment?

    Comparison:

        already-known context

    versus

        already-known context + candidate exterior effect

    This is a per-transformation decision.

    It never means that a currently irrelevant branch is
    irrelevant forever.
    """

    if context_receipt is None:

        context_receipt = (
            BoundaryEffectReceipt
            .resolved_zero(
                local_engine.N
            )
        )


    # --------------------------------------------------------
    # Unknown outside is not zero.
    # --------------------------------------------------------

    if (
        not context_receipt.resolved
        or
        not candidate_receipt.resolved
    ):

        return RelevanceDecision(
            status=
                "REQUIRE_MORE_ACCESS",

            state_delta=
                float("nan"),

            membrane_delta=
                float("nan"),

            membrane_status_changed=
                False,

            reason=
                (
                    "The exterior consequence required "
                    "for this transformation is not yet "
                    "resolved."
                ),
        )


    if cluster_indices is None:

        cluster_indices = list(
            range(
                local_engine.N
            )
        )


    # ========================================================
    # SAME FRAGMENT, SAME STARTING REALITY
    # ========================================================

    baseline_engine = (
        clone_engine(
            local_engine
        )
    )

    candidate_engine = (
        clone_engine(
            local_engine
        )
    )


    expanded_receipt = (
        combine_boundary_receipts(
            context_receipt,
            candidate_receipt,
        )
    )


    # ========================================================
    # CURRENT MEMBRANE CONSEQUENCE
    # ========================================================

    baseline_membrane = (
        evaluate_cluster_with_boundary(
            baseline_engine,
            cluster_indices,
            context_receipt,
            beta=baseline_engine.beta,
        )
    )

    candidate_membrane = (
        evaluate_cluster_with_boundary(
            candidate_engine,
            cluster_indices,
            expanded_receipt,
            beta=candidate_engine.beta,
        )
    )


    baseline_mc = (
        baseline_membrane[
            "M_C_upper"
        ]
    )

    candidate_mc = (
        candidate_membrane[
            "M_C_upper"
        ]
    )


    membrane_delta = float(
        abs(
            candidate_mc
            -
            baseline_mc
        )
    )


    membrane_status_changed = (
        baseline_membrane[
            "status"
        ]
        !=
        candidate_membrane[
            "status"
        ]
    )


    # ========================================================
    # NEXT TRANSFORMATION
    # ========================================================

    step_with_boundary(
        baseline_engine,
        context_receipt,
    )

    step_with_boundary(
        candidate_engine,
        expanded_receipt,
    )


    state_delta = (
        _maximum_state_difference(
            baseline_engine,
            candidate_engine,
        )
    )


    # ========================================================
    # DECISION
    # ========================================================

    relevant = (
        state_delta
        > tolerance

        or

        membrane_delta
        > tolerance

        or

        membrane_status_changed
    )


    if relevant:

        return RelevanceDecision(
            status=
                "EXPAND_THIS_TRANSFORMATION",

            state_delta=
                state_delta,

            membrane_delta=
                membrane_delta,

            membrane_status_changed=
                membrane_status_changed,

            reason=
                (
                    "The accessible exterior difference "
                    "changes a distinguishable continuation "
                    "of the focal fragment."
                ),
        )


    return RelevanceDecision(
        status=
            "STOP_EXPANSION_THIS_TRANSFORMATION",

        state_delta=
            state_delta,

        membrane_delta=
            membrane_delta,

        membrane_status_changed=
            membrane_status_changed,

        reason=
            (
                "The accessible exterior difference does "
                "not change the fragment's distinguishable "
                "continuation in this transformation."
            ),
    )


# ============================================================
# EXAMINE THE CURRENTLY ACCESSIBLE SURROUNDING FIELD
# ============================================================

def scan_accessible_environment(
    parent_engine,
    focal_indices,
    context_indices=None,
    candidate_indices=None,
    tolerance=1e-12,
):
    """
    Starting from the focal fragment:

        1. preserve already-established surrounding effects;
        2. inspect each additional accessible surrounding fragment;
        3. record what reaches the focal fragment;
        4. record what the focal fragment sends back;
        5. continue only where a difference changes continuation.

    No pre-defined hierarchy is required.
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
            i
            for i
            in range(
                parent_engine.N
            )
            if (
                i not in focal_set
                and
                i not in context_set
            )
        ]

    else:

        candidate_indices = list(
            candidate_indices
        )


    # --------------------------------------------------------
    # Local fragment
    # --------------------------------------------------------

    local_engine = PhiSubstrateEngine(
        n_nodes=len(
            focal_indices
        ),
        sigma=parent_engine.sigma,
        alpha=parent_engine.alpha,
        beta=parent_engine.beta,
        lmbda=parent_engine.lmbda,
        gamma=parent_engine.gamma,
        mu=parent_engine.mu,
        eta=parent_engine.eta,
        seed=1,
    )


    local_engine.pos = np.copy(
        parent_engine.pos[
            focal_indices
        ]
    )

    local_engine.S = np.copy(
        parent_engine.S[
            focal_indices
        ]
    )

    local_engine.R = np.copy(
        parent_engine.R[
            focal_indices
        ]
    )


    # --------------------------------------------------------
    # Already-established surrounding context
    # --------------------------------------------------------

    if context_indices:

        context_receipt = (
            boundary_receipt_from_parent(
                parent_engine,
                focal_indices,
                context_indices,
            )
        )

    else:

        context_receipt = (
            BoundaryEffectReceipt
            .resolved_zero(
                len(
                    focal_indices
                )
            )
        )


    results = []


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
            assess_boundary_relevance(
                local_engine=
                    local_engine,

                candidate_receipt=
                    exchange[
                        "incoming"
                    ],

                context_receipt=
                    context_receipt,

                cluster_indices=
                    list(
                        range(
                            local_engine.N
                        )
                    ),

                tolerance=
                    tolerance,
            )
        )


        results.append(
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


    return results
