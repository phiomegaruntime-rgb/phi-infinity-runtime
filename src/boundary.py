
"""
PHI-INFINITY
Infinity -> Field -> Fragment
Boundary Consequence Transmission

A local fragment must never confuse the end of its computational
scope with the end of reality.

The containing field transmits only the effects that actually cross
the fragment boundary during the current transformation.

Effects transmitted by several containing shells are additive and
may therefore be composed without enumerating the whole containing
reality.

No PHI core equation is changed.
"""

from dataclasses import dataclass

import numpy as np


class UnresolvedExternalFieldError(RuntimeError):
    """
    Raised when a local transformation would require exterior
    consequences that have not yet been resolved.
    """


@dataclass(frozen=True)
class BoundaryEffectReceipt:
    """
    Consequences arriving from outside a local computational scope.

    Arrays follow the local engine ordering.

    flow_e
        Exterior contribution to the first native exchange flow.

    flow_r
        Exterior contribution to the second native exchange flow.

    geometry
        Exterior weighted displacement contribution.

    coupling_mass
        Exterior coupling reaching each local element.

    resolved
        True only when the relevant exterior contribution for the
        current transformation has actually been resolved.

        Missing access is never silently converted to zero.
    """

    flow_e: np.ndarray
    flow_r: np.ndarray
    geometry: np.ndarray
    coupling_mass: np.ndarray
    resolved: bool = True


    @staticmethod
    def unresolved(n_local):

        return BoundaryEffectReceipt(
            flow_e=np.zeros(
                n_local,
                dtype=np.float64,
            ),
            flow_r=np.zeros(
                n_local,
                dtype=np.float64,
            ),
            geometry=np.zeros(
                (n_local, 2),
                dtype=np.float64,
            ),
            coupling_mass=np.zeros(
                n_local,
                dtype=np.float64,
            ),
            resolved=False,
        )


    @staticmethod
    def resolved_zero(n_local):
        """
        Explicit zero is allowed only when the caller has actually
        resolved the relevant exterior contribution and it is zero.
        """

        return BoundaryEffectReceipt(
            flow_e=np.zeros(
                n_local,
                dtype=np.float64,
            ),
            flow_r=np.zeros(
                n_local,
                dtype=np.float64,
            ),
            geometry=np.zeros(
                (n_local, 2),
                dtype=np.float64,
            ),
            coupling_mass=np.zeros(
                n_local,
                dtype=np.float64,
            ),
            resolved=True,
        )


    def __add__(self, other):

        return BoundaryEffectReceipt(
            flow_e=(
                np.asarray(self.flow_e)
                + np.asarray(other.flow_e)
            ),
            flow_r=(
                np.asarray(self.flow_r)
                + np.asarray(other.flow_r)
            ),
            geometry=(
                np.asarray(self.geometry)
                + np.asarray(other.geometry)
            ),
            coupling_mass=(
                np.asarray(self.coupling_mass)
                + np.asarray(other.coupling_mass)
            ),
            resolved=bool(
                self.resolved
                and other.resolved
            ),
        )


# ============================================================
# FIELD -> FRAGMENT
# ============================================================

