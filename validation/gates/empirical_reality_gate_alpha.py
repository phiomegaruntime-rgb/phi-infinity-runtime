import csv
import hashlib
from pathlib import Path

import numpy as np


print("=" * 78)
print("PHI-INFINITY — EMPIRICAL REALITY GATE ALPHA")
print("=" * 78)


ROOT = Path(__file__).resolve().parents[2]

DATA = (
    ROOT
    /
    "validation"
    /
    "data"
    /
    "empirical_reality_gate_alpha"
)


COOLING = (
    DATA
    /
    "cooling_okstate_sample.csv"
)

PENDULUM = (
    DATA
    /
    "overdamped_pendulum_arizona_archive.csv"
)


EXPECTED_COOLING_HASH = "ed717d68d0bcfc4fd0cff77f3ec226b10ffe76b5997ac42ecbac1bde2aaf0e0c"

EXPECTED_PENDULUM_HASH = "ae70376843f2171539fc08e8dc7fdc7dbd1da1b7c63722a454f75c3e793fde38"


N_BOOT = 1_000_000
N_PERM = 1_000_000

CHUNK_BOOT = 100_000
CHUNK_PERM = 50_000


def sha256_file(path):

    h = hashlib.sha256()

    h.update(
        path.read_bytes()
    )

    return h.hexdigest()


def read_csv(path):

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:

        reader = csv.reader(f)

        header = next(reader)

        rows = [
            [
                float(value)
                for value in row
            ]
            for row in reader
        ]

    return (
        header,
        np.asarray(
            rows, dtype =float,
        ),
    )


def regression_slope(
    x,
    y,
):

    xm = np.mean(x)
    ym = np.mean(y)

    return float(
        np.sum(
            (x - xm)
            *
            (y - ym)
        )
        /
        np.sum(
            (x - xm) ** 2
        )
    )


def bootstrap_slopes(
    x,
    y,
    *,
    seed,
):

    rng = np.random.default_rng(
        seed
    )

    samples = []

    negative = 0

    n = len(x)

    for done in range(
        0,
        N_BOOT,
        CHUNK_BOOT,
    ):

        m = min(
            CHUNK_BOOT,
            N_BOOT - done,
        )

        idx = rng.integers(
            0,
            n, size =(m, n),
        )

        xb = x[idx]
        yb = y[idx]

        xm = xb.mean(
            axis=1
        )

        ym = yb.mean(
            axis=1
        )

        xc = (
            xb
            -
            xm[:, None]
        )

        yc = (
            yb
            -
            ym[:, None]
        )

        denominator = np.sum(
            xc * xc,
            axis=1,
        )

        slopes = (
            np.sum(
                xc * yc,
                axis=1,
            )
            /
            denominator
        )

        samples.append(
            slopes
        )

        negative += int(
            np.sum(
                slopes < 0.0
            )
        )

    samples = np.concatenate(
        samples
    )

    ci = np.quantile(
        samples,
        [
            0.025,
            0.975,
        ],
    )

    return (
        negative,
        ci,
    )


def correlation(
    x,
    y,
):

    return float(
        np.corrcoef(
            x,
            y,
        )[0, 1]
    )


def bootstrap_correlations(
    x,
    y,
    *,
    seed,
):

    rng = np.random.default_rng(
        seed
    )

    positive = 0

    values = []

    n = len(x)

    for done in range(
        0,
        N_BOOT,
        CHUNK_BOOT,
    ):

        m = min(
            CHUNK_BOOT,
            N_BOOT - done,
        )

        idx = rng.integers(
            0,
            n, size =(m, n),
        )

        xb = x[idx]
        yb = y[idx]

        xm = xb.mean(
            axis=1
        )

        ym = yb.mean(
            axis=1
        )

        xc = (
            xb
            -
            xm[:, None]
        )

        yc = (
            yb
            -
            ym[:, None]
        )

        denominator = np.sqrt(
            np.sum(
                xc * xc,
                axis=1,
            )
            *
            np.sum(
                yc * yc,
                axis=1,
            )
        )

        r = (
            np.sum(
                xc * yc,
                axis=1,
            )
            /
            denominator
        )

        values.append(
            r
        )

        positive += int(
            np.sum(
                r > 0.0
            )
        )

    values = np.concatenate(
        values
    )

    ci = np.quantile(
        values,
        [
            0.025,
            0.975,
        ],
    )

    return (
        positive,
        ci,
    )


