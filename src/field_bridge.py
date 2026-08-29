"""
PHI-INFINITY: Field Bridge & AccessPointer Architecture
Core Principle:
  Human symbol -> AccessPointer -> Omega_A [symbol discarded] -> Phi Reconstruction -> T_Phi_H.
The symbol only locates the focal region; it never generates states, thresholds, or dynamics.
Author: Massimiliano Brighindi (2026)
"""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize
from src.core import PhiSubstrateEngine
from src.membrane import MembraneEvaluator

@dataclass(frozen=True)
class AccessPointer:
    """Ancora spazio-temporale: localizza la regione focale senza generare meccanica."""
    source_id: str
    spatial_span: tuple            # (x_min, x_max, y_min, y_max)
    time_window: tuple = (0, -1)   # [t_start, t_end]
    label_metadata: str | None = None

class AccessibleField:
    """Realtà osservabile accessibile: posizioni grezze nel tempo (history di pos)."""
    def __init__(self, time_series_positions):
        self.history = [np.asarray(frame, dtype=np.float64) for frame in time_series_positions]
        if len(self.history) < 2:
            raise ValueError("AccessibleField richiede almeno due fotogrammi temporali.")
        first_shape = self.history[0].shape
        if len(first_shape) != 2 or first_shape[1] < 2:
            raise ValueError("Ogni frame deve avere forma (N, >=2).")
        self.n_nodes = first_shape[0]

    def resolve_access(self, pointer: AccessPointer):
        t_start, t_end = pointer.time_window
        window_history = self.history[t_start:] if t_end == -1 else self.history[t_start:t_end + 1]
        if len(window_history) < 2:
            raise ValueError("La finestra temporale deve contenere almeno due fotogrammi.")
        
        terminal_positions = window_history[-1]
        x_min, x_max, y_min, y_max = pointer.spatial_span
        focal_nodes = []
        for i, pos in enumerate(terminal_positions):
            if x_min <= pos[0] <= x_max and y_min <= pos[1] <= y_max:
                focal_nodes.append(i)
        return focal_nodes, window_history

class FieldBridge:
    def __init__(self, beta=0.25, tol_loss=1e-2, search_upper_bound=10.0):
        self.beta = float(beta)
        self.tol_loss = float(tol_loss)
        self.search_upper_bound = float(search_upper_bound)
        self.evaluator = MembraneEvaluator(beta=self.beta)

    def _new_engine(self, n_nodes):
        engine = PhiSubstrateEngine(n_nodes=n_nodes, seed=1)
        engine.beta = self.beta
        return engine

    def _inverse_loss(self, z_flat, observed_window):
        x_initial = observed_window[0]
        n_nodes = x_initial.shape[0]
        s_size = n_nodes * 3
        S_initial = z_flat[:s_size].reshape((n_nodes, 3))
        R_initial = z_flat[s_size:]

        engine = self._new_engine(n_nodes)
        engine.pos = np.copy(x_initial)
        engine.S = np.copy(S_initial)
        engine.R = np.copy(R_initial)

        total_loss = 0.0
        for t in range(1, len(observed_window)):
            engine.step()
            diff = engine.pos - observed_window[t]
            total_loss += float(np.sum(diff * diff))
        return total_loss

    def reconstruct_phi_state(self, observed_window):
        n_nodes = observed_window[0].shape[0]
        s_size = n_nodes * 3
        upper = self.search_upper_bound
        bounds = [(0.01, upper)] * s_size + [(0.0, upper)] * n_nodes

        seeds = [
            np.concatenate([np.ones(s_size), np.zeros(n_nodes)]),
            np.concatenate([np.full(s_size, 1.5), np.full(n_nodes, 0.2)]),
            np.concatenate([np.full(s_size, 0.75), np.full(n_nodes, 0.1)]),
        ]

        results = []
        for s0 in seeds:
            res = minimize(
                self._inverse_loss,
                s0,
                args=(observed_window,),
                method="L-BFGS-B",
                bounds=bounds,
                options={"maxiter": 1000}
            )
            if np.isfinite(res.fun):
                results.append(res)

        if not results:
            return None

        best_res = min(results, key=lambda r: r.fun)
        if best_res.fun > self.tol_loss:
            return None

        S_initial = best_res.x[:s_size].reshape((n_nodes, 3))
        R_initial = best_res.x[s_size:]

        # Propagazione genealogica: Z_{-T} -> Z_0
        engine = self._new_engine(n_nodes)
        engine.pos = np.copy(observed_window[0])
        engine.S = np.copy(S_initial)
        engine.R = np.copy(R_initial)

        for _ in range(len(observed_window) - 1):
            engine.step()

        return {
            "terminal_pos": np.copy(engine.pos),
            "terminal_S": np.copy(engine.S),
            "terminal_R": np.copy(engine.R),
            "fit_loss": float(best_res.fun),
            "resolution_scope": "COMPATIBLE_WITHIN_EXPLORED_SEARCH_DOMAIN"
        }

    def process_pointer(self, pointer: AccessPointer, field: AccessibleField, future_horizon=10):
        try:
            focal_nodes, observed_window = field.resolve_access(pointer)
        except (ValueError, IndexError):
            return {"status": "UNKNOWN", "trajectory": [], "human_synthesis": "UNKNOWN: finestra temporale non valida."}

        if not focal_nodes:
            return {"status": "UNKNOWN", "trajectory": [], "human_synthesis": "UNKNOWN: nessun nodo nella regione del puntatore."}

        reconstruction = self.reconstruct_phi_state(observed_window)
        if reconstruction is None:
            return {"status": "UNRESOLVED_IN_SEARCH_DOMAIN", "trajectory": [], "human_synthesis": "UNRESOLVED: nessuno stato compatibile trovato."}

        # La continuazione futura inizia da Z_0
        engine = self._new_engine(field.n_nodes)
        engine.pos = np.copy(reconstruction["terminal_pos"])
        engine.S = np.copy(reconstruction["terminal_S"])
        engine.R = np.copy(reconstruction["terminal_R"])

        trajectory = []
        for cycle in range(future_horizon):
            m = engine.step()
            memb = self.evaluator.evaluate_cluster(engine, focal_nodes)
            W, _ = engine.compute_coupling()
            trajectory.append({
                "cycle": cycle,
                "M_C": float(memb["M_C"]),
                "R_C": float(memb["R_C"]),
                "d_tau": float(m["mean_dtau"]),
                "S": np.copy(engine.S),
                "R": np.copy(engine.R),
                "W": np.copy(W)
            })

        final_memb = self.evaluator.evaluate_cluster(engine, focal_nodes)
        final_mc = float(final_memb["M_C"])
        final_rc = float(final_memb["R_C"])
        final_dtau = float(trajectory[-1]["d_tau"])
        status = "PERSISTENT" if final_mc > 1.0 else "REORGANIZING"

        human_synth = f"REGION {focal_nodes}: status={status}, M_C={final_mc:.6f}, R_C={final_rc:.6f}, d_tau={final_dtau:.6f}."

        return {
            "status": status,
            "focal_nodes": list(focal_nodes),
            "M_C": final_mc,
            "R_C": final_rc,
            "fit_loss": reconstruction["fit_loss"],
            "resolution_scope": reconstruction["resolution_scope"],
            "trajectory": trajectory,
            "human_synthesis": human_synth
        }
