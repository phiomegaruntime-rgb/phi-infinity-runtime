"""
Minimal PHI-INFINITY AccessPointer demonstration.
"""
import numpy as np
from src.core import PhiSubstrateEngine
from src.field_bridge import AccessPointer, AccessibleField, FieldBridge

def create_demo_field():
    n_nodes = 4
    x0 = np.array([[0.0, 0.0], [0.1, 0.05], [5.0, 5.0], [5.1, 5.0]], dtype=np.float64)
    engine = PhiSubstrateEngine(n_nodes=n_nodes, seed=42)
    engine.pos = np.copy(x0)
    engine.S = np.array([
        [1.50, 1.20, 1.00], [1.40, 1.15, 0.95],
        [0.50, 0.50, 0.50], [0.50, 0.50, 0.50]
    ], dtype=np.float64)

    for i in range(n_nodes):
        engine.R[i] = abs((engine.S[i, 0] / (engine.S[i, 1] + 1e-5)) - 1.0)

    history = [np.copy(engine.pos)]
    for _ in range(3):
        engine.step()
        history.append(np.copy(engine.pos))

    return AccessibleField(history)

def main():
    print("=== PHI-INFINITY ACCESSPOINTER DEMO ===")
    field = create_demo_field()
    pointer = AccessPointer(
        source_id="DemoObservation",
        spatial_span=(-0.5, 1.0, -0.5, 1.0),
        time_window=(0, -1),
        label_metadata="ARBITRARY_HUMAN_LABEL"
    )
    bridge = FieldBridge()
    result = bridge.process_pointer(pointer, field)
    print(result["human_synthesis"])
    if "resolution_scope" in result:
        print("Resolution scope:", result["resolution_scope"])

if __name__ == "__main__":
    main()
