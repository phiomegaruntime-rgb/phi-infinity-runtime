"""
PHI-INFINITY (Phi-Infinity) - Multi-Access Gating
Author: Massimiliano Brighindi (2026)
"""
class FirstDivergenceException(Exception):
    pass

class MultiAccessGating:
    def __init__(self, acceptance_predicate):
        self.acceptance_predicate = acceptance_predicate
        self.execution_locked = False

    def check_trajectory(self, step_metrics, step_index):
        if self.execution_locked:
            raise FirstDivergenceException("System locked in FirstDivergence. REOPEN protocol required.")
        is_valid = self.acceptance_predicate(step_metrics)
        if not is_valid:
            self.execution_locked = True
            raise FirstDivergenceException(f"[FIRSTDIVERGENCE at k*={step_index}] Constraints violated: {step_metrics}.")

    def trigger_reopen(self):
        self.execution_locked = False
        print("[REOPEN] State space reopened. Verification on a new independent interval required.")
