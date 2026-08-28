"""
PHI-INFINITY (Phi-Infinity) - Core Invariant Engine
Author: Massimiliano Brighindi (2026)
"""
import numpy as np

class PhiSubstrateEngine:
    def __init__(self, n_nodes=60, sigma=1.2, alpha=0.04, beta=0.25, lmbda=0.01, gamma=0.3, mu=0.05, eta=0.01, seed=42):
        self.N = n_nodes
        self.sigma = sigma
        self.alpha = alpha
        self.beta = beta
        self.lmbda = lmbda
        self.gamma = gamma
        self.mu = mu
        self.eta = eta
        rng = np.random.RandomState(seed)
        self.pos = rng.uniform(-3.0, 3.0, size=(n_nodes, 2))
        self.S = np.column_stack([
            rng.uniform(1.0, 5.0, size=n_nodes),
            rng.uniform(1.0, 5.0, size=n_nodes),
            rng.uniform(0.5, 1.5, size=n_nodes)
        ])
        self.R = np.zeros(n_nodes)

    def compute_coupling(self):
        diff = self.pos[np.newaxis, :, :] - self.pos[:, np.newaxis, :]
        dist_sq = np.sum(diff**2, axis=-1)
        norm_S = np.linalg.norm(self.S, axis=1, keepdims=True)
        affinity = np.clip((self.S @ self.S.T) / (norm_S @ norm_S.T + 1e-8), 0.0, 1.0)
        W = np.exp(-dist_sq / (2 * (self.sigma**2))) * affinity
        np.fill_diagonal(W, 0.0)
        return W, diff

    def step(self):
        W, diff = self.compute_coupling()
        flow_e = np.sum(W * np.tanh(self.gamma * (self.S[:, 0:1].T - self.S[:, 0:1])), axis=1)
        flow_r = np.sum(W * np.tanh(self.gamma * (self.S[:, 1:2].T - self.S[:, 1:2])), axis=1)
        prev_S = self.S.copy()
        self.S[:, 0] = np.maximum(0.01, self.S[:, 0] + self.mu * flow_e)
        self.S[:, 1] = np.maximum(0.01, self.S[:, 1] + self.mu * flow_r)
        d_tau = np.linalg.norm(self.S - prev_S, axis=1)
        incomp = np.abs((self.S[:, 0] / (self.S[:, 1] + 1e-3)) - 1.0)
        self.R = (1.0 - self.lmbda * d_tau) * self.R + self.alpha * (incomp**2) * d_tau
        force = W[:, :, np.newaxis] * (1.0 - self.beta * self.R[:, np.newaxis, np.newaxis])
        self.pos += np.sum(force * diff, axis=1) * self.eta
        return {
            "mean_energy": float(np.mean(self.S[:, 0])),
            "energy_variance": float(np.std(self.S[:, 0])),
            "mean_stress": float(np.mean(self.R)),
            "max_stress": float(np.max(self.R)),
            "mean_dtau": float(np.mean(d_tau))
        }
