"""PHI-INFINITY multi-access gate (Massimiliano Brighindi, 2026).

Independent review contribution: fail closed on *predicate evaluation errors*.
The predicate remains externally supplied; neither this module nor REOPEN
proves independent support, provenance, or a valid physical interval.
"""


class FirstDivergenceException(Exception):
    """Trajectory check refused, or gate locked after an earlier refusal."""


class MultiAccessGating:
    def __init__(self, acceptance_predicate):
        self.acceptance_predicate = acceptance_predicate
        self.execution_locked = False

    def check_trajectory(self, step_metrics, step_index):
        if self.execution_locked:
            raise FirstDivergenceException(
                "System locked in FirstDivergence. REOPEN protocol required."
            )
        try:
            # Include conversion to bool: NumPy's ambiguous truth can itself
            # throw, and that must not leave the gate looking authorized.
            is_valid = bool(self.acceptance_predicate(step_metrics))
        except Exception as exc:
            self.execution_locked = True
            raise FirstDivergenceException(
                f"[FIRSTDIVERGENCE at k*={step_index}] "
                "Acceptance predicate could not be evaluated."
            ) from exc
        if not is_valid:
            self.execution_locked = True
            raise FirstDivergenceException(
                f"[FIRSTDIVERGENCE at k*={step_index}] "
                f"Constraints violated: {step_metrics}."
            )

    def trigger_reopen(self):
        self.execution_locked = False
        print("[REOPEN] State space reopened. Verification on a new independent interval required.")
