"""
Fundamental PHI-INFINITY bridge benchmarks.
"""
import numpy as np
from src.core import PhiSubstrateEngine
from src.field_bridge import AccessPointer, AccessibleField, FieldBridge

def generate_sample_field(variant="A"):
    n_nodes = 4
    x0 = np.array([
        [0.0, 0.0], [0.1, 0.05], [5.0, 5.0], [5.1, 5.0]
    ], dtype=np.float64)

    engine = PhiSubstrateEngine(n_nodes=n_nodes, seed=42)
    engine.pos = np.copy(x0)

    if variant == "A":
        engine.S = np.array([
            [1.50, 1.20, 1.00], [1.40, 1.15, 0.95],
            [0.50, 0.50, 0.50], [0.50, 0.50, 0.50]
        ], dtype=np.float64)
    elif variant == "B":
        engine.S = np.array([
            [1.15, 1.50, 0.85], [1.05, 1.40, 1.10],
            [0.55, 0.45, 0.60], [0.45, 0.60, 0.40]
        ], dtype=np.float64)
    else:
        raise ValueError(f"Variante non valida: {variant}")

    for i in range(n_nodes):
        e_i, r_i = engine.S[i, 0], engine.S[i, 1]
        engine.R[i] = abs((e_i / (r_i + 1e-5)) - 1.0)

    history = [np.copy(engine.pos)]
    for _ in range(3):
        engine.step()
        history.append(np.copy(engine.pos))

    return AccessibleField(history)

def assert_same_phi_trajectory(result_a, result_b):
    assert result_a["status"] == result_b["status"]
    assert result_a["focal_nodes"] == result_b["focal_nodes"]
    assert result_a["M_C"] == result_b["M_C"]
    assert result_a["R_C"] == result_b["R_C"]
    assert len(result_a["trajectory"]) == len(result_b["trajectory"])

    for step_a, step_b in zip(result_a["trajectory"], result_b["trajectory"]):
        assert step_a["M_C"] == step_b["M_C"]
        assert step_a["R_C"] == step_b["R_C"]
        assert step_a["d_tau"] == step_b["d_tau"]
        assert np.array_equal(step_a["S"], step_b["S"])
        assert np.array_equal(step_a["R"], step_b["R"])
        assert np.array_equal(step_a["W"], step_b["W"])

def test_label_invariance():
    field = generate_sample_field(variant="A")
    bridge = FieldBridge()

    pointer_a = AccessPointer(source_id="Stream1", spatial_span=(-0.5, 1.0, -0.5, 1.0), time_window=(0, -1), label_metadata="Banca")
    pointer_b = AccessPointer(source_id="Stream1", spatial_span=(-0.5, 1.0, -0.5, 1.0), time_window=(0, -1), label_metadata="Argine")
    pointer_c = AccessPointer(source_id="Stream1", spatial_span=(-0.5, 1.0, -0.5, 1.0), time_window=(0, -1), label_metadata="XYZ_TOKEN")

    res_a = bridge.process_pointer(pointer_a, field)
    res_b = bridge.process_pointer(pointer_b, field)
    res_c = bridge.process_pointer(pointer_c, field)

    assert res_a["status"] not in {"UNKNOWN", "UNRESOLVED_IN_SEARCH_DOMAIN"}
    assert res_b["status"] not in {"UNKNOWN", "UNRESOLVED_IN_SEARCH_DOMAIN"}
    assert res_c["status"] not in {"UNKNOWN", "UNRESOLVED_IN_SEARCH_DOMAIN"}

    assert_same_phi_trajectory(res_a, res_b)
    assert_same_phi_trajectory(res_a, res_c)

def test_field_dependence_without_preconceptions():
    field_a = generate_sample_field(variant="A")
    field_b = generate_sample_field(variant="B")
    bridge = FieldBridge()

    pointer = AccessPointer(source_id="Stream", spatial_span=(-0.5, 1.0, -0.5, 1.0), time_window=(0, -1), label_metadata="Banca")

    res_a = bridge.process_pointer(pointer, field_a)
    res_b = bridge.process_pointer(pointer, field_b)

    assert res_a["status"] not in {"UNKNOWN", "UNRESOLVED_IN_SEARCH_DOMAIN"}
    assert res_b["status"] not in {"UNKNOWN", "UNRESOLVED_IN_SEARCH_DOMAIN"}

    same_trajectory = True
    for step_a, step_b in zip(res_a["trajectory"], res_b["trajectory"]):
        same_step = (
            np.array_equal(step_a["S"], step_b["S"]) and
            np.array_equal(step_a["R"], step_b["R"]) and
            np.array_equal(step_a["W"], step_b["W"]) and
            step_a["M_C"] == step_b["M_C"] and
            step_a["R_C"] == step_b["R_C"] and
            step_a["d_tau"] == step_b["d_tau"]
        )
        if not same_step:
            same_trajectory = False
            break

    assert not same_trajectory
