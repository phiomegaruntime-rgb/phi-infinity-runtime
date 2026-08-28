from src.core import PhiSubstrateEngine
from src.membrane import MembraneEvaluator
from src.gating import MultiAccessGating, FirstDivergenceException

def main():
    print("=== PHI-INFINITY RUNTIME ===")
    engine = PhiSubstrateEngine(n_nodes=60, seed=42)
    evaluator = MembraneEvaluator(beta=0.25)
    gating = MultiAccessGating(acceptance_predicate=lambda m: m["mean_stress"] < 0.5)
    print("Running 50 deterministic cycles...")
    for cycle in range(1, 51):
        metrics = engine.step()
        try:
            gating.check_trajectory(metrics, cycle)
        except FirstDivergenceException as e:
            print(e)
            gating.trigger_reopen()
            break
        if cycle % 10 == 0:
            memb = evaluator.evaluate_cluster(engine, list(range(15)))
            print(f"Cycle {cycle:02d} | Energy: {metrics['mean_energy']:.4f} | Stress: {metrics['mean_stress']:.4f} | M_C: {memb['M_C']:.3f}")
    print("Execution completed.")

if __name__ == "__main__":
    main()
