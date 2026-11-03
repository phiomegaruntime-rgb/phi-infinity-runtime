"""Opt-in declarative, versioned multi-channel access protocol for PHI.

Unlike caller-provided Python predicates, the quorum decision is a fixed,
side-effect-free rule over exact built-in booleans. Recovery requires a new
positive publication AFTER the rejected revision. This is a reproducible
software freshness rule, not authentication of a physical independent interval.

Original MultiAccessGating and original mechanics remain available unchanged.
"""

import copy

from src.effect_authorization import SynchronizedSupport
from src.gating import FirstDivergenceException, MultiAccessGating


class VersionedSupport(SynchronizedSupport):
    """Cooperative monotonic revision ledger for plain boolean support flags."""

    @staticmethod
    def _validate(evidence):
        if type(evidence) is not dict or not evidence:
            raise TypeError('Support evidence must be a nonempty plain dict')
        for key, value in evidence.items():
            if type(key) is not str or not key:
                raise TypeError('Support channel names must be nonempty strings')
            if type(value) is not bool:
                raise TypeError('Support channel values must be exact booleans')

    def __init__(self, initial_evidence):
        self._validate(initial_evidence)
        super().__init__(initial_evidence)
        self._revision = 0

    def publish(self, evidence):
        self._validate(evidence)
        if getattr(self._local, 'inside_effect', False):
            raise RuntimeError('Cannot publish from inside an authorized effect')
        prepared = copy.deepcopy(evidence)
        with self._lock:
            self._evidence = prepared
            self._revision += 1
            return self._revision

    def read_revision(self):
        """Return coherent (revision, copied flags), never an auth token."""
        with self._lock:
            return self._revision, copy.deepcopy(self._evidence)


class VersionedQuorumGate(MultiAccessGating):
    """Gate requiring *all* named channels and new publication to REOPEN.

    No user-provided callback is executed for the acceptance decision.
    Direct check_trajectory(step_metrics, ...) cannot forge support because the
    gate always reads its bound VersionedSupport under the same source lock.
    """

    def __init__(self, source, required_channels):
        if type(source) is not VersionedSupport:
            raise TypeError('source must be a VersionedSupport')
        channels = tuple(required_channels)
        if (not channels or len(set(channels)) != len(channels)
                or any(type(s) is not str or not s for s in channels)):
            raise ValueError('required_channels must be unique nonempty strings')
        self._phi_required_source = source
        self.required_channels = channels
        self.rejected_revision = None
        self.accepted_revision = None
        super().__init__(self._all_required_present)

    def _all_required_present(self, flags):
        return all(flags.get(channel) is True for channel in self.required_channels)

    def check_trajectory(self, step_metrics, step_index):
        # Ignore caller-supplied step_metrics; the bound source is the authority
        # for the (cooperative) decision. This closes the arbitrary-metrics path.
        with self._phi_required_source._lock:
            if self.execution_locked:
                raise FirstDivergenceException(
                    'System locked in FirstDivergence. REOPEN protocol required.'
                )
            revision, flags = self._phi_required_source.read_revision()
            try:
                super().check_trajectory(flags, step_index)
            except FirstDivergenceException:
                self.rejected_revision = revision
                raise
            self.accepted_revision = revision

    def _record_execution_refusal(self):
        """Record a rejected source revision while the effect window is held.

        Also covers argument, snapshot, transaction and numeric failures that
        occur *after* quorum validation, not just support withdrawal.
        Callers must hold the same source lock as the effect publication.
        This is cooperative software freshness, not external authentication.
        """
        source = self._phi_required_source
        with source._lock:
            self.execution_locked = True
            self.rejected_revision = source._revision

    def trigger_reopen(self):
        """Allow recovery only after a newer all-positive published observation."""
        source = self._phi_required_source
        with source._lock:
            if getattr(source._local, 'inside_effect', False):
                raise RuntimeError('Cannot REOPEN inside a protected effect')
            if self.execution_locked is False:
                raise FirstDivergenceException('REOPEN requires a prior refusal')
            revision, flags = source.read_revision()
            if (self.rejected_revision is None
                    or revision <= self.rejected_revision
                    or not self._all_required_present(flags)):
                raise FirstDivergenceException(
                    'REOPEN refused: no newer positive support publication.'
                )
            self.execution_locked = False
            return revision
