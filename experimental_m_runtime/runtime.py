"""Public entry point for the isolated experimental fragment runtime."""

from __future__ import annotations

from .authority import (
    EXPERIMENTAL_RUNTIME_ID,
    EXPERIMENTAL_RUNTIME_VERSION,
    verify_experimental_authority,
)
from .gate import AntiDriftGate
from .model import (
    Decision,
    ExperimentalProposal,
    ExperimentalResult,
    Stage,
)


class ExperimentalFragmentRuntime:
    """A non-auto-integrated, fail-closed experimental execution boundary."""

    def __init__(self, repository_root: str | None = None) -> None:
        self.authority = verify_experimental_authority(repository_root)
        self.anti_drift = AntiDriftGate()

    def execute(self, proposal: ExperimentalProposal) -> ExperimentalResult:
        gate = self.anti_drift.evaluate(proposal)
        receipts = tuple(proposal.receipts) + tuple(gate.receipts)
        if gate.decision != Decision.ALLOW:
            return ExperimentalResult(
                decision=gate.decision,
                stage=gate.stage,
                classification=gate.classification,
                output=None,
                reason=gate.reason,
                receipts=receipts,
                runtime_id=self.authority.runtime_id,
                runtime_version=self.authority.version,
                authority_hash=self.authority.authority_sha256,
            )
        return ExperimentalResult(
            decision=Decision.ALLOW,
            stage=Stage.OUTPUT,
            classification=gate.classification,
            output={
                "classification": gate.classification.value,
                "fragment_ids": tuple(
                    fragment.fragment_id for fragment in proposal.fragments
                ),
                "path_fragment_ids": tuple(proposal.exact_path),
            },
            reason=gate.reason,
            receipts=receipts,
            runtime_id=self.authority.runtime_id,
            runtime_version=self.authority.version,
            authority_hash=self.authority.authority_sha256,
        )