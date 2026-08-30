"""
PHI-INFINITY
AccessPointer + OMNIA inverse bridge

Architecture:

    human symbol
        -> AccessPointer
        -> accessible observation bases
        -> [symbol discarded]
        -> PHI-compatible candidate genealogies
        -> OMNIA conjunctive compatibility
        -> continuation classes
        -> T_Phi_H


IMPORTANT

OMNIA does NOT:

    - vote;
    - average semantic interpretations;
    - rank meanings;
    - convert language into S or R;
    - introduce new PHI dynamics.

A candidate survives only if it is compatible with EVERY
currently accessible observation basis.

If several PHI-distinguishable continuation classes remain,
the correct result is UNKNOWN.

Current implementation intentionally supports homogeneous
positional observation bases aligned to the same nodes and
temporal grid.

No claim is made yet for arbitrary heterogeneous data sources.
"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from src.core import PhiSubstrateEngine
from src.membrane import MembraneEvaluator


# ============================================================
# ACCESS POINTER
# ============================================================

@dataclass(frozen=True)
class AccessPointer:

    source_id: str

    spatial_span: tuple

    time_window: tuple = (
        0,
        -1,
    )

    label_metadata: str | None = None


# ============================================================
# ONE ACCESSIBLE OBSERVATION BASIS
# ============================================================

class AccessibleField:
    """
    One positional observation basis.

    Each frame has shape:

        (N, 2)

    NaN means:

        not observed

    NaN never generates PHI state.

    The first frame of the selected window must be fully
    observable because it initializes the native runtime
    geometry.
    """

    def __init__(
        self,
        time_series_positions,
    ):

        self.history = [
            np.asarray(
                frame,
                dtype=np.float64,
            )
            for frame in time_series_positions
        ]

        if len(
            self.history
        ) < 2:

            raise ValueError(
                "AccessibleField requires at least "
                "two temporal frames."
            )

        first_shape = (
            self.history[0]
            .shape
        )

        if (
            len(first_shape) != 2
            or
            first_shape[1] != 2
        ):

            raise ValueError(
                "Each frame must have shape (N, 2)."
            )

        for frame in (
            self.history
        ):

            if (
                frame.shape
                != first_shape
            ):

                raise ValueError(
                    "All frames must have identical shape."
                )

        self.n_nodes = (
            first_shape[0]
        )

    def resolve_access(
        self,
        pointer,
    ):

        (
            t_start,
            t_end,
        ) = (
            pointer.time_window
        )

        window_history = (
            self.history[
                t_start:
            ]
            if t_end == -1
            else
            self.history[
                t_start:
                t_end + 1
            ]
        )

        if len(
            window_history
        ) < 2:

            raise ValueError(
                "Selected time window must contain "
                "at least two frames."
            )

        if not np.all(
            np.isfinite(
                window_history[0]
            )
        ):

            raise ValueError(
                "The first selected frame must be "
                "fully observed."
            )

        (
            x_min,
            x_max,
            y_min,
            y_max,
        ) = (
            pointer.spatial_span
        )

        # ----------------------------------------------------
        # Locate every node from its latest finite observation.
        #
        # label_metadata is deliberately NEVER read.
        # ----------------------------------------------------

        latest_position = [
            None
        ] * self.n_nodes

        for frame in reversed(
            window_history
        ):

            for (
                i,
                pos,
            ) in enumerate(
                frame
            ):

                if (
                    latest_position[i]
                    is None
                    and
                    np.all(
                        np.isfinite(
                            pos
                        )
                    )
                ):

                    latest_position[i] = (
                        pos
                    )

            if all(
                pos is not None
                for pos
                in latest_position
            ):

                break

        focal_nodes = []

        for (
            i,
            pos,
        ) in enumerate(
            latest_position
        ):

            if (
                pos is None
            ):

                continue

            if (
                x_min
                <= pos[0]
                <= x_max
                and
                y_min
                <= pos[1]
                <= y_max
            ):

                focal_nodes.append(
                    i
                )

        return (
            focal_nodes,
            window_history,
        )


# ============================================================
# OMNIA
# ============================================================

class OmniaField:
    """
    All currently accessible aligned positional bases
    for the same phenomenon.

    OMNIA is conjunctive:

        compatible with B1
        AND
        compatible with B2
        AND
        ...
        AND
        compatible with Bn

    No majority and no weighted vote.
    """

    def __init__(
        self,
        *bases,
    ):

        if not bases:

            raise ValueError(
                "OmniaField requires at least "
                "one AccessibleField."
            )

        if not all(
            isinstance(
                base,
                AccessibleField,
            )
            for base
            in bases
        ):

            raise TypeError(
                "Every OMNIA basis must be "
                "an AccessibleField."
            )

        self.bases = list(
            bases
        )


# ============================================================
# FIELD BRIDGE
# ============================================================

class FieldBridge:

    def __init__(
        self,
        beta=0.25,
        tol_loss=1e-2,
        search_upper_bound=10.0,
        search_seeds=8,
        ambiguity_horizon=20,
    ):

        self.beta = float(
            beta
        )

        # Numerical search / access resolution parameters.
        # NOT ontological PHI laws.
        self.tol_loss = float(
            tol_loss
        )

        self.search_upper_bound = float(
            search_upper_bound
        )

        self.search_seeds = int(
            search_seeds
        )

        self.ambiguity_horizon = int(
            ambiguity_horizon
        )

        self.evaluator = (
            MembraneEvaluator(
                beta=self.beta
            )
        )


    # ========================================================
    # NATIVE ENGINE
    # ========================================================

    def _new_engine(
        self,
        n_nodes,
        seed=1,
    ):

        return PhiSubstrateEngine(
            n_nodes=n_nodes,
            beta=self.beta,
            seed=seed,
        )


    # ========================================================
    # NUMERICAL SEARCH SEEDS
    # ========================================================

    def _native_search_seeds(
        self,
        n_nodes,
    ):
        """
        Starting points are taken from native PHI runtime
        initializations.

        They are search seeds only.

        They do NOT encode linguistic categories.
        """

        seeds = []

        for runtime_seed in range(
            1,
            self.search_seeds + 1,
        ):

            engine = (
                self._new_engine(
                    n_nodes,
                    seed=runtime_seed,
                )
            )

            z = np.concatenate(
                [
                    np.asarray(
                        engine.S,
                        dtype=np.float64,
                    ).reshape(-1),

                    np.asarray(
                        engine.R,
                        dtype=np.float64,
                    ).reshape(-1),
                ]
            )

            seeds.append(
                z
            )

        return seeds


    # ========================================================
    # ONE-BASIS COMPATIBILITY
    # ========================================================

    def _basis_loss(
        self,
        z_flat,
        observed_window,
    ):
        """
        Compatibility with ONE positional observation basis.

        Missing observations (NaN) do not contribute.
        """

        n_nodes = (
            observed_window[0]
            .shape[0]
        )

        s_size = (
            n_nodes
            * 3
        )

        if not np.all(
            np.isfinite(
                observed_window[0]
            )
        ):

            return 1e30

        engine = (
            self._new_engine(
                n_nodes,
                seed=1,
            )
        )

        engine.pos = np.copy(
            observed_window[0]
        )

        engine.S = (
            np.asarray(
                z_flat[
                    :s_size
                ],
                dtype=np.float64,
            )
            .reshape(
                (
                    n_nodes,
                    3,
                )
            )
            .copy()
        )

        engine.R = (
            np.asarray(
                z_flat[
                    s_size:
                ],
                dtype=np.float64,
            )
            .copy()
        )

        total_loss = 0.0
        observed_values = 0

        for t in range(
            1,
            len(
                observed_window
            ),
        ):

            engine.step()

            observation = (
                observed_window[t]
            )

            mask = (
                np.isfinite(
                    observation
                )
            )

            if not np.any(
                mask
            ):

                continue

            difference = (
                engine.pos
                -
                observation
            )

            total_loss += float(
                np.sum(
                    difference[
                        mask
                    ]
                    ** 2
                )
            )

            observed_values += int(
                np.sum(
                    mask
                )
            )

        if (
            observed_values
            == 0
        ):

            return 1e30

        return (
            total_loss
        )


    # ========================================================
    # SEARCH OBJECTIVE
    # ========================================================

    def _search_objective(
        self,
        z_flat,
        observed_windows,
    ):
        """
        Sum is used ONLY to help the numerical optimizer
        locate shared candidates.

        It is NOT the OMNIA decision rule.

        Final survival is conjunctive:

            every basis loss <= tolerance
        """

        return sum(
            self._basis_loss(
                z_flat,
                window,
            )
            for window
            in observed_windows
        )


    # ========================================================
    # ALL COMPATIBLE GENEALOGIES FOUND
    # ========================================================

    def reconstruct_phi_candidates(
        self,
        observed_windows,
    ):

        n_nodes = (
            observed_windows[0][0]
            .shape[0]
        )

        s_size = (
            n_nodes
            * 3
        )

        upper = (
            self.search_upper_bound
        )

        bounds = (
            [
                (
                    0.01,
                    upper,
                )
            ]
            * s_size

            +

            [
                (
                    0.0,
                    upper,
                )
            ]
            * n_nodes
        )

        candidates = []

        for initial_guess in (
            self._native_search_seeds(
                n_nodes
            )
        ):

            result = minimize(
                self._search_objective,
                initial_guess,
                args=(
                    observed_windows,
                ),
                method="L-BFGS-B",
                bounds=bounds,
                options={
                    "maxiter":
                        1000,
                },
            )

            if not np.isfinite(
                result.fun
            ):

                continue

            basis_losses = [
                self._basis_loss(
                    result.x,
                    window,
                )
                for window
                in observed_windows
            ]

            # =================================================
            # OMNIA VETO
            #
            # NO averaging decision.
            # NO majority.
            # NO semantic score.
            #
            # Every accessible basis must remain compatible.
            # =================================================

            if all(
                loss
                <= self.tol_loss
                for loss
                in basis_losses
            ):

                candidates.append(
                    {
                        "z":
                            np.copy(
                                result.x
                            ),

                        "basis_losses":
                            basis_losses,

                        "search_objective":
                            float(
                                result.fun
                            ),
                    }
                )

        return (
            candidates
        )


    # ========================================================
    # GENEALOGICAL CONTINUATION
    # ========================================================

    def _continue_candidate(
        self,
        z_flat,
        observed_window,
        focal_nodes,
        horizon,
    ):

        n_nodes = (
            observed_window[0]
            .shape[0]
        )

        s_size = (
            n_nodes
            * 3
        )

        engine = (
            self._new_engine(
                n_nodes,
                seed=1,
            )
        )

        engine.pos = np.copy(
            observed_window[0]
        )

        engine.S = (
            np.asarray(
                z_flat[
                    :s_size
                ],
                dtype=np.float64,
            )
            .reshape(
                (
                    n_nodes,
                    3,
                )
            )
            .copy()
        )

        engine.R = (
            np.asarray(
                z_flat[
                    s_size:
                ],
                dtype=np.float64,
            )
            .copy()
        )

        # Z_-T -> ... -> Z_0
        for _ in range(
            len(
                observed_window
            )
            - 1
        ):

            engine.step()

        trajectory = []

        # Z_0 -> future continuation
        for cycle in range(
            horizon
        ):

            metrics = (
                engine.step()
            )

            (
                W,
                _,
            ) = (
                engine.compute_coupling()
            )

            membrane = (
                self.evaluator
                .evaluate_cluster(
                    engine,
                    focal_nodes,
                )
            )

            status = (
                "PERSISTENT"
                if
                membrane[
                    "M_C"
                ]
                > 1.0
                else
                "REORGANIZING"
            )

            trajectory.append(
                {
                    "cycle":
                        cycle,

                    "pos":
                        np.copy(
                            engine.pos
                        ),

                    "S":
                        np.copy(
                            engine.S
                        ),

                    "R":
                        np.copy(
                            engine.R
                        ),

                    "W":
                        np.copy(
                            W
                        ),

                    "M_C":
                        float(
                            membrane[
                                "M_C"
                            ]
                        ),

                    "R_C":
                        float(
                            membrane[
                                "R_C"
                            ]
                        ),

                    "structural_path_increment":
                        float(
                            metrics[
                                "mean_structural_path_increment"
                            ]
                        ),

                    "status":
                        status,
                }
            )

        return (
            trajectory
        )


    # ========================================================
    # PHI-CONTINUATION EQUIVALENCE
    # ========================================================

    def _same_observable_continuation(
        self,
        trajectory_a,
        trajectory_b,
    ):
        """
        Are these genealogies distinguishable under the
        CURRENT positional access?

        We compare:

            1. reported PHI status sequence;
            2. future observable positions.

        tol_loss is numerical access resolution only.
        """

        if (
            len(
                trajectory_a
            )
            !=
            len(
                trajectory_b
            )
        ):

            return False

        status_a = [
            step[
                "status"
            ]
            for step
            in trajectory_a
        ]

        status_b = [
            step[
                "status"
            ]
            for step
            in trajectory_b
        ]

        if (
            status_a
            !=
            status_b
        ):

            return False

        future_position_loss = 0.0

        for (
            step_a,
            step_b,
        ) in zip(
            trajectory_a,
            trajectory_b,
        ):

            difference = (
                step_a[
                    "pos"
                ]
                -
                step_b[
                    "pos"
                ]
            )

            future_position_loss += float(
                np.sum(
                    difference
                    ** 2
                )
            )

        return (
            future_position_loss
            <= self.tol_loss
        )


    # ========================================================
    # BUILD CONTINUATION CLASSES
    # ========================================================

    def _continuation_classes(
        self,
        runs,
    ):

        classes = []

        for run in (
            runs
        ):

            placed = False

            for continuation_class in (
                classes
            ):

                if (
                    self
                    ._same_observable_continuation(
                        run[
                            "trajectory"
                        ],
                        continuation_class[
                            0
                        ][
                            "trajectory"
                        ],
                    )
                ):

                    continuation_class.append(
                        run
                    )

                    placed = True

                    break

            if not placed:

                classes.append(
                    [
                        run
                    ]
                )

        return (
            classes
        )


    # ========================================================
    # INPUT NORMALIZATION
    # ========================================================

    def _normalize_fields(
        self,
        field,
    ):

        if isinstance(
            field,
            OmniaField,
        ):

            return list(
                field.bases
            )

        if isinstance(
            field,
            AccessibleField,
        ):

            return [
                field
            ]

        if (
            isinstance(
                field,
                (
                    list,
                    tuple,
                ),
            )
            and
            field
        ):

            if not all(
                isinstance(
                    item,
                    AccessibleField,
                )
                for item
                in field
            ):

                raise TypeError(
                    "All field entries must be "
                    "AccessibleField instances."
                )

            return list(
                field
            )

        raise TypeError(
            "field must be AccessibleField, "
            "OmniaField, or a non-empty list "
            "of AccessibleField."
        )


    # ========================================================
    # MAIN PIPELINE
    # ========================================================

    def process_pointer(
        self,
        pointer,
        field,
        future_horizon=10,
    ):

        try:

            fields = (
                self._normalize_fields(
                    field
                )
            )

            resolved = [
                base.resolve_access(
                    pointer
                )
                for base
                in fields
            ]

        except (
            ValueError,
            IndexError,
            TypeError,
        ) as exc:

            return {
                "status":
                    "UNKNOWN",

                "trajectory":
                    [],

                "human_synthesis":
                    (
                        "UNKNOWN: invalid or "
                        f"insufficient access ({exc})."
                    ),
            }


        nonempty_focal_sets = [
            tuple(
                focal
            )
            for (
                focal,
                _,
            )
            in resolved
            if focal
        ]

        if not (
            nonempty_focal_sets
        ):

            return {
                "status":
                    "UNKNOWN",

                "trajectory":
                    [],

                "human_synthesis":
                    (
                        "UNKNOWN: no observable trace "
                        "lies inside the selected "
                        "access region."
                    ),
            }


        # ====================================================
        # OMNIA cannot silently privilege one basis when
        # different bases locate different focal regions.
        # ====================================================

        if any(
            focal
            !=
            nonempty_focal_sets[
                0
            ]
            for focal
            in nonempty_focal_sets
        ):

            return {
                "status":
                    "UNKNOWN_ACCESS_DISAGREEMENT",

                "trajectory":
                    [],

                "human_synthesis":
                    (
                        "UNKNOWN: accessible bases "
                        "disagree on the focal region."
                    ),
            }


        focal_nodes = list(
            nonempty_focal_sets[
                0
            ]
        )

        observed_windows = [
            window
            for (
                _,
                window,
            )
            in resolved
        ]


        node_counts = {
            window[
                0
            ].shape[
                0
            ]
            for window
            in observed_windows
        }

        window_lengths = {
            len(
                window
            )
            for window
            in observed_windows
        }


        if (
            len(
                node_counts
            )
            != 1
            or
            len(
                window_lengths
            )
            != 1
        ):

            return {
                "status":
                    "UNKNOWN_ACCESS_MISALIGNED",

                "trajectory":
                    [],

                "human_synthesis":
                    (
                        "UNKNOWN: OMNIA bases are "
                        "not aligned to the same "
                        "nodes and time grid."
                    ),
            }


        # ====================================================
        # SYMBOLIC LAYER ENDS HERE.
        #
        # label_metadata is NEVER used after access.
        # ====================================================


        candidates = (
            self.reconstruct_phi_candidates(
                observed_windows
            )
        )


        # ====================================================
        # ZERO COMPATIBLE GENEALOGIES
        # ====================================================

        if not candidates:

            return {
                "status":
                    "UNRESOLVED_IN_SEARCH_DOMAIN",

                "trajectory":
                    [],

                "candidate_count":
                    0,

                "continuation_classes":
                    0,

                "resolution_scope":
                    (
                        "NO_COMPATIBLE_CANDIDATE_"
                        "WITHIN_EXPLORED_SEARCH_DOMAIN"
                    ),

                "human_synthesis":
                    (
                        "UNRESOLVED: no candidate "
                        "genealogy is compatible with "
                        "every accessible OMNIA basis "
                        "inside the explored numerical "
                        "search domain."
                    ),
            }


        classification_horizon = max(
            int(
                future_horizon
            ),
            self.ambiguity_horizon,
        )


        runs = []


        # ====================================================
        # Every surviving genealogy is continued from every
        # accessible positional basis.
        #
        # No single basis is privileged.
        # ====================================================

        for (
            candidate_index,
            candidate,
        ) in enumerate(
            candidates
        ):

            for (
                basis_index,
                observed_window,
            ) in enumerate(
                observed_windows
            ):

                runs.append(
                    {
                        "candidate_index":
                            candidate_index,

                        "basis_index":
                            basis_index,

                        "trajectory":
                            self._continue_candidate(
                                candidate[
                                    "z"
                                ],
                                observed_window,
                                focal_nodes,
                                classification_horizon,
                            ),
                    }
                )


        continuation_classes = (
            self._continuation_classes(
                runs
            )
        )


        # ====================================================
        # MULTIPLE DISTINGUISHABLE CONTINUATIONS
        #
        # THIS IS THE AMBIGUITY CORRECTION.
        #
        # Do NOT choose the lowest loss.
        # ====================================================

        if (
            len(
                continuation_classes
            )
            > 1
        ):

            class_summaries = []

            for (
                index,
                continuation_class,
            ) in enumerate(
                continuation_classes
            ):

                finals = [
                    run[
                        "trajectory"
                    ][
                        -1
                    ]
                    for run
                    in continuation_class
                ]

                class_summaries.append(
                    {
                        "class_index":
                            index,

                        "members":
                            len(
                                continuation_class
                            ),

                        "final_statuses":
                            sorted(
                                {
                                    step[
                                        "status"
                                    ]
                                    for step
                                    in finals
                                }
                            ),

                        "M_C_range":
                            (
                                float(
                                    min(
                                        step[
                                            "M_C"
                                        ]
                                        for step
                                        in finals
                                    )
                                ),

                                float(
                                    max(
                                        step[
                                            "M_C"
                                        ]
                                        for step
                                        in finals
                                    )
                                ),
                            ),
                    }
                )


            return {
                "status":
                    (
                        "UNKNOWN_AMBIGUOUS_"
                        "UNDER_CURRENT_ACCESS"
                    ),

                "trajectory":
                    [],

                "candidate_count":
                    len(
                        candidates
                    ),

                "continuation_classes":
                    len(
                        continuation_classes
                    ),

                "class_summaries":
                    class_summaries,

                "resolution_scope":
                    (
                        "MULTIPLE_CONTINUATION_CLASSES_"
                        "WITHIN_EXPLORED_SEARCH_DOMAIN"
                    ),

                "human_synthesis":
                    (
                        "UNKNOWN: "
                        f"{len(continuation_classes)} "
                        "PHI-distinguishable continuation "
                        "classes remain compatible with all "
                        "currently accessible OMNIA bases."
                    ),
            }


        # ====================================================
        # ONE CONTINUATION CLASS
        #
        # The representative is selected only for deterministic
        # serialization.
        #
        # It is NOT claimed to be the unique latent genealogy.
        # ====================================================

        best_candidate_index = min(
            range(
                len(
                    candidates
                )
            ),
            key=lambda i:
                (
                    max(
                        candidates[
                            i
                        ][
                            "basis_losses"
                        ]
                    ),

                    sum(
                        candidates[
                            i
                        ][
                            "basis_losses"
                        ]
                    ),

                    i,
                ),
        )


        representative = (
            self._continue_candidate(
                candidates[
                    best_candidate_index
                ][
                    "z"
                ],
                observed_windows[
                    0
                ],
                focal_nodes,
                int(
                    future_horizon
                ),
            )
        )


        final_steps = [
            run[
                "trajectory"
            ][
                int(
                    future_horizon
                )
                - 1
            ]
            for run
            in runs
        ]


        M_C_range = (
            float(
                min(
                    step[
                        "M_C"
                    ]
                    for step
                    in final_steps
                )
            ),

            float(
                max(
                    step[
                        "M_C"
                    ]
                    for step
                    in final_steps
                )
            ),
        )


        R_C_range = (
            float(
                min(
                    step[
                        "R_C"
                    ]
                    for step
                    in final_steps
                )
            ),

            float(
                max(
                    step[
                        "R_C"
                    ]
                    for step
                    in final_steps
                )
            ),
        )


        d_tau_range = (
            float(
                min(
                    step[
                        "structural_path_increment"
                    ]
                    for step
                    in final_steps
                )
            ),

            float(
                max(
                    step[
                        "structural_path_increment"
                    ]
                    for step
                    in final_steps
                )
            ),
        )


        final_step = (
            representative[
                -1
            ]
        )

        status = (
            final_step[
                "status"
            ]
        )


        human_synthesis = (
            f"REGION {focal_nodes}: "
            f"status={status}; "
            f"M_C compatible range="
            f"[{M_C_range[0]:.6f}, "
            f"{M_C_range[1]:.6f}]; "
            f"R_C range="
            f"[{R_C_range[0]:.6f}, "
            f"{R_C_range[1]:.6f}]; "
            f"{len(candidates)} candidate "
            "genealogies collapse to one "
            "continuation class under "
            "current access."
        )


        return {
            "status":
                status,

            "focal_nodes":
                focal_nodes,

            # Representative values retained for
            # backward compatibility.
            "M_C":
                float(
                    final_step[
                        "M_C"
                    ]
                ),

            "R_C":
                float(
                    final_step[
                        "R_C"
                    ]
                ),

            # Epistemically correct ranges across
            # every surviving candidate/basis run.
            "M_C_range":
                M_C_range,

            "R_C_range":
                R_C_range,

            "d_tau_range":
                d_tau_range,

            "fit_loss":
                float(
                    sum(
                        candidates[
                            best_candidate_index
                        ][
                            "basis_losses"
                        ]
                    )
                ),

            "basis_losses":
                [
                    float(
                        x
                    )
                    for x
                    in candidates[
                        best_candidate_index
                    ][
                        "basis_losses"
                    ]
                ],

            "candidate_count":
                len(
                    candidates
                ),

            "continuation_classes":
                1,

            "resolution_scope":
                (
                    "ONE_CONTINUATION_CLASS_"
                    "WITHIN_EXPLORED_SEARCH_DOMAIN"
                ),

            "trajectory":
                representative,

            "human_synthesis":
                human_synthesis,
        }
