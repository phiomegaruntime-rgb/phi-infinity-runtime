from src.core import PhiSubstrateEngine
from src.membrane import MembraneEvaluator
from src.gating import MultiAccessGating, FirstDivergenceException
from src.translator import PhiBidirectionalTranslator

def run_pipeline():
    print("=== PHI-INFINITY: END-TO-END BIDIRECTIONAL PIPELINE ===")
    translator = PhiBidirectionalTranslator()
    
    # 1. Ingestione & De-costruzione (T_H_Phi)
    prompt_entity = "Fronte Dinamico Alpha"
    print(f"\n[1. Ingestione T_H_Phi] Decostruzione concetto: '{prompt_entity}'")
    node_mapping = translator.deconstruct_human_to_phi(prompt_entity, is_rigid_statement=True, energy_bias=3.5, resource_bias=1.2)
    print(f" -> Mappatura: {node_mapping['mapped_to']} | R_i iniziale: {node_mapping['initial_Ri']:.2f}")

    # 2. Evoluzione Deterministica nel Substrato
    print("\n[2. Evoluzione Substrato Phi] Esecuzione cicli deterministici...")
    engine = PhiSubstrateEngine(n_nodes=60, seed=42)
    evaluator = MembraneEvaluator(beta=0.25)
    gating = MultiAccessGating(acceptance_predicate=lambda m: m["mean_stress"] < 0.5)
    
    cluster = list(range(15))
    engine.R[cluster] = node_mapping["initial_Ri"]  # Assegnazione dello stress iniziale decostruito

    for cycle in range(1, 31):
        metrics = engine.step()
        try:
            gating.check_trajectory(metrics, cycle)
        except FirstDivergenceException as e:
            print(f" -> {e}")
            gating.trigger_reopen()
            break

    memb = evaluator.evaluate_cluster(engine, cluster)

    # 3. Traduzione Anti-Allucinazione (T_Phi_H)
    print("\n[3. Traduzione T_Phi_H] Output deterministico nel linguaggio naturale:")
    human_verdict = translator.translate_phi_to_human(
        M_C=memb["M_C"],
        R_C=memb["R_C"],
        d_tau=metrics["mean_dtau"],
        K_ext=memb["K_ext"],
        K_int=memb["K_int"],
        name=prompt_entity
    )
    print(f" -> {human_verdict}")

if __name__ == "__main__":
    run_pipeline()
