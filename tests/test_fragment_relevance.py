
import numpy as np

from src.core import PhiSubstrateEngine

from src.boundary import (
    BoundaryEffectReceipt,
    boundary_receipt_from_parent,
    evaluate_cluster_with_boundary,
)

from src.relevance import (
    assess_boundary_consequence,
    assess_boundary_relevance,
    bidirectional_exchange,
    compose_accessible_consequences,
)


# ============================================================
# 1. COMPUTATIONAL ZERO IS NOT CALLED IRRELEVANT
# ============================================================

def test_computational_zero_is_not_called_irrelevant():

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

            tolerance=
                1e-12,

            source_present=
                False,
        )
    )


    assert (
        result.status
        ==
        "NO_SOURCE_IN_THIS_RESOLVED_SCOPE"
    )


# ============================================================
# 2. TINY REPRESENTED EFFECT MUST SURVIVE
# ============================================================

def test_tiny_represented_consequence_is_propagated_without_threshold():

    local = PhiSubstrateEngine(
        n_nodes=2,
        seed=1,
    )


    tiny = BoundaryEffectReceipt(
        flow_e=
            np.full(
                2,
                1e-15,
            ),

        flow_r=
            np.zeros(
                2,
            ),

        geometry=
            np.zeros(
                (
                    2,
                    2,
                )
            ),

        coupling_mass=
            np.full(
                2,
                1e-15,
            ),

        resolved=
            True,
    )


    result = (
        assess_boundary_relevance(
            local_engine=
                local,

            candidate_receipt=
                tiny,

            # Old threshold deliberately larger
            # than the real consequence.
            tolerance=
                1e-12,

            source_present=
                True,
        )
    )


    assert (
        result.status
        ==
        "PROPAGATE_REPRESENTED_CONSEQUENCE"
    )


    assert (
        0.0
        <
        result.represented_magnitude
        <
        1e-12
    )


# ============================================================
# 3. UNRESOLVED != ZERO
# ============================================================

def test_unresolved_difference_requires_more_access():

    local = PhiSubstrateEngine(
        n_nodes=2,
        seed=2,
    )


    result = (
        assess_boundary_consequence(
            BoundaryEffectReceipt
            .unresolved(
                local.N
            ),

            source_present=
                True,
        )
    )


    assert (
        result.status
        ==
        "REQUIRE_MORE_ACCESS"
    )


# ============================================================
# 4. SAME REAL EXCHANGE IS PRESERVED BOTH WAYS
# ============================================================

def test_real_relation_is_preserved_in_both_directions():

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
            [
                0,
                1,
            ],
            [
                2,
            ],
        )
    )


    assert (
        exchange[
            "incoming"
        ].resolved
    )

    assert (
        exchange[
            "outgoing"
        ].resolved
    )


    assert np.any(
        exchange[
            "incoming"
        ].coupling_mass
        >
        0.0
    )


    assert np.any(
        exchange[
            "outgoing"
        ].coupling_mass
        >
        0.0
    )


# ============================================================
# 5. REAL SOURCE BELOW FLOAT RESOLUTION IS NOT DISCARDED
# ============================================================

def test_real_source_below_float_resolution_is_not_declared_irrelevant():

    parent = PhiSubstrateEngine(
        n_nodes=3,
        seed=11,
    )


    parent.pos = np.array(
        [
            [0.0, 0.0],
            [0.1, 0.0],
            [100.0, 100.0],
        ],
        dtype=np.float64,
    )


    receipt = (
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


    # Current float calculation underflows here.
    assert np.all(
        receipt.coupling_mass
        ==
        0.0
    )


    result = (
        assess_boundary_consequence(
            receipt,
            source_present=True,
        )
    )


    assert (
        result.status
        ==
        (
            "PRESERVE_BELOW_CURRENT_"
            "NUMERICAL_RESOLUTION"
        )
    )


# ============================================================
# 6. "HEAP" FALSIFICATION
#
# Ten individually tiny consequences are all below the old
# 1e-12 threshold.
#
# NONE may be discarded.
#
# Together they change the final classification.
# ============================================================

def test_many_subthreshold_consequences_are_composed_before_verdict():

    local = PhiSubstrateEngine(
        n_nodes=2,
        seed=1,
    )


    local.pos = np.array(
        [
            [0.0, 0.0],
            [0.1, 0.0],
        ],
        dtype=np.float64,
    )


    local.S = np.array(
        [
            [2.0, 2.0, 1.0],
            [2.0, 2.0, 1.0],
        ],
        dtype=np.float64,
    )


    local.R[:] = 0.0


    W, _ = (
        local.compute_coupling()
    )


    K_int = float(
        np.sum(
            W[
                np.ix_(
                    [
                        0,
                        1,
                    ],
                    [
                        0,
                        1,
                    ],
                )
            ]
        )
        /
        2.0
    )


    # --------------------------------------------------------
    # Start continuously just above the human classification
    # boundary M_C = 1.
    # --------------------------------------------------------

    target_mc = (
        1.000000000005
    )


    base_k = (
        K_int
        /
        target_mc
        -
        0.20
    )


    base = BoundaryEffectReceipt(
        flow_e=
            np.zeros(
                2,
            ),

        flow_r=
            np.zeros(
                2,
            ),

        geometry=
            np.zeros(
                (
                    2,
                    2,
                )
            ),

        coupling_mass=
            np.full(
                2,
                base_k,
            ),

        resolved=
            True,
    )


    before = (
        evaluate_cluster_with_boundary(
            local,
            [
                0,
                1,
            ],
            base,
            beta=
                local.beta,
        )
    )


    tiny_receipts = []


    for _ in range(
        10
    ):

        tiny = BoundaryEffectReceipt(
            flow_e=
                np.zeros(
                    2,
                ),

            flow_r=
                np.zeros(
                    2,
                ),

            geometry=
                np.zeros(
                    (
                        2,
                        2,
                    )
                ),

            coupling_mass=
                np.full(
                    2,
                    6e-13,
                ),

            resolved=
                True,
        )


        # ----------------------------------------------------
        # Every single contribution is below the OLD
        # distinguishability threshold.
        # ----------------------------------------------------

        decision = (
            assess_boundary_relevance(
                local_engine=
                    local,

                candidate_receipt=
                    tiny,

                tolerance=
                    1e-12,

                source_present=
                    True,
            )
        )


        assert (
            decision.status
            ==
            "PROPAGATE_REPRESENTED_CONSEQUENCE"
        )


        assert (
            decision.represented_magnitude
            <
            1e-12
        )


        tiny_receipts.append(
            tiny
        )


    # ========================================================
    # NO PER-BRANCH PRUNING.
    #
    # ALL consequences are composed.
    # ========================================================

    combined = (
        compose_accessible_consequences(
            [
                base,
                *tiny_receipts,
            ]
        )
    )


    after = (
        evaluate_cluster_with_boundary(
            local,
            [
                0,
                1,
            ],
            combined,
            beta=
                local.beta,
        )
    )


    assert (
        before[
            "M_C"
        ]
        >
        1.0
    )


    assert (
        after[
            "M_C"
        ]
        <=
        1.0
    )


    assert (
        before[
            "status"
        ]
        ==
        "PERSISTENT"
    )


    assert (
        after[
            "status"
        ]
        ==
        "CRITICAL_DISSOLUTION"
    )
