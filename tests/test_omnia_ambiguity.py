"""
PHI-INFINITY OMNIA ambiguity benchmark.

Test 1:
    insufficient current access
    -> several distinguishable PHI continuations
    -> UNKNOWN

Test 2:
    additional aligned accessible basis
    -> OMNIA conjunctive veto
    -> remaining candidates collapse to one continuation class

The second test does NOT vote across bases.

Every surviving candidate must satisfy every basis independently.
"""

import numpy as np

from src.core import PhiSubstrateEngine

from src.field_bridge import (
    AccessPointer,
    AccessibleField,
    OmniaField,
    FieldBridge,
)


def make_truth(
    steps=6,
):
    """
    Synthetic fixture generated only by the native PHI runtime.

    No semantic category determines S/R.
    """

    engine = PhiSubstrateEngine(
        n_nodes=4,
        seed=7,
    )

    engine.pos = np.array(
        [
            [
                0.0,
                0.0,
            ],
            [
                0.1,
                0.0,
            ],
            [
                1.66,
                0.0,
            ],
            [
                1.76,
                0.0,
            ],
        ],
        dtype=np.float64,
    )

    history = [
        np.copy(
            engine.pos
        )
    ]

    for _ in range(
        steps
    ):

        engine.step()

        history.append(
            np.copy(
                engine.pos
            )
        )

    return (
        history
    )


def make_sparse_and_full_bases():

    full_history = (
        make_truth()
    )

    # Same phenomenon and same temporal grid.
    #
    # Sparse basis has only the initial movement trace.
    # Remaining positions are inaccessible, not zero.
    sparse_history = [
        np.copy(
            full_history[0]
        )
    ]

    for t in range(
        1,
        len(
            full_history
        ),
    ):

        if (
            t == 1
        ):

            sparse_history.append(
                np.copy(
                    full_history[t]
                )
            )

        else:

            sparse_history.append(
                np.full_like(
                    full_history[t],
                    np.nan,
                )
            )

    return (
        AccessibleField(
            sparse_history
        ),
        AccessibleField(
            full_history
        ),
    )


def test_sparse_access_refuses_false_uniqueness():

    (
        sparse,
        _,
    ) = (
        make_sparse_and_full_bases()
    )

    bridge = FieldBridge(
        search_seeds=8,
        ambiguity_horizon=20,
    )

    pointer = AccessPointer(
        source_id=
            "same-phenomenon",

        spatial_span=(
            -0.5,
            0.5,
            -0.5,
            0.5,
        ),

        time_window=(
            0,
            -1,
        ),

        label_metadata=
            "arbitrary label",
    )

    result = (
        bridge.process_pointer(
            pointer,
            sparse,
        )
    )

    assert (
        result[
            "status"
        ]
        ==
        "UNKNOWN_AMBIGUOUS_UNDER_CURRENT_ACCESS"
    )

    assert (
        result[
            "candidate_count"
        ]
        >= 2
    )

    assert (
        result[
            "continuation_classes"
        ]
        >= 2
    )

    assert (
        result[
            "trajectory"
        ]
        ==
        []
    )


def test_omnia_additional_basis_collapses_ambiguity_without_voting():

    (
        sparse,
        full,
    ) = (
        make_sparse_and_full_bases()
    )

    bridge = FieldBridge(
        search_seeds=8,
        ambiguity_horizon=20,
    )

    pointer = AccessPointer(
        source_id=
            "same-phenomenon",

        spatial_span=(
            -0.5,
            0.5,
            -0.5,
            0.5,
        ),

        time_window=(
            0,
            -1,
        ),

        label_metadata=
            "another arbitrary label",
    )

    result = (
        bridge.process_pointer(
            pointer,
            OmniaField(
                sparse,
                full,
            ),
        )
    )

    assert (
        result[
            "status"
        ]
        not in {
            "UNKNOWN",
            "UNKNOWN_AMBIGUOUS_UNDER_CURRENT_ACCESS",
            "UNRESOLVED_IN_SEARCH_DOMAIN",
        }
    )

    assert (
        result[
            "continuation_classes"
        ]
        ==
        1
    )

    assert (
        result[
            "candidate_count"
        ]
        >= 1
    )

    assert (
        len(
            result[
                "basis_losses"
            ]
        )
        ==
        2
    )

    # Every basis independently passes.
    # No average can hide an incompatible basis.
    assert all(
        loss
        <= bridge.tol_loss
        for loss
        in result[
            "basis_losses"
        ]
    )
