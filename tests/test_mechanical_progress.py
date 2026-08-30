
import inspect

import numpy as np
import pytest

from src.core import PhiSubstrateEngine

from src.boundary import (
    boundary_receipt_from_parent,
    step_with_boundary,
)


def clone_engine(
    engine,
):

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


def max_difference(
    a,
    b,
):

    return float(
        max(
            np.max(
                np.abs(
                    a.pos - b.pos
                )
            ),
            np.max(
                np.abs(
                    a.S - b.S
                )
            ),
            np.max(
                np.abs(
                    a.R - b.R
                )
            ),
        )
    )


def local_from_parent(
    parent,
    indices,
):

    local = PhiSubstrateEngine(
        n_nodes=len(indices),
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
            indices
        ]
    )

    local.S = np.copy(
        parent.S[
            indices
        ]
    )

    local.R = np.copy(
        parent.R[
            indices
        ]
    )

    return local


# ============================================================
# 1
# ============================================================

def test_unit_progress_is_exactly_default_mechanics():

    base = PhiSubstrateEngine(
        n_nodes=8,
        seed=23,
    )

    implicit = clone_engine(
        base
    )

    explicit = clone_engine(
        base
    )


    for _ in range(
        100
    ):

        implicit.step()

        explicit.step(
            mechanical_progress=1.0
        )


    assert (
        max_difference(
            implicit,
            explicit,
        )
        ==
        0.0
    )


# ============================================================
# 2
# ============================================================

def test_structural_zero_is_not_false_immobility():

    engine = PhiSubstrateEngine(
        n_nodes=2,
        seed=1,
    )

    engine.pos = np.array(
        [
            [-0.5, 0.0],
            [ 0.5, 0.0],
        ],
        dtype=np.float64,
    )

    engine.S = np.array(
        [
            [2.0, 2.0, 1.0],
            [2.0, 2.0, 1.0],
        ],
        dtype=np.float64,
    )

    engine.R[:] = 0.0


    result = engine.step()


    assert np.all(
        result[
            "structural_path_increment"
        ]
        ==
        0.0
    )


    assert np.any(
        result[
            "geometry_path_increment"
        ]
        >
        0.0
    )


    assert (
        result[
            "representation_status"
        ]
        ==
        "REPRESENTED_TRANSFORMATION"
    )


# ============================================================
# 3
# ============================================================

def test_computational_stasis_is_only_representation_statement():

    engine = PhiSubstrateEngine(
        n_nodes=1,
        seed=7,
    )


    result = engine.step()


    assert (
        result[
            "representation_status"
        ]
        ==
        (
            "NO_DISTINGUISHABLE_TRANSFORMATION_"
            "IN_CURRENT_REPRESENTATION"
        )
    )


# ============================================================
# 4 — LOCAL REPARAMETERIZATION
# ============================================================

def test_arbitrary_reparameterization_preserves_trajectory():

    base = PhiSubstrateEngine(
        n_nodes=7,
        seed=31,
    )

    canonical = clone_engine(
        base
    )

    alternative = clone_engine(
        base
    )


    rng = np.random.RandomState(
        20260830
    )


    h = 0.037


    for _ in range(
        200
    ):

        scale = float(
            np.exp(
                rng.uniform(
                    np.log(0.2),
                    np.log(5.0),
                )
            )
        )


        canonical.step(
            mechanical_progress=h
        )


        original_mu = alternative.mu
        original_eta = alternative.eta


        try:

            alternative.mu = (
                base.mu
                /
                scale
            )

            alternative.eta = (
                base.eta
                /
                scale
            )


            alternative.step(
                mechanical_progress=
                    scale
                    *
                    h
            )


        finally:

            alternative.mu = original_mu
            alternative.eta = original_eta


    assert (
        max_difference(
            canonical,
            alternative,
        )
        <
        1e-14
    )


