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

    def _step_phi_mechanics(self):
        W, diff = self.compute_coupling()
        flow_e = np.sum(W * np.tanh(self.gamma * (self.S[:, 0:1].T - self.S[:, 0:1])), axis=1)
        flow_r = np.sum(W * np.tanh(self.gamma * (self.S[:, 1:2].T - self.S[:, 1:2])), axis=1)
        prev_S = self.S.copy()
        self.S[:, 0] = np.maximum(0.01, self.S[:, 0] + self.mu * flow_e)
        self.S[:, 1] = np.maximum(0.01, self.S[:, 1] + self.mu * flow_r)
        structural_path_increment = np.linalg.norm(self.S - prev_S, axis=1)
        incomp = np.abs((self.S[:, 0] / (self.S[:, 1] + 1e-3)) - 1.0)
        self.R = (1.0 - self.lmbda * structural_path_increment) * self.R + self.alpha * (incomp**2) * structural_path_increment
        force = W[:, :, np.newaxis] * (1.0 - self.beta * self.R[:, np.newaxis, np.newaxis])
        self.pos += np.sum(force * diff, axis=1) * self.eta
        return {
            "mean_energy": float(np.mean(self.S[:, 0])),
            "energy_variance": float(np.std(self.S[:, 0])),
            "mean_stress": float(np.mean(self.R)),
            "max_stress": float(np.max(self.R)),
            "mean_structural_path_increment": float(np.mean(structural_path_increment))
        }

    def step(
        self,
        mechanical_progress=1.0,
    ):
        """
        Traverse the existing PHI mechanics using a neutral
        mechanical-progress coordinate.

        mechanical_progress is NOT universal time and NOT proper time.

        mechanical_progress=1.0 reproduces the pre-integration
        mechanics exactly.

        The underlying PHI equations remain in _step_phi_mechanics().
        """

        try:
            progress = float(
                mechanical_progress
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "mechanical_progress must be a finite "
                "strictly positive scalar."
            ) from exc


        if (
            not np.isfinite(
                progress
            )
            or
            progress <= 0.0
        ):

            raise ValueError(
                "mechanical_progress must be finite "
                "and strictly positive."
            )


        prev_pos = self.pos.copy()
        prev_S = self.S.copy()
        prev_R = self.R.copy()


        original_mu = self.mu
        original_eta = self.eta


        try:

            # Same mechanics, different amount of numerical
            # traversal along its trajectory.
            self.mu = (
                original_mu
                *
                progress
            )

            self.eta = (
                original_eta
                *
                progress
            )


            result = (
                self._step_phi_mechanics()
            )


        finally:

            self.mu = original_mu
            self.eta = original_eta


        if not isinstance(
            result,
            dict,
        ):

            raise TypeError(
                "_step_phi_mechanics() must return a dict."
            )


        result = dict(
            result
        )


        structural_path_increment = (
            np.linalg.norm(
                self.S
                -
                prev_S,
                axis=1,
            )
        )


        geometry_path_increment = (
            np.linalg.norm(
                self.pos
                -
                prev_pos,
                axis=1,
            )
        )


        residual_path_increment = (
            np.abs(
                self.R
                -
                prev_R
            )
        )


        represented_transformation = bool(
            np.any(
                structural_path_increment
                !=
                0.0
            )
            or
            np.any(
                geometry_path_increment
                !=
                0.0
            )
            or
            np.any(
                residual_path_increment
                !=
                0.0
            )
        )


        result[
            "mechanical_progress"
        ] = progress


        result[
            "structural_path_increment"
        ] = (
            structural_path_increment.copy()
        )


        result[
            "mean_structural_path_increment"
        ] = float(
            np.mean(
                structural_path_increment
            )
        )


        result[
            "geometry_path_increment"
        ] = (
            geometry_path_increment.copy()
        )


        result[
            "residual_path_increment"
        ] = (
            residual_path_increment.copy()
        )


        result[
            "representation_status"
        ] = (
            "REPRESENTED_TRANSFORMATION"
            if represented_transformation
            else
            (
                "NO_DISTINGUISHABLE_TRANSFORMATION_"
                "IN_CURRENT_REPRESENTATION"
            )
        )


        # Explicitly prevent obsolete aliases from escaping.
        result.pop(
            "d_tau",
            None,
        )

        result.pop(
            "mean_dtau",
            None,
        )


        return result
