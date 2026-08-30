
import numpy as np
import pytest

from src.core import PhiSubstrateEngine


N = 36


LEAVES = [
    np.arange(0, 4),
    np.arange(4, 8),
    np.arange(8, 12),

    np.arange(12, 18),
    np.arange(18, 24),

    np.arange(24, 28),
    np.arange(28, 32),
    np.arange(32, 36),
]


PARENTS = [
    np.arange(0, 12),
    np.arange(12, 24),
    np.arange(24, 36),
]


ALTERNATIVE_GROUPS = [
    np.array([0, 7, 14, 21, 28, 35]),
    np.array([1, 8, 15, 22, 29]),
    np.array([2, 9, 16, 23, 30]),
    np.array([3, 10, 17, 24, 31]),
    np.array([4, 11, 18, 25, 32]),
    np.array([5, 12, 19, 26, 33]),
    np.array([6, 13, 20, 27, 34]),
]


def make_base():

    return PhiSubstrateEngine(
        n_nodes=N,
        seed=9217,
    )


def clone_engine(engine):

    clone = PhiSubstrateEngine(
        n_nodes=engine.N,
        sigma=engine.sigma,
        alpha=engine.alpha,
        beta=engine.beta,
        lmbda=engine.lmbda,
        gamma=engine.gamma,
        mu=engine.mu,
        eta=engine.eta,
        seed=0,
    )

    clone.pos = engine.pos.copy()
    clone.S = engine.S.copy()
    clone.R = engine.R.copy()

    return clone


def state_vector(engine):

    return np.concatenate(
        [
            engine.pos.ravel(),
            engine.S.ravel(),
            engine.R.ravel(),
        ]
    )


def state_difference(a, b):

    return float(
        np.max(
            np.abs(
                state_vector(a)
                -
                state_vector(b)
            )
        )
    )


def decomposed_step(
    engine,
    groups,
    mechanical_progress=1.0,
    require_complete=True,
):

    if (
        not np.isfinite(
            mechanical_progress
        )
        or
        mechanical_progress <= 0.0
    ):
        raise ValueError(
            "mechanical_progress must be finite and positive"
        )

    N_local = engine.N

    normalized_groups = [
        np.asarray(
            group,
            dtype=int,
        )
        for group in groups
    ]

    represented = np.concatenate(
        normalized_groups
    )

    unique = np.unique(
        represented
    )

    complete = (
        len(represented) == N_local
        and
        len(unique) == N_local
        and
        np.array_equal(
            np.sort(unique),
            np.arange(N_local),
        )
    )

    if require_complete and not complete:

        raise RuntimeError(
            "UNRESOLVED_EXTERNAL_FIELD"
        )

    W, diff = engine.compute_coupling()

    old_S = engine.S.copy()
    old_pos = engine.pos.copy()
    old_R = engine.R.copy()

    mu = (
        engine.mu
        *
        mechanical_progress
    )

    eta = (
        engine.eta
        *
        mechanical_progress
    )

    delta_e = np.tanh(
        engine.gamma
        *
        (
            old_S[:, 0][None, :]
            -
            old_S[:, 0][:, None]
        )
    )

    delta_r = np.tanh(
        engine.gamma
        *
        (
            old_S[:, 1][None, :]
            -
            old_S[:, 1][:, None]
        )
    )

    flow_e_parts = []
    flow_r_parts = []

    for group in normalized_groups:

        flow_e_parts.append(
            np.sum(
                W[:, group]
                *
                delta_e[:, group],
                axis=1,
            )
        )

        flow_r_parts.append(
            np.sum(
                W[:, group]
                *
                delta_r[:, group],
                axis=1,
            )
        )

    flow_e = np.sum(
        np.stack(
            flow_e_parts,
            axis=0,
        ),
        axis=0,
    )

    flow_r = np.sum(
        np.stack(
            flow_r_parts,
            axis=0,
        ),
        axis=0,
    )

    new_S = old_S.copy()

    new_S[:, 0] = np.maximum(
        0.01,
        old_S[:, 0]
        +
        mu * flow_e,
    )

    new_S[:, 1] = np.maximum(
        0.01,
        old_S[:, 1]
        +
        mu * flow_r,
    )

    structural_increment = np.linalg.norm(
        new_S
        -
        old_S,
        axis=1,
    )

    incomp = np.abs(
        (
            new_S[:, 0]
            /
            (
                new_S[:, 1]
                +
                1e-3
            )
        )
        -
        1.0
    )

    new_R = (
        (
            1.0
            -
            engine.lmbda
            *
            structural_increment
        )
        *
        old_R
        +
        engine.alpha
        *
        (
            incomp ** 2
        )
        *
        structural_increment
    )

    geometry_parts = []

    for group in normalized_groups:

        geometry_parts.append(
            np.sum(
                W[:, group, None]
                *
                (
                    1.0
                    -
                    engine.beta
                    *
                    new_R[
                        :,
                        None,
                        None,
                    ]
                )
                *
                diff[:, group, :],
                axis=1,
            )
        )

    geometry_total = np.sum(
        np.stack(
            geometry_parts,
            axis=0,
        ),
        axis=0,
    )

    new_pos = (
        old_pos
        +
        eta
        *
        geometry_total
    )

    engine.S = new_S
    engine.R = new_R
    engine.pos = new_pos

    return {
        "complete_access":
            complete,

        "structural_path_increment":
            structural_increment,
    }