# ============================================================
# 5 — BOUNDARY REPARAMETERIZATION
# ============================================================

def test_boundary_reparameterization_preserves_trajectory():

    parent = PhiSubstrateEngine(
        n_nodes=8,
        seed=41,
    )


    focal = [
        0,
        1,
        2,
    ]


    external = [
        3,
        4,
        5,
        6,
        7,
    ]


    receipt = (
        boundary_receipt_from_parent(
            parent,
            focal,
            external,
        )
    )


    canonical = local_from_parent(
        parent,
        focal,
    )


    alternative = local_from_parent(
        parent,
        focal,
    )


    rng = np.random.RandomState(
        404
    )


    h = 0.025


    for _ in range(
        50
    ):

        scale = float(
            np.exp(
                rng.uniform(
                    np.log(0.25),
                    np.log(4.0),
                )
            )
        )


        step_with_boundary(
            canonical,
            receipt,
            mechanical_progress=h,
        )


        old_mu = alternative.mu
        old_eta = alternative.eta


        try:

            alternative.mu = (
                parent.mu
                /
                scale
            )

            alternative.eta = (
                parent.eta
                /
                scale
            )


            step_with_boundary(
                alternative,
                receipt,
                mechanical_progress=
                    scale
                    *
                    h,
            )


        finally:

            alternative.mu = old_mu
            alternative.eta = old_eta


    assert (
        max_difference(
            canonical,
            alternative,
        )
        <
        1e-14
    )


# ============================================================
# 6 — CONVERGENCE
# ============================================================

def test_finer_partition_converges_toward_same_trajectory():

    base = PhiSubstrateEngine(
        n_nodes=6,
        seed=53,
    )


    total_progress = 1.0


    def evolve(
        n_steps,
    ):

        engine = clone_engine(
            base
        )

        h = (
            total_progress
            /
            n_steps
        )


        for _ in range(
            n_steps
        ):

            engine.step(
                mechanical_progress=h
            )


        return engine


    reference = evolve(
        1024
    )

    coarse = evolve(
        16
    )

    fine = evolve(
        256
    )


    coarse_error = (
        max_difference(
            coarse,
            reference,
        )
    )


    fine_error = (
        max_difference(
            fine,
            reference,
        )
    )


    assert (
        fine_error
        <
        coarse_error
    )


    assert (
        fine_error
        <
        coarse_error
        /
        4.0
    )


# ============================================================
# 7 — REAL DIFFERENCE IN PROGRESS
# ============================================================

def test_different_actual_progress_changes_sampled_point():

    base = PhiSubstrateEngine(
        n_nodes=5,
        seed=67,
    )


    short = clone_engine(
        base
    )

    long = clone_engine(
        base
    )


    short.step(
        mechanical_progress=0.1
    )


    long.step(
        mechanical_progress=0.2
    )


    assert (
        max_difference(
            short,
            long,
        )
        >
        0.0
    )


# ============================================================
# 8 — API / SEMANTIC GATE
# ============================================================

def test_progress_api_and_no_false_proper_time_alias():

    engine = PhiSubstrateEngine(
        n_nodes=3,
        seed=3,
    )


    with pytest.raises(
        ValueError
    ):

        engine.step(
            mechanical_progress=0.0
        )


    with pytest.raises(
        ValueError
    ):

        engine.step(
            mechanical_progress=-1.0
        )


    result = engine.step(
        mechanical_progress=0.5
    )


    assert (
        "mechanical_progress"
        in result
    )

    assert (
        "structural_path_increment"
        in result
    )

    assert (
        "geometry_path_increment"
        in result
    )

    assert (
        "residual_path_increment"
        in result
    )


    assert (
        "d_tau"
        not in result
    )

    assert (
        "mean_dtau"
        not in result
    )


    signature = inspect.signature(
        PhiSubstrateEngine.step
    )


    assert (
        "mechanical_progress"
        in
        signature.parameters
    )
