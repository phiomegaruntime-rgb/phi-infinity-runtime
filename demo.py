import numpy as np
import matplotlib.pyplot as plt
from src.core import PhiSubstrateEngine
from src.membrane import MembraneEvaluator

def run_demo():
    engine = PhiSubstrateEngine(n_nodes=60, seed=42)
    evaluator = MembraneEvaluator(beta=0.25)
    cluster = list(range(20))
    history = {"energy": [], "stress": [], "dtau": [], "m_c": []}
    initial_pos = engine.pos.copy()
    for _ in range(100):
        m = engine.step()
        memb = evaluator.evaluate_cluster(engine, cluster)
        history["energy"].append(m["mean_energy"])
        history["stress"].append(m["mean_stress"])
        history["dtau"].append(m["mean_dtau"])
        history["m_c"].append(memb["M_C"])
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    ax = axes[0, 0]
    ax.scatter(initial_pos[:, 0], initial_pos[:, 1], color="lightgray", label="t=0", alpha=0.7)
    sc = ax.scatter(engine.pos[:, 0], engine.pos[:, 1], c=engine.R, cmap="coolwarm", s=90, edgecolors="black", label="t=100")
    plt.colorbar(sc, ax=ax, label="Stress R_i")
    ax.set_title("Riconfigurazione Posizionale")
    ax.legend(); ax.grid(True, linestyle="--", alpha=0.5)
    ax = axes[0, 1]
    ax.plot(history["m_c"], color="darkblue", lw=2)
    ax.axhline(1.0, color="red", linestyle="--", label="Soglia Critica (1.0)")
    ax.set_title("Tenuta di Membrana M_C")
    ax.legend(); ax.grid(True, linestyle="--", alpha=0.5)
    ax = axes[1, 0]
    ax.plot(history["energy"], color="green", lw=2)
    ax.set_title("Energia Globale Media")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax = axes[1, 1]
    ax.plot(history["stress"], color="crimson", lw=2, label="Stress")
    ax.plot(history["dtau"], color="purple", linestyle=":", label="dtau")
    ax.set_title("Stress ed Attività")
    ax.legend(); ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig("simulation_plot.png", dpi=300)
    print("Grafico generato: simulation_plot.png")

if __name__ == "__main__":
    run_demo()