def boundary_receipt_from_parent(
    parent_engine,
    local_indices,
    external_indices,
):
    """
    Derive what a containing field actually transmits to the selected
    fragment at the current transformation.

    Nothing about the containing field is copied wholesale.

    Only its consequences on the local fragment are transmitted.
    """

    local_indices = np.asarray(
        local_indices,
        dtype=int,
    )

    external_indices = np.asarray(
        external_indices,
        dtype=int,
    )

    n_local = len(
        local_indices
    )

    if n_local == 0:
        raise ValueError(
            "local_indices cannot be empty."
        )

    if len(external_indices) == 0:

        return (
            BoundaryEffectReceipt
            .resolved_zero(
                n_local
            )
        )

    W, diff = (
        parent_engine
        .compute_coupling()
    )

    W_le = W[
        np.ix_(
            local_indices,
            external_indices,
        )
    ]

    S = parent_engine.S


    # --------------------------------------------------------
    # Effects on the two native exchange flows
    # --------------------------------------------------------

    flow_e = np.sum(
        W_le
        * np.tanh(
            parent_engine.gamma
            * (
                S[
                    external_indices,
                    0
                ][None, :]
                -
                S[
                    local_indices,
                    0
                ][:, None]
            )
        ),
        axis=1,
    )


    flow_r = np.sum(
        W_le
        * np.tanh(
            parent_engine.gamma
            * (
                S[
                    external_indices,
                    1
                ][None, :]
                -
                S[
                    local_indices,
                    1
                ][:, None]
            )
        ),
        axis=1,
    )


    # --------------------------------------------------------
    # Effects on spatial transformation
    # --------------------------------------------------------

    geometry = np.sum(
        W_le[:, :, None]
        *
        diff[
            np.ix_(
                local_indices,
                external_indices,
            )
        ],
        axis=1,
    )


    # --------------------------------------------------------
    # Coupling crossing the boundary
    # --------------------------------------------------------

    coupling_mass = np.sum(
        W_le,
        axis=1,
    )


    return BoundaryEffectReceipt(
        flow_e=np.asarray(
            flow_e,
            dtype=np.float64,
        ),
        flow_r=np.asarray(
            flow_r,
            dtype=np.float64,
        ),
        geometry=np.asarray(
            geometry,
            dtype=np.float64,
        ),
        coupling_mass=np.asarray(
            coupling_mass,
            dtype=np.float64,
        ),
        resolved=True,
    )


# ============================================================
# MULTIPLE CONTAINING FIELDS
# ============================================================

def combine_boundary_receipts(
    *receipts,
):
    """
    Compose consequences transmitted through several containing shells.

    No voting.
    No averaging.
    No semantic weighting.

    Real contributions simply accumulate.
    """

    if not receipts:
        raise ValueError(
            "At least one receipt is required."
        )

    combined = receipts[0]

    for receipt in receipts[1:]:

        combined = (
            combined
            + receipt
        )

    return combined


# ============================================================
# LOCAL TRANSFORMATION WITH CONTAINING-FIELD EFFECTS
# ============================================================

def _step_with_boundary_phi_mechanics(
    engine,
    receipt,
):
    """
    Advance the local fragment by one native PHI transformation while
    including consequences arriving from the containing field.

    If those exterior consequences remain unresolved, no local future
    is fabricated.
    """

    if not isinstance(
        receipt,
        BoundaryEffectReceipt,
    ):
        raise TypeError(
            "receipt must be a BoundaryEffectReceipt."
        )


    if not receipt.resolved:

        raise UnresolvedExternalFieldError(
            "Exterior consequences are unresolved. "
            "Local evolution cannot be treated as closed."
        )


    n = engine.N


    if np.asarray(
        receipt.flow_e
    ).shape != (n,):

        raise ValueError(
            "receipt.flow_e has wrong shape."
        )


    if np.asarray(
        receipt.flow_r
    ).shape != (n,):

        raise ValueError(
            "receipt.flow_r has wrong shape."
        )


    if np.asarray(
        receipt.geometry
    ).shape != (n, 2):

        raise ValueError(
            "receipt.geometry has wrong shape."
        )


    if np.asarray(
        receipt.coupling_mass
    ).shape != (n,):

        raise ValueError(
            "receipt.coupling_mass has wrong shape."
        )


    W, diff = (
        engine.compute_coupling()
    )


    # --------------------------------------------------------
    # Internal consequences
    # --------------------------------------------------------

    internal_flow_e = np.sum(
        W
        * np.tanh(
            engine.gamma
            * (
                engine.S[:, 0:1].T
                -
                engine.S[:, 0:1]
            )
        ),
        axis=1,
    )


    internal_flow_r = np.sum(
        W
        * np.tanh(
            engine.gamma
            * (
                engine.S[:, 1:2].T
                -
                engine.S[:, 1:2]
            )
        ),
        axis=1,
    )


    # --------------------------------------------------------
    # Internal + transmitted external consequences
    # --------------------------------------------------------

    total_flow_e = (
        internal_flow_e
        + receipt.flow_e
    )

    total_flow_r = (
        internal_flow_r
        + receipt.flow_r
    )


    prev_S = (
        engine.S.copy()
    )


    engine.S[:, 0] = np.maximum(
        0.01,
        engine.S[:, 0]
        +
        engine.mu
        * total_flow_e,
    )


    engine.S[:, 1] = np.maximum(
        0.01,
        engine.S[:, 1]
        +
        engine.mu
        * total_flow_r,
    )


    structural_path_increment = np.linalg.norm(
        engine.S
        -
        prev_S,
        axis=1,
    )


    incomp = np.abs(
        (
            engine.S[:, 0]
            /
            (
                engine.S[:, 1]
                + 1e-3
            )
        )
        -
        1.0
    )


    engine.R = (
        (
            1.0
            -
            engine.lmbda
            * structural_path_increment
        )
        * engine.R
        +
        engine.alpha
        * (
            incomp ** 2
        )
        * structural_path_increment
    )


    internal_geometry = np.sum(
        W[:, :, None]
        * diff,
        axis=1,
    )


    total_geometry = (
        internal_geometry
        +
        receipt.geometry
    )


    engine.pos += (
        (
            1.0
            -
            engine.beta
            * engine.R
        )[:, None]
        *
        total_geometry
        *
        engine.eta
    )


    return {
        "mean_energy":
            float(
                np.mean(
                    engine.S[:, 0]
                )
            ),

        "energy_variance":
            float(
                np.std(
                    engine.S[:, 0]
                )
            ),

        "mean_stress":
            float(
                np.mean(
                    engine.R
                )
            ),

        "max_stress":
            float(
                np.max(
                    engine.R
                )
            ),

        "mean_structural_path_increment":
            float(
                np.mean(
                    structural_path_increment
                )
            ),
    }