def permutation_absolute_correlation(
    x,
    y,
    *,
    seed,
):

    rng = np.random.default_rng(
        seed
    )

    observed = abs(
        correlation(
            x,
            y,
        )
    )

    x_centered = (
        x
        -
        np.mean(x)
    )

    xx = np.sum(
        x_centered
        *
        x_centered
    )

    exceed = 0

    n = len(y)

    for done in range(
        0,
        N_PERM,
        CHUNK_PERM,
    ):

        m = min(
            CHUNK_PERM,
            N_PERM - done,
        )

        # Random keys generate independent row-wise
        # permutations without Python-level inner loops.
        keys = rng.random(
            (
                m,
                n,
            )
        )

        index = np.argsort(
            keys, axis =1,
        )

        yp = y[index]

        yp_centered = (
            yp
            -
            yp.mean(
                axis=1
            )[:, None]
        )

        denominator = np.sqrt(
            xx
            *
            np.sum(
                yp_centered
                *
                yp_centered, axis =1,
            )
        )

        r = (
            np.sum(
                yp_centered
                *
                x_centered[None, :],
                axis=1,
            )
            /
            denominator
        )

        exceed += int(
            np.sum(
                np.abs(r)
                >=
                observed
            )
        )

    return (
        exceed,
        exceed / N_PERM,
    )


# ============================================================
# SOURCE-ID GATES
# ============================================================

print()
print("--- Source-table identity ---")


actual_cooling_hash = sha256_file(
    COOLING
)

actual_pendulum_hash = sha256_file(
    PENDULUM
)


print(
    "Cooling :",
    actual_cooling_hash,
)

print(
    "Pendulum:",
    actual_pendulum_hash,
)


assert (
    actual_cooling_hash
    ==
    EXPECTED_COOLING_HASH
)


assert (
    actual_pendulum_hash
    ==
    EXPECTED_PENDULUM_HASH
)


print(
    "✅ Transcribed empirical tables unchanged"
)


# ============================================================
# A. COOLING
# ============================================================

print()
print("=" * 78)
print("DIRECT EMPIRICAL GATE A — COOLING")
print("=" * 78)


header_c, cool = read_csv(
    COOLING
)


time_c = cool[:, 0]
temperature = cool[:, 1]

room_temperature = 23.9


assert len(
    temperature
) == 30


delta_temperature = np.diff(
    temperature
)


decreases = int(
    np.sum(
        delta_temperature < 0.0
    )
)

increases = int(
    np.sum(
        delta_temperature > 0.0
    )
)


print(
    "Observations:",
    len(temperature),
)

print(
    "Decreasing intervals:",
    decreases,
)

print(
    "Increasing intervals:",
    increases,
)


assert decreases == 23
assert increases == 6


slope_c = regression_slope(
    time_c,
    temperature,
)


print(
    "Observed global slope:",
    slope_c,
)


assert slope_c < 0.0


negative_c, slope_ci_c = bootstrap_slopes(
    time_c,
    temperature, seed =20260830,
)


print(
    "Negative bootstrap slopes:",
    negative_c,
    "/",
    N_BOOT,
)

print(
    "95% bootstrap slope interval:",
    slope_ci_c.tolist(),
)


assert negative_c == N_BOOT

assert slope_ci_c[1] < 0.0


# Accessible field difference at each interval start.
field_difference = (
    temperature[:-1]
    -
    room_temperature
)


# Positive means temperature was lost during the
# next sampling interval.
next_change = (
    temperature[:-1]
    -
    temperature[1:]
)


r_c = correlation(
    field_difference,
    next_change,
)


print(
    "Correlation: field difference vs next change:",
    r_c,
)


assert r_c > 0.45


positive_c, corr_ci_c = bootstrap_correlations(
    field_difference,
    next_change, seed =20260831,
)


positive_fraction_c = (
    positive_c
    /
    N_BOOT
)


print(
    "Positive correlation bootstraps:",
    positive_c,
    "/",
    N_BOOT,
)

print(
    "Positive fraction:",
    positive_fraction_c,
)

print(
    "95% correlation interval:",
    corr_ci_c.tolist(),
)


assert positive_fraction_c > 0.998


perm_count_c, perm_p_c = permutation_absolute_correlation(
    field_difference,
    next_change, seed =20260833,
)


print(
    "Absolute-correlation permutation exceedances:",
    perm_count_c,
    "/",
    N_PERM,
)