def test_monolithic_equals_flat_decomposition():

    base = make_base()

    whole = clone_engine(
        base
    )

    flat = clone_engine(
        base
    )

    whole.step()

    decomposed_step(
        flat,
        PARENTS,
    )

    assert state_difference(
        whole,
        flat,
    ) <= 1e-13


def test_monolithic_equals_recursive_subfragments():

    base = make_base()

    whole = clone_engine(
        base
    )

    recursive = clone_engine(
        base
    )

    whole.step()

    decomposed_step(
        recursive,
        LEAVES,
    )

    assert state_difference(
        whole,
        recursive,
    ) <= 1e-13


def test_arbitrary_partition_does_not_generate_continuation():

    base = make_base()

    whole = clone_engine(
        base
    )

    alternative = clone_engine(
        base
    )

    whole.step()

    decomposed_step(
        alternative,
        ALTERNATIVE_GROUPS,
    )

    assert state_difference(
        whole,
        alternative,
    ) <= 1e-13


def test_recursive_scale_identity_survives_100_steps():

    base = make_base()

    whole = clone_engine(
        base
    )

    recursive = clone_engine(
        base
    )

    maximum_difference = 0.0

    for _ in range(100):

        whole.step()

        decomposed_step(
            recursive,
            LEAVES,
        )

        maximum_difference = max(
            maximum_difference,
            state_difference(
                whole,
                recursive,
            ),
        )

    assert maximum_difference <= 1e-10


@pytest.mark.parametrize(
    "progress",
    [
        0.17,
        0.5,
        1.0,
        1.7,
    ],
)
def test_scale_identity_survives_mechanical_progress(
    progress,
):

    base = make_base()

    whole = clone_engine(
        base
    )

    recursive = clone_engine(
        base
    )

    whole.step(
        mechanical_progress=progress
    )

    decomposed_step(
        recursive,
        LEAVES,
        mechanical_progress=progress,
    )

    assert state_difference(
        whole,
        recursive,
    ) <= 1e-13


def test_single_fragment_nested_fields_compose_exactly():

    base = make_base()

    target = 2

    same_leaf_others = np.array(
        [
            0,
            1,
            3,
        ]
    )

    same_parent_rest = np.arange(
        4,
        12,
    )

    outside_parent = np.arange(
        12,
        N,
    )

    W, _ = base.compute_coupling()

    delta_e = np.tanh(
        base.gamma
        *
        (
            base.S[:, 0][None, :]
            -
            base.S[:, 0][:, None]
        )
    )

    full = np.sum(
        W[target]
        *
        delta_e[target]
    )

    nested = (
        np.sum(
            W[
                target,
                same_leaf_others
            ]
            *
            delta_e[
                target,
                same_leaf_others
            ]
        )
        +
        np.sum(
            W[
                target,
                same_parent_rest
            ]
            *
            delta_e[
                target,
                same_parent_rest
            ]
        )
        +
        np.sum(
            W[
                target,
                outside_parent
            ]
            *
            delta_e[
                target,
                outside_parent
            ]
        )
    )

    assert abs(
        full - nested
    ) <= 1e-14


def test_all_nested_shells_compose_into_whole_consequence():

    base = make_base()

    W, _ = base.compute_coupling()

    delta_e = np.tanh(
        base.gamma
        *
        (
            base.S[:, 0][None, :]
            -
            base.S[:, 0][:, None]
        )
    )

    maximum_error = 0.0

    for target in range(N):

        leaf = next(
            group
            for group in LEAVES
            if target in group
        )

        parent = next(
            group
            for group in PARENTS
            if target in group
        )

        leaf_others = leaf[
            leaf != target
        ]

        parent_shell = np.setdiff1d(
            parent,
            leaf,
        )

        world_shell = np.setdiff1d(
            np.arange(N),
            parent,
        )

        full = np.sum(
            W[target]
            *
            delta_e[target]
        )

        composed = (
            np.sum(
                W[
                    target,
                    leaf_others
                ]
                *
                delta_e[
                    target,
                    leaf_others
                ]
            )
            +
            np.sum(
                W[
                    target,
                    parent_shell
                ]
                *
                delta_e[
                    target,
                    parent_shell
                ]
            )
            +
            np.sum(
                W[
                    target,
                    world_shell
                ]
                *
                delta_e[
                    target,
                    world_shell
                ]
            )
        )

        maximum_error = max(
            maximum_error,
            abs(
                full
                -
                composed
            ),
        )

    assert maximum_error <= 1e-13


def test_incomplete_exterior_is_unresolved_and_state_unchanged():

    base = make_base()

    partial = clone_engine(
        base
    )

    partial_groups = [
        np.arange(0, 12),
        np.arange(12, 24),
    ]

    with pytest.raises(
        RuntimeError,
        match="UNRESOLVED_EXTERNAL_FIELD",
    ):

        decomposed_step(
            partial,
            partial_groups,
            require_complete=True,
        )

    assert state_difference(
        partial,
        base,
    ) == 0.0


def test_false_exterior_zero_changes_reality():

    base = make_base()

    full = clone_engine(
        base
    )

    false_closed = clone_engine(
        base
    )

    partial_groups = [
        np.arange(0, 12),
        np.arange(12, 24),
    ]

    full.step()

    decomposed_step(
        false_closed,
        partial_groups,
        require_complete=False,
    )

    assert state_difference(
        full,
        false_closed,
    ) > 1e-15
