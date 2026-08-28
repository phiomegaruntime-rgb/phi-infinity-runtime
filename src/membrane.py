"""
PHI-INFINITY (Phi-Infinity) - Membrane & Topology Evaluator
Author: Massimiliano Brighindi (2026)
"""
import numpy as np

class MembraneEvaluator:
    def __init__(self, beta=0.25, epsilon=0.20):
        self.beta = beta
        self.epsilon = epsilon

    def evaluate_cluster(self, engine, cluster_indices):
        N_C = len(cluster_indices)
        if N_C <= 1:
            return {"M_C": 0.0, "status": "DISSOLVED", "K_int": 0.0, "K_ext": 0.0, "R_C": 0.0}
        W, _ = engine.compute_coupling()
        W_sub = W[np.ix_(cluster_indices, cluster_indices)]
        rho_C = np.sum(W_sub) / (N_C * (N_C - 1))
        K_int = (N_C - 1) * rho_C
        mask_ext = np.ones(engine.N, dtype=bool)
        mask_ext[cluster_indices] = False
        K_ext = np.sum(W[np.ix_(cluster_indices, mask_ext)]) / N_C
        R_C = np.mean(engine.R[cluster_indices])
        M_C = K_int / (K_ext + self.beta * R_C + self.epsilon)
        status = "PERSISTENT" if M_C > 1.0 else "CRITICAL_DISSOLUTION"
        return {
            "M_C": float(M_C),
            "status": status,
            "K_int": float(K_int),
            "K_ext": float(K_ext),
            "R_C": float(R_C)
        }
