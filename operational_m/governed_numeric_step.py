"""Opt-in caller-support gate for the real in-memory PHI numerical engine.

This is an operational control, not a native M derivation or authentication
mechanism.  It gates calls to ``PhiSubstrateEngine.step`` without changing the
engine's equations or its historical, ungoverned entry point.
"""

from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from hashlib import sha256
from threading import RLock
from typing import Any

import numpy as np

from src.core import PhiSubstrateEngine


class GovernedStepError(RuntimeError):
    """Base error for the opt-in numerical state gate."""


class OptInRequired(GovernedStepError):
    """Raised unless callers explicitly enable the operational gate."""


class SupportUnavailable(GovernedStepError):
    """Raised when the configured caller support is absent or stale."""


class ReopenRequired(GovernedStepError):
    """Raised when a withdrawn support has not been explicitly reopened."""


class FreshVerificationRequired(GovernedStepError):
    """Raised when support changed after its last verification."""


@dataclass(frozen=True, slots=True)
class CallerSupport:
    """A caller assertion recorded by the process-local support authority."""

    support_id: str
    statement: str


@dataclass(frozen=True, slots=True)
class SupportSnapshot:
    """Read-only view of the current caller-supplied support state."""

    revision: int
    support: CallerSupport | None
    reopen_required: bool
    verified_revision: int | None


@dataclass(frozen=True, slots=True)
class GovernedStepReport:
    """Measurements from one successful call on the existing PHI engine."""

    step_number: int
    support_id: str
    support_revision: int
    state_before_sha256: str
    state_after_sha256: str
    metrics: dict[str, Any]


class CallerSupportAuthority:
    """Process-local owner of caller assertions and their lifecycle.

    Possession of this Python object is the only update boundary.  It provides
    no user authentication, cryptographic identity, or native M derivation.
    """

    def __init__(self, required_support_id: str) -> None:
        if type(required_support_id) is not str or not required_support_id.strip():
            raise ValueError("required_support_id must be a non-empty string.")
        self._required_support_id = required_support_id
        self._lock = RLock()
        self._revision = 0
        self._support: CallerSupport | None = None
        self._reopen_required = False
        self._verified_revision: int | None = None

    @property
    def required_support_id(self) -> str:
        return self._required_support_id

    def publish_support(self, *, support_id: str, statement: str) -> None:
        """Record a caller assertion; this does not independently prove it."""
        if support_id != self.required_support_id:
            raise ValueError("Support id does not match the configured requirement.")
        if type(statement) is not str or not statement.strip():
            raise ValueError("A non-empty caller statement is required.")
        with self._lock:
            self._revision += 1
            self._support = CallerSupport(support_id, statement)
            self._verified_revision = None

    def withdraw_support(self) -> None:
        """Withdraw the current support and require an explicit reopen."""
        with self._lock:
            self._revision += 1
            self._support = None
            self._reopen_required = True
            self._verified_revision = None

    def reopen(self) -> None:
        """Reopen only when support is present; a fresh verify still follows."""
        with self._lock:
            if self._support is None:
                raise SupportUnavailable(
                    "Cannot reopen while the required support is absent."
                )
            self._revision += 1
            self._reopen_required = False
            self._verified_revision = None

    def verify(self) -> SupportSnapshot:
        """Verify presence against this operational ledger, not against M."""
        with self._lock:
            if self._support is None:
                raise SupportUnavailable("The required caller support is absent.")
            if self._reopen_required:
                raise ReopenRequired(
                    "Support was restored but the authority has not reopened it."
                )
            self._verified_revision = self._revision
            return self._snapshot_unlocked()

    def snapshot(self) -> SupportSnapshot:
        with self._lock:
            return self._snapshot_unlocked()

    def _snapshot_unlocked(self) -> SupportSnapshot:
        return SupportSnapshot(
            revision=self._revision,
            support=self._support,
            reopen_required=self._reopen_required,
            verified_revision=self._verified_revision,
        )


class GovernedPhiStepper:
    """Gate real numerical state advancement behind current support.

    The authority lock serializes support updates with governed steps. The
    existing engine implementation runs on a private candidate. Its arrays
    are published only if the verified support revision still holds.
    """

    def __init__(
        self,
        engine: PhiSubstrateEngine,
        authority: CallerSupportAuthority,
        *,
        opt_in: bool = False,
    ) -> None:
        if not opt_in:
            raise OptInRequired(
                "Governed numerical stepping requires explicit opt_in=True."
            )
        if type(engine) is not PhiSubstrateEngine:
            raise TypeError("Governed stepping requires the existing PHI engine.")
        if type(authority) is not CallerSupportAuthority:
            raise TypeError("A CallerSupportAuthority instance is required.")
        self.engine = engine
        self.authority = authority
        self._step_number = 0

    def step(self, mechanical_progress: float = 1.0) -> GovernedStepReport:
        authority = self.authority
        with authority._lock:
            support = authority._support
            if support is None:
                raise SupportUnavailable("The required caller support is absent.")
            if authority._reopen_required:
                raise ReopenRequired(
                    "Restored support remains blocked until explicit reopen."
                )
            if authority._verified_revision != authority._revision:
                raise FreshVerificationRequired(
                    "Verify the current support revision before stepping."
                )
            if support.support_id != authority.required_support_id:
                raise SupportUnavailable(
                    "The current support no longer matches the configured requirement."
                )

            before_arrays = {
                name: getattr(self.engine, name).copy()
                for name in ("pos", "S", "R")
            }
            before = _state_digest(self.engine)
            verified_revision = authority._revision
            candidate = deepcopy(self.engine)
            metrics = candidate.step(mechanical_progress=mechanical_progress)
            _validate_state(candidate, before_arrays)
            after = _state_digest(candidate)
            # RLock permits same-thread callbacks to update the authority.
            # Even revoke/restore/verify cannot reuse this attempted step.
            if (authority._revision != verified_revision
                or authority._verified_revision != verified_revision
                or authority._support != support
                or authority._reopen_required):
                raise FreshVerificationRequired(
                    "Support changed during calculation; candidate discarded."
                )
            self.engine.pos, self.engine.S, self.engine.R = (
                candidate.pos, candidate.S, candidate.R
            )

            self._step_number += 1
            return GovernedStepReport(
                step_number=self._step_number,
                support_id=support.support_id,
                support_revision=verified_revision,
                state_before_sha256=before,
                state_after_sha256=after,
                metrics=dict(metrics),
            )


def _state_digest(engine: PhiSubstrateEngine) -> str:
    digest = sha256()
    for name in ("pos", "S", "R"):
        value = np.ascontiguousarray(getattr(engine, name))
        digest.update(name.encode("ascii"))
        digest.update(value.dtype.str.encode("ascii"))
        digest.update(repr(value.shape).encode("ascii"))
        digest.update(value.tobytes())
    return digest.hexdigest()


def _validate_state(
    engine: PhiSubstrateEngine,
    before_arrays: dict[str, np.ndarray],
) -> None:
    for name in ("pos", "S", "R"):
        before = before_arrays[name]
        after = getattr(engine, name)
        if not isinstance(after, np.ndarray):
            raise TypeError(f"Engine state {name} must remain a NumPy array.")
        if before.shape != after.shape or before.dtype != after.dtype:
            raise ValueError(f"Engine state {name} changed shape or dtype.")
        if not np.isfinite(after).all():
            raise ValueError(f"Engine state {name} became non-finite.")
