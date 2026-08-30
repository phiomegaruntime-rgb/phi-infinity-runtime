
import numpy as np


def infer_common_rhythm(
    rates,
    observed=None,
):

    rates = np.asarray(
        rates,
        dtype=float,
    )

    n_fields, n_processes = (
        rates.shape
    )

    if observed is None:

        observed = np.isfinite(
            rates
        )

    else:

        observed = (
            np.asarray(
                observed,
                dtype=bool,
            )
            &
            np.isfinite(
                rates
            )
        )

    if np.any(
        rates[observed] <= 0.0
    ):

        raise ValueError(
            "Observed rates must be positive."
        )

    rows = []
    targets = []

    for i in range(
        n_fields
    ):

        for k in range(
            n_processes
        ):

            if not observed[i, k]:
                continue

            row = np.zeros(
                (n_fields - 1)
                +
                n_processes
            )

            if i > 0:
                row[i - 1] = 1.0

            row[
                (n_fields - 1)
                +
                k
            ] = 1.0

            rows.append(
                row
            )

            targets.append(
                np.log(
                    rates[i, k]
                )
            )

    if not rows:

        return {
            "status":
                "UNRESOLVED_NO_ACCESS"
        }

    A = np.vstack(
        rows
    )

    y = np.asarray(
        targets
    )

    required_rank = (
        n_fields
        +
        n_processes
        -
        1
    )

    rank = np.linalg.matrix_rank(
        A
    )

    if rank < required_rank:

        return {
            "status":
                "UNRESOLVED_DISCONNECTED_ACCESS",

            "rank":
                int(rank),

            "required_rank":
                int(required_rank),
        }

    solution = np.linalg.lstsq(
        A,
        y,
        rcond=None,
    )[0]

    a = np.zeros(
        n_fields
    )

    a[1:] = solution[
        :n_fields - 1
    ]

    b = solution[
        n_fields - 1:
    ]

    rho = np.exp(
        a
    )

    kappa = np.exp(
        b
    )

    residual = (
        y
        -
        A @ solution
    )

    relative_residual = np.abs(
        np.exp(residual)
        -
        1.0
    )

    q = (
        rho[:, None]
        /
        rho[None, :]
    )

    return {
        "status":
            "CONNECTED_TEMPORAL_FACTOR_TEST",

        "rho":
            rho,

        "kappa":
            kappa,

        "q":
            q,

        "max_relative_residual":
            float(
                np.max(
                    relative_residual
                )
            ),
    }


print("=" * 78)
print("PHI-INFINITY — RHO EMERGENCE VALIDATION GATE")
print("=" * 78)


hidden_rho = np.array(
    [
        1.00,
        0.70,
        1.30,
        2.20,
        0.42,
    ]
)


process_rates = np.array(
    [
        0.5,
        1.7,
        4.2,
        9.1,
    ]
)


rates = (
    hidden_rho[:, None]
    *
    process_rates[None, :]
)


expected = (
    hidden_rho
    /
    hidden_rho[0]
)


# A
a = infer_common_rhythm(
    rates
)

assert np.allclose(
    a["rho"],
    expected,
    rtol=1e-12,
    atol=1e-12,
)

assert (
    a["max_relative_residual"]
    <
    1e-12
)

print(
    "A PASS — blind common-factor recovery"
)


# B
wild = np.array(
    [
        1e-5,
        0.3,
        17.0,
        8e4,
        2e8,
    ]
)


b = infer_common_rhythm(
    hidden_rho[:, None]
    *
    wild[None, :]
)


assert np.allclose(
    b["rho"],
    expected,
    rtol=1e-11,
    atol=1e-11,
)


print(
    "B PASS — independent of intrinsic process speed"
)


# C
c = infer_common_rhythm(
    rates / 7.314159265
)


assert np.allclose(
    a["q"],
    c["q"],
    rtol=1e-12,
    atol=1e-12,
)


print(
    "C PASS — gauge / reparameterization invariance"
)


# D
row_perm = np.array(
    [
        3,
        0,
        4,
        1,
        2,
    ]
)


col_perm = np.array(
    [
        2,
        0,
        3,
        1,
    ]
)


d = infer_common_rhythm(
    rates[
        row_perm
    ][
        :,
        col_perm
    ]
)


inverse_rows = np.argsort(
    row_perm
)


rho_unpermuted = d["rho"][
    inverse_rows
]


q_unpermuted = (
    rho_unpermuted[:, None]
    /
    rho_unpermuted[None, :]
)


q_expected = (
    expected[:, None]
    /
    expected[None, :]
)


assert np.allclose(
    q_unpermuted,
    q_expected,
    rtol=1e-12,
    atol=1e-12,
)


print(
    "D PASS — label/order invariance"
)


# E
mask = np.zeros_like(
    rates,
    dtype=bool,
)


for edge in [
    (0, 0),
    (0, 1),
    (1, 0),
    (1, 2),
    (2, 1),
    (2, 3),
    (3, 2),
    (3, 3),
    (4, 0),
    (4, 3),
]:

    mask[edge] = True


e = infer_common_rhythm(
    rates,
    mask,
)


assert np.allclose(
    e["rho"],
    expected,
    rtol=1e-11,
    atol=1e-11,
)


print(
    "E PASS — partial connected access"
)


# F
disconnected = np.zeros_like(
    rates,
    dtype=bool,
)


for edge in [
    (0, 0),
    (1, 0),
    (0, 1),
    (1, 1),
    (2, 2),
    (3, 2),
    (4, 3),
    (3, 3),
    (4, 2),
]:

    disconnected[edge] = True


f = infer_common_rhythm(
    rates,
    disconnected,
)


assert (
    f["status"]
    ==
    "UNRESOLVED_DISCONNECTED_ACCESS"
)


print(
    "F PASS — disconnected access -> UNRESOLVED"
)


# G
broken = rates.copy()

broken[
    3,
    2
] *= 1.17


g = infer_common_rhythm(
    broken
)


assert (
    g["max_relative_residual"]
    >
    1e-3
)


print(
    "G PASS — incompatible scalar rhythm rejected"
)


# H
rho_A = np.array(
    [
        1.0,
        0.8,
        1.2,
        1.5,
        0.7,
    ]
)


rho_B = np.array(
    [
        1.0,
        1.1,
        0.9,
        1.6,
        0.6,
    ]
)


composite = np.column_stack(
    [
        rho_A[:, None]
        *
        np.array(
            [
                1.2,
                3.4,
            ]
        )[None, :],

        rho_B[:, None]
        *
        np.array(
            [
                2.1,
                5.7,
            ]
        )[None, :],
    ]
)


h = infer_common_rhythm(
    composite
)


assert (
    h["max_relative_residual"]
    >
    1e-3
)


print(
    "H PASS — composite not forced into one clock"
)


# I
rho = a["rho"]


cycle = (
    rho[0] / rho[1]
    *
    rho[1] / rho[2]
    *
    rho[2] / rho[0]
)


assert np.isclose(
    cycle,
    1.0,
    rtol=1e-12,
    atol=1e-12,
)


broken_cycle = (
    cycle
    *
    1.01
)


assert not np.isclose(
    broken_cycle,
    1.0,
    rtol=1e-6,
    atol=1e-6,
)


print(
    "I PASS — scalar temporal cycle consistency"
)


print()
print(
    "RHO EMERGENCE GATE PASS"
)

print(
    "Interpretation limited to mathematical "
    "identifiability/falsifiability."
)

print(
    "This does NOT prove physical universality."
)
