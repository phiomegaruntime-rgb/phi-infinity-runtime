
import numpy as np

from src.core import PhiSubstrateEngine


def make_two_fragment_engine():
    engine = PhiSubstrateEngine(
        n_nodes=2,
        seed=1,
    )

    engine.pos = np.array(
        [
            [-1.0, 0.0],
            [ 1.0, 0.0],
        ],
        dtype=float,
    )

    # Equal represented structural values:
    # structural exchange must therefore be zero.
    engine.S[:, 0] = 2.0
    engine.S[:, 1] = 2.0
    engine.S[:, 2] = 1.0

    engine.R[:] = 0.0

    return engine


def test_geometry_can_change_while_structural_increment_is_zero():

    engine = make_two_fragment_engine()

    old_pos = engine.pos.copy()

    result = engine.step()

    structural = np.asarray(
        result["structural_path_increment"]
    )

    geometric_change = np.linalg.norm(
        engine.pos - old_pos
    )

    assert np.allclose(
        structural,
        0.0,
        atol=0.0,
        rtol=0.0,
    )

    assert geometric_change > 0.0

    assert (
        result["representation_status"]
        ==
        "REPRESENTED_TRANSFORMATION"
    )


def test_static_centroid_does_not_imply_internal_immobility():

    engine = make_two_fragment_engine()

    old_centroid = np.mean(
        engine.pos,
        axis=0,
    )

    old_distance = np.linalg.norm(
        engine.pos[1]
        -
        engine.pos[0]
    )

    engine.step()

    new_centroid = np.mean(
        engine.pos,
        axis=0,
    )

    new_distance = np.linalg.norm(
        engine.pos[1]
        -
        engine.pos[0]
    )

    assert np.allclose(
        new_centroid,
        old_centroid,
        atol=1e-15,
        rtol=0.0,
    )

    assert not np.isclose(
        new_distance,
        old_distance,
        atol=1e-15,
        rtol=0.0,
    )


def test_one_fragment_exact_stasis_is_only_representational():

    engine = PhiSubstrateEngine(
        n_nodes=1,
        seed=7,
    )

    old_pos = engine.pos.copy()
    old_S = engine.S.copy()
    old_R = engine.R.copy()

    result = engine.step()

    assert np.array_equal(
        engine.pos,
        old_pos,
    )

    assert np.array_equal(
        engine.S,
        old_S,
    )

    assert np.array_equal(
        engine.R,
        old_R,
    )

    assert (
        result["representation_status"]
        ==
        "NO_DISTINGUISHABLE_TRANSFORMATION_IN_CURRENT_REPRESENTATION"
    )


def test_public_step_result_contains_no_obsolete_proper_time_aliases():

    engine = PhiSubstrateEngine(
        n_nodes=4,
        seed=10,
    )

    result = engine.step()

    assert "d_tau" not in result
    assert "mean_dtau" not in result

    assert "structural_path_increment" in result
    assert "geometry_path_increment" in result
    assert "residual_path_increment" in result
