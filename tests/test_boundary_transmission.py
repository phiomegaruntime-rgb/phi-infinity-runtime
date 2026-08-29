
import numpy as np
import pytest

from src.core import PhiSubstrateEngine

from src.boundary import (
    BoundaryEffectReceipt,
    UnresolvedExternalFieldError,
    boundary_receipt_from_parent,
    combine_boundary_receipts,
    step_with_boundary,
    evaluate_cluster_with_boundary,
)


def clone_local(
    parent,
    local_indices,
):

    local = PhiSubstrateEngine(
        n_nodes=len(
            local_indices
        ),
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
            local_indices
        ]
    )

    local.S = np.copy(
        parent.S[
            local_indices
        ]
    )

    local.R = np.copy(
        parent.R[
            local_indices
        ]
    )

    return local


# ============================================================
# 1. SAME REALITY:
#    whole environment vs fragment receiving real effects
# ============================================================

def test_boundary_transmission_reproduces_full_runtime_50_steps():

    parent = PhiSubstrateEngine(
        n_nodes=6,
        seed=7,
    )

    local_indices = [
        0,
        1,
        2,
    ]

    external_indices = [
        3,
        4,
        5,
    ]

    local = clone_local(
        parent,
        local_indices,
    )


    for _ in range(50):

        receipt = (
            boundary_receipt_from_parent(
                parent,
                local_indices,
                external_indices,
            )
        )

        step_with_boundary(
            local,
            receipt,
        )

        parent.step()


        assert np.allclose(
            local.pos,
            parent.pos[
                local_indices
            ],
            rtol=0.0,
            atol=1e-14,
        )


        assert np.allclose(
            local.S,
            parent.S[
                local_indices
            ],
            rtol=0.0,
            atol=1e-14,
        )


        assert np.allclose(
            local.R,
            parent.R[
                local_indices
            ],
            rtol=0.0,
            atol=1e-14,
        )


# ============================================================
# 2. MANY CONTAINING LEVELS:
#    separate shells must equal direct containing field
# ============================================================

def test_multiple_containing_shells_compose_exactly():

    parent = PhiSubstrateEngine(
        n_nodes=8,
        seed=12,
    )


    local_indices = [
        0,
        1,
        2,
    ]


    shell_1 = [
        3,
        4,
    ]

    shell_2 = [
        5,
    ]

    shell_3 = [
        6,
        7,
    ]


    r1 = boundary_receipt_from_parent(
        parent,
        local_indices,
        shell_1,
    )


    r2 = boundary_receipt_from_parent(
        parent,
        local_indices,
        shell_2,
    )


    r3 = boundary_receipt_from_parent(
        parent,
        local_indices,
        shell_3,
    )


    composed = (
        combine_boundary_receipts(
            r1,
            r2,
            r3,
        )
    )


    direct = (
        boundary_receipt_from_parent(
            parent,
            local_indices,
            shell_1
            +
            shell_2
            +
            shell_3,
        )
    )


    assert np.allclose(
        composed.flow_e,
        direct.flow_e,
        rtol=0.0,
        atol=1e-14,
    )


    assert np.allclose(
        composed.flow_r,
        direct.flow_r,
        rtol=0.0,
        atol=1e-14,
    )


    assert np.allclose(
        composed.geometry,
        direct.geometry,
        rtol=0.0,
        atol=1e-14,
    )


    assert np.allclose(
        composed.coupling_mass,
        direct.coupling_mass,
        rtol=0.0,
        atol=1e-14,
    )


# ============================================================
# 3. UNKNOWN EXTERIOR:
#    missing reality must never become zero
# ============================================================

def test_unresolved_exterior_is_not_silently_zero():

    local = PhiSubstrateEngine(
        n_nodes=3,
        seed=4,
    )


    before_pos = np.copy(
        local.pos
    )

    before_S = np.copy(
        local.S
    )

    before_R = np.copy(
        local.R
    )


    with pytest.raises(
        UnresolvedExternalFieldError
    ):

        step_with_boundary(
            local,
            BoundaryEffectReceipt
            .unresolved(
                local.N
            ),
        )


    assert np.array_equal(
        local.pos,
        before_pos,
    )

    assert np.array_equal(
        local.S,
        before_S,
    )

    assert np.array_equal(
        local.R,
        before_R,
    )


# ============================================================
# 4. UNKNOWN EXTERIOR:
#    persistence cannot be invented
# ============================================================

def test_unresolved_exterior_cannot_assert_persistence():

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


    local.S[:] = np.array(
        [
            [2.0, 2.0, 1.0],
            [2.0, 2.0, 1.0],
        ],
        dtype=np.float64,
    )


    local.R[:] = 0.0


    result = (
        evaluate_cluster_with_boundary(
            local,
            [
                0,
                1,
            ],
            BoundaryEffectReceipt
            .unresolved(
                local.N
            ),
        )
    )


    assert (
        result[
            "M_C"
        ]
        is None
    )


    assert (
        result[
            "M_C_upper"
        ]
        > 1.0
    )


    assert (
        result[
            "status"
        ]
        ==
        "UNKNOWN_EXTERNAL_FIELD"
    )


    assert (
        result[
            "external_resolved"
        ]
        is False
    )