def step_with_boundary(
    engine,
    *args,
    mechanical_progress=1.0,
    **kwargs,
):
    """
    Traverse the existing boundary-aware PHI mechanics using
    a neutral mechanical-progress coordinate.

    The original boundary function is preserved as
    _step_with_boundary_phi_mechanics().

    mechanical_progress is NOT proper time.
    """

    try:
        progress = float(
            mechanical_progress
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise ValueError(
            "mechanical_progress must be a finite "
            "strictly positive scalar."
        ) from exc


    if (
        not np.isfinite(
            progress
        )
        or
        progress <= 0.0
    ):

        raise ValueError(
            "mechanical_progress must be finite "
            "and strictly positive."
        )


    prev_pos = engine.pos.copy()
    prev_S = engine.S.copy()
    prev_R = engine.R.copy()


    original_mu = engine.mu
    original_eta = engine.eta


    try:

        engine.mu = (
            original_mu
            *
            progress
        )

        engine.eta = (
            original_eta
            *
            progress
        )


        result = (
            _step_with_boundary_phi_mechanics(
                engine,
                *args,
                **kwargs,
            )
        )


    finally:

        engine.mu = original_mu
        engine.eta = original_eta


    if result is None:

        result = {}


    elif isinstance(
        result,
        dict,
    ):

        result = dict(
            result
        )


    else:

        raise TypeError(
            "_step_with_boundary_phi_mechanics() "
            "must return dict or None."
        )


    structural_path_increment = (
        np.linalg.norm(
            engine.S
            -
            prev_S,
            axis=1,
        )
    )


    geometry_path_increment = (
        np.linalg.norm(
            engine.pos
            -
            prev_pos,
            axis=1,
        )
    )


    residual_path_increment = (
        np.abs(
            engine.R
            -
            prev_R
        )
    )


    represented_transformation = bool(
        np.any(
            structural_path_increment
            !=
            0.0
        )
        or
        np.any(
            geometry_path_increment
            !=
            0.0
        )
        or
        np.any(
            residual_path_increment
            !=
            0.0
        )
    )


    result[
        "mechanical_progress"
    ] = progress


    result[
        "structural_path_increment"
    ] = (
        structural_path_increment.copy()
    )


    result[
        "mean_structural_path_increment"
    ] = float(
        np.mean(
            structural_path_increment
        )
    )


    result[
        "geometry_path_increment"
    ] = (
        geometry_path_increment.copy()
    )


    result[
        "residual_path_increment"
    ] = (
        residual_path_increment.copy()
    )


    result[
        "representation_status"
    ] = (
        "REPRESENTED_TRANSFORMATION"
        if represented_transformation
        else
        (
            "NO_DISTINGUISHABLE_TRANSFORMATION_"
            "IN_CURRENT_REPRESENTATION"
        )
    )


    result.pop(
        "d_tau",
        None,
    )

    result.pop(
        "mean_dtau",
        None,
    )


    return result



# ============================================================
# MEMBRANE WITH REAL CONTAINING FIELD
# ============================================================

def evaluate_cluster_with_boundary(
    engine,
    cluster_indices,
    receipt,
    beta=0.25,
    epsilon=0.20,
):
    """
    Evaluate persistence without confusing the local computational
    boundary with the end of reality.

    If exterior consequences are unresolved, persistence cannot be
    asserted.

    A dissolution conclusion can still be guaranteed when the known
    exterior already places the upper bound of M_C at or below 1,
    because additional external coupling can only increase the
    denominator.
    """

    cluster_indices = np.asarray(
        cluster_indices,
        dtype=int,
    )

    N_C = len(
        cluster_indices
    )


    if N_C <= 1:

        return {
            "M_C":
                0.0,

            "M_C_upper":
                0.0,

            "status":
                "DISSOLVED",

            "K_int":
                0.0,

            "K_ext_known":
                0.0,

            "R_C":
                0.0,

            "external_resolved":
                bool(
                    receipt.resolved
                ),
        }


    W, _ = (
        engine.compute_coupling()
    )


    W_sub = W[
        np.ix_(
            cluster_indices,
            cluster_indices,
        )
    ]


    rho_C = (
        np.sum(
            W_sub
        )
        /
        (
            N_C
            *
            (
                N_C
                - 1
            )
        )
    )


    K_int = (
        (
            N_C
            - 1
        )
        *
        rho_C
    )


    mask_ext = np.ones(
        engine.N,
        dtype=bool,
    )

    mask_ext[
        cluster_indices
    ] = False


    K_ext_local = (
        np.sum(
            W[
                np.ix_(
                    cluster_indices,
                    mask_ext,
                )
            ]
        )
        /
        N_C
    )


    coupling_mass = np.asarray(
        receipt.coupling_mass,
        dtype=np.float64,
    )


    if coupling_mass.shape != (
        engine.N,
    ):

        raise ValueError(
            "receipt.coupling_mass has wrong shape."
        )


    K_ext_parent_known = float(
        np.mean(
            coupling_mass[
                cluster_indices
            ]
        )
    )


    K_ext_known = (
        float(
            K_ext_local
        )
        +
        K_ext_parent_known
    )


    R_C = float(
        np.mean(
            engine.R[
                cluster_indices
            ]
        )
    )


    M_C_upper = float(
        K_int
        /
        (
            K_ext_known
            +
            beta
            * R_C
            +
            epsilon
        )
    )


    # --------------------------------------------------------
    # Exterior resolved: ordinary verdict is permitted
    # --------------------------------------------------------

    if receipt.resolved:

        status = (
            "PERSISTENT"
            if
            M_C_upper > 1.0
            else
            "CRITICAL_DISSOLUTION"
        )

        return {
            "M_C":
                M_C_upper,

            "M_C_upper":
                M_C_upper,

            "status":
                status,

            "K_int":
                float(
                    K_int
                ),

            "K_ext_known":
                float(
                    K_ext_known
                ),

            "R_C":
                R_C,

            "external_resolved":
                True,
        }


    # --------------------------------------------------------
    # Exterior unresolved
    # --------------------------------------------------------

    if M_C_upper <= 1.0:

        status = (
            "CRITICAL_DISSOLUTION_GUARANTEED"
        )

    else:

        status = (
            "UNKNOWN_EXTERNAL_FIELD"
        )


    return {
        "M_C":
            None,

        "M_C_upper":
            M_C_upper,

        "status":
            status,

        "K_int":
            float(
                K_int
            ),

        "K_ext_known":
            float(
                K_ext_known
            ),

        "R_C":
            R_C,

        "external_resolved":
            False,
    }