print(
    "Permutation fraction:",
    perm_p_c,
)


assert perm_p_c < 0.02


print(
    "✅ COOLING EMPIRICAL GATE PASS"
)


# ============================================================
# B. OVERDAMPED PENDULUM
# ============================================================

print()
print("=" * 78)
print("DIRECT EMPIRICAL GATE B — OVERDAMPED PENDULUM")
print("=" * 78)


header_p, pend = read_csv(
    PENDULUM
)


time_p = pend[:, 0]
amplitude = pend[:, 1]


assert len(
    amplitude
) == 27


delta_amplitude = np.diff(
    amplitude
)


decreasing_p = int(
    np.sum(
        delta_amplitude < 0.0
    )
)


print(
    "Observations:",
    len(amplitude),
)

print(
    "Decreasing intervals:",
    decreasing_p,
    "/",
    len(amplitude) - 1,
)


assert decreasing_p == 26


slope_p = regression_slope(
    time_p,
    amplitude,
)


print(
    "Observed global slope:",
    slope_p,
)


assert slope_p < 0.0


negative_p, slope_ci_p = bootstrap_slopes(
    time_p,
    amplitude, seed =20260830,
)


print(
    "Negative bootstrap slopes:",
    negative_p,
    "/",
    N_BOOT,
)

print(
    "95% bootstrap slope interval:",
    slope_ci_p.tolist(),
)


assert negative_p == N_BOOT
assert slope_ci_p[1] < 0.0


# This is explicitly a RATE:
#
# local amplitude loss divided by the
# unequal measurement-time interval.
local_loss_rate = (
    (
        amplitude[:-1]
        -
        amplitude[1:]
    )
    /
    (
        time_p[1:]
        -
        time_p[:-1]
    )
)


present_amplitude = amplitude[:-1]


r_p = correlation(
    present_amplitude,
    local_loss_rate,
)


print(
    "Correlation: present amplitude vs local loss rate:",
    r_p,
)


assert r_p > 0.87


positive_p, corr_ci_p = bootstrap_correlations(
    present_amplitude,
    local_loss_rate, seed =20260836,
)


positive_fraction_p = (
    positive_p
    /
    N_BOOT
)


print(
    "Positive correlation bootstraps:",
    positive_p,
    "/",
    N_BOOT,
)

print(
    "Positive fraction:",
    positive_fraction_p,
)

print(
    "95% correlation interval:",
    corr_ci_p.tolist(),
)


assert positive_fraction_p == 1.0


perm_count_p, perm_p_p = permutation_absolute_correlation(
    present_amplitude,
    local_loss_rate, seed =20260837,
)


print(
    "Absolute-correlation permutation exceedances:",
    perm_count_p,
    "/",
    N_PERM,
)

print(
    "Permutation fraction:",
    perm_p_p,
)


assert perm_count_p == 0


print(
    "✅ OVERDAMPED PENDULUM EMPIRICAL GATE PASS"
)


# ============================================================
# C. PHI INTERPRETATION BOUNDARY
# ============================================================

print()
print("=" * 78)
print("EMPIRICAL REALITY GATE ALPHA — CLASSIFICATION")
print("=" * 78)

print()

print(
    "DIRECTLY REPROCESSED:"
)

print(
    "  • 30-point cooling table"
)

print(
    "  • 27-point overdamped-pendulum table"
)

print(
    "  • 6,000,000 total statistical resampling checks"
)

print()

print(
    "IMPORTANT:"
)

print(
    "  6,000,000 resampling checks"
)

print(
    "  != 6,000,000 independent physical experiments"
)

print()

print(
    "SUPPORTED:"
)

print(
    "  • accessible field/configuration differences"
)

print(
    "    are associated with different subsequent changes"
)

print(
    "    in these two empirical records"
)

print()

print(
    "NOT SUPPORTED BY THIS GATE:"
)

print(
    "  • universal proof of PHI-INFINITY"
)

print(
    "  • unique derivation of standard physical laws"
)

print(
    "  • proof that no undiscovered mechanics exists"
)

print(
    "  • treating compatibility as quantitative prediction"
)

print()

print(
    "MOTHER MECHANICS STATUS:"
)

print(
    "  NO SECOND FUNDAMENTAL OPERATION REQUIRED"
)

print(
    "  WITHIN THESE TWO DIRECT EMPIRICAL FAMILIES"
)

print()

print(
    "✅ EMPIRICAL REALITY GATE ALPHA PASS"
)
