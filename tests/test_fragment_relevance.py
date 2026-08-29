
import numpy as np

from src.core import PhiSubstrateEngine

from src.boundary import (
    BoundaryEffectReceipt,
    boundary_receipt_from_parent,
)

from src.relevance import (
    assess_boundary_relevance,
    bidirectional_exchange,
    scan_accessible_environment,
)


# ============================================================
# 1. A REAL ZERO EFFECT DOES NOT OPEN A NEW BRANCH
# ============================================================

def test_resolved_zero_stops_for_current_transformation():

    local = PhiSubstrateEngine(
        n_nodes=2,
        seed=1,
    )

    zero = (
        BoundaryEffectReceipt
        .resolved_zero(
            local.N
        )
    )

    result = (
        assess_boundary_relevance(
            local_engine=
                local,

            candidate_receipt=
                zero,

            context_receipt=
                zero,

            tolerance=
                1e-12,
        )
    )

    assert (
        result.status
        ==
        "STOP_EXPANSION_THIS_TRANSFORMATION"
    )

    assert (
        result.state_delta
        == 0.0
    )

    assert (
        result.membrane_delta
        == 0.0
    )


# ============================================================
# 2. AN EXTERNAL DIFFERENCE THAT CHANGES THE FRAGMENT
#    MUST BE FOLLOWED
# ============================================================

def test_external_difference_that_changes_continuation_expands():

    parent = PhiSubstrateEngine(
        n_nodes=3,
        seed=1,
    )

    parent.pos = np.array(
        [
            [0.00, 0.00],
            [0.10, 0.00],
            [0.20, 0.05],
        ],
        dtype=np.float64,
    )

    parent.S = np.array(
        [
            [2.0, 2.0, 1.0],
            [2.1, 1.9, 1.0],
            [5.0, 1.0, 0.7],
        ],
        dtype=np.float64,
    )

    parent.R[:] = 0.0


    local = PhiSubstrateEngine(
        n_nodes=2,
        sigma=parent.sigma,
        alpha=parent.alpha,
        beta=parent.beta,
        lmbda=parent.lmbda,
        gamma=parent.gamma,
        mu=parent.mu,
        eta=parent.eta,
        seed=1,
    )

    local.pos = np.copy(
        parent.pos[
            [0, 1]
        ]
    )

    local.S = np.copy(
        parent.S[
            [0, 1]
        ]
    )

    local.R = np.copy(
        parent.R[
            [0, 1]
        ]
    )


    candidate = (
        boundary_receipt_from_parent(
            parent,
            [
                0,
                1,
            ],
            [
                2,
            ],
        )
    )


    result = (
        assess_boundary_relevance(
            local_engine=
                local,

            candidate_receipt=
                candidate,

            context_receipt=
                BoundaryEffectReceipt
                .resolved_zero(
                    local.N
                ),

            tolerance=
                1e-12,
        )
    )


    assert (
        result.status
        ==
        "EXPAND_THIS_TRANSFORMATION"
    )


    assert (
        result.state_delta
        > 0.0

        or

        result.membrane_delta
        > 0.0

        or

        result.membrane_status_changed
    )


# ============================================================
# 3. UNKNOWN EXTERIOR DOES NOT BECOME ZERO
# ============================================================

def test_unresolved_difference_requires_more_access():

    local = PhiSubstrateEngine(
        n_nodes=2,
        seed=2,
    )


    result = (
        assess_boundary_relevance(
            local_engine=
                local,

            candidate_receipt=
                BoundaryEffectReceipt
                .unresolved(
                    local.N
                ),

            context_receipt=
                BoundaryEffectReceipt
                .resolved_zero(
                    local.N
                ),
        )
    )


    assert (
        result.status
        ==
        "REQUIRE_MORE_ACCESS"
    )


# ============================================================
# 4. THE SAME REAL RELATION IS FOLLOWED IN BOTH DIRECTIONS
# ============================================================

def test_fragment_receives_and_also_produces_consequences():

    parent = PhiSubstrateEngine(
        n_nodes=3,
        seed=5,
    )


    parent.pos = np.array(
        [
            [0.00, 0.00],
            [0.10, 0.00],
            [0.25, 0.05],
        ],
        dtype=np.float64,
    )


    exchange = (
        bidirectional_exchange(
            parent,
            focal_indices=[
                0,
                1,
            ],
            other_indices=[
                2,
            ],
        )
    )


    incoming = (
        exchange[
            "incoming"
        ]
    )

    outgoing = (
        exchange[
            "outgoing"
        ]
    )


    assert (
        incoming.resolved
        is True
    )

    assert (
        outgoing.resolved
        is True
    )


    assert (
        incoming.flow_e.shape
        ==
        (2,)
    )

    assert (
        outgoing.flow_e.shape
        ==
        (1,)
    )


    assert (
        incoming.coupling_mass.shape
        ==
        (2,)
    )

    assert (
        outgoing.coupling_mass.shape
        ==
        (1,)
    )


    assert (
        np.any(
            incoming.coupling_mass
            > 0.0
        )
    )

    assert (
        np.any(
            outgoing.coupling_mass
            > 0.0
        )
    )


# ============================================================
# 5. AUTOMATIC SCAN OF CURRENTLY ACCESSIBLE SURROUNDINGS
# ============================================================

def test_accessible_environment_scan_opens_only_relevant_branches():

    parent = PhiSubstrateEngine(
        n_nodes=4,
        seed=11,
    )


    parent.pos = np.array(
        [
            [0.00, 0.00],
            [0.10, 0.00],

            # close surrounding fragment
            [0.20, 0.02],

            # effectively remote surrounding fragment
            [100.0, 100.0],
        ],
        dtype=np.float64,
    )


    results = (
        scan_accessible_environment(
            parent_engine=
                parent,

            focal_indices=[
                0,
                1,
            ],

            candidate_indices=[
                2,
                3,
            ],

            tolerance=
                1e-12,
        )
    )


    by_index = {
        item[
            "candidate_index"
        ]:
            item[
                "decision"
            ].status
        for item
        in results
    }


    assert (
        by_index[
            2
        ]
        ==
        "EXPAND_THIS_TRANSFORMATION"
    )


    assert (
        by_index[
            3
        ]
        ==
        "STOP_EXPANSION_THIS_TRANSFORMATION"
    )
