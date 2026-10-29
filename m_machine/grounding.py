"""Non-generative trusted acquisition grounding under Amendment 07."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from .mechanical_propositions import (
    AMENDMENT_07_SOURCE,
    AMENDMENT_08_SOURCE,
    ConstructorPolicy,
    FrozenPropositionTypeRegistry,
    MechanicalProposition,
    PropositionOrigin,
    PropositionStatus,
    PropositionType,
    WitnessStatus,
    _TRUSTED_GROUNDING_CONSTRUCTOR_TOKEN,
    _construct_from_authorized_trusted_grounding,
    default_proposition_type_registry,
)
from .receipts import DerivationReceipt


DEFAULT_GROUNDING_CONTRACT_ID = "PHI_INFINITY_TRACE_GROUNDING_CONTRACT_V1"
DEFAULT_GROUNDING_CONTRACT_VERSION = "1"
GROUNDING_ASSERTION_KIND = "ACQUISITION_TRACE_INSTANTIATION"
PAIRWISE_GROUNDING_CONTRACT_ID = (
    "PHI_INFINITY_PAIRWISE_TRACE_NON_IDENTITY_CONTRACT_V1"
)
PAIRWISE_GROUNDING_CONTRACT_VERSION = "1"
PAIRWISE_GROUNDING_ASSERTION_KIND = (
    "PAIRWISE_PHYSICAL_TRACE_INSTANCE_NON_IDENTITY"
)
TRUST_ROOT_EXTERNAL_ORIGIN = "EXTERNALLY_ACCEPTED_NOT_DERIVED_BY_M"


def _tuple(values: Iterable[Any] | None) -> tuple[Any, ...]:
    if values is None:
        return ()
    return values if isinstance(values, tuple) else tuple(values)


def _hash_canonical(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


class ReplayState(str, Enum):
    FRESH = "FRESH"
    REPLAYED = "REPLAYED"


@dataclass(frozen=True, slots=True)
class GroundingApplicability:
    historically_valid: bool = True
    currently_applicable: bool = True
    replay_state: ReplayState = ReplayState.FRESH
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "replay_state", ReplayState(self.replay_state)
        )
        object.__setattr__(self, "reasons", _tuple(self.reasons))
        if self.replay_state == ReplayState.REPLAYED:
            object.__setattr__(self, "currently_applicable", False)

    def invalidate_current(self, reason: str) -> "GroundingApplicability":
        if not reason:
            raise ValueError("Applicability invalidation requires a reason.")
        return GroundingApplicability(
            historically_valid=self.historically_valid,
            currently_applicable=False,
            replay_state=self.replay_state,
            reasons=self.reasons + (reason,),
        )


@dataclass(frozen=True, slots=True)
class GroundingAncestry:
    trust_root_ids: tuple[str, ...] = ()
    contract_references: tuple[str, ...] = ()
    assertion_ids: tuple[str, ...] = ()
    acquisition_channel_ids: tuple[str, ...] = ()
    trace_ids: tuple[str, ...] = ()
    validation_ids: tuple[str, ...] = ()
    mechanical_scope: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "trust_root_ids",
            "contract_references",
            "assertion_ids",
            "acquisition_channel_ids",
            "trace_ids",
            "validation_ids",
        ):
            object.__setattr__(self, name, _unique(getattr(self, name)))
        object.__setattr__(
            self, "mechanical_scope", _tuple(self.mechanical_scope)
        )

    @classmethod
    def union(
        cls, *ancestries: "GroundingAncestry"
    ) -> "GroundingAncestry":
        if not ancestries:
            return cls()
        scopes = {
            ancestry.mechanical_scope
            for ancestry in ancestries
            if ancestry.mechanical_scope
        }
        if len(scopes) > 1:
            raise ValueError(
                "Grounding ancestry cannot flatten distinct exact scopes."
            )
        return cls(
            trust_root_ids=tuple(
                item
                for ancestry in ancestries
                for item in ancestry.trust_root_ids
            ),
            contract_references=tuple(
                item
                for ancestry in ancestries
                for item in ancestry.contract_references
            ),
            assertion_ids=tuple(
                item
                for ancestry in ancestries
                for item in ancestry.assertion_ids
            ),
            acquisition_channel_ids=tuple(
                item
                for ancestry in ancestries
                for item in ancestry.acquisition_channel_ids
            ),
            trace_ids=tuple(
                item
                for ancestry in ancestries
                for item in ancestry.trace_ids
            ),
            validation_ids=tuple(
                item
                for ancestry in ancestries
                for item in ancestry.validation_ids
            ),
            mechanical_scope=next(iter(scopes), ()),
        )


@dataclass(frozen=True, slots=True)
class GroundingContract:
    contract_id: str
    version: str
    semantic_specification: str
    semantic_hash: str
    permitted_assertion_kind: str
    permitted_proposition_type: PropositionType
    required_scope_keys: tuple[str, ...]
    permitted_channels: tuple[str, ...]
    source_semantics_excluded: bool
    allow_replay_as_current: bool
    constructor_policy: ConstructorPolicy
    authority_source: str
    authority_range: tuple[int, int]
    authority_range_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "permitted_proposition_type",
            PropositionType(self.permitted_proposition_type),
        )
        object.__setattr__(
            self,
            "constructor_policy",
            ConstructorPolicy(self.constructor_policy),
        )
        object.__setattr__(
            self, "required_scope_keys", _tuple(self.required_scope_keys)
        )
        object.__setattr__(
            self, "permitted_channels", _tuple(self.permitted_channels)
        )
        if not self.contract_id or not self.version:
            raise ValueError("Grounding contract identity is required.")
        if hashlib.sha256(
            self.semantic_specification.encode("utf-8")
        ).hexdigest() != self.semantic_hash:
            raise ValueError("Grounding contract semantic hash mismatch.")
        permitted_pairs = {
            (
                GROUNDING_ASSERTION_KIND,
                PropositionType.REAL_ACQUISITION_TRACE_EXISTS,
            ),
            (
                PAIRWISE_GROUNDING_ASSERTION_KIND,
                PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES,
            ),
        }
        if (
            (
                self.permitted_assertion_kind,
                self.permitted_proposition_type,
            )
            not in permitted_pairs
            or self.constructor_policy
            != ConstructorPolicy.TRUSTED_GROUNDING_ONLY
        ):
            raise ValueError(
                "Grounding contracts may authorize only frozen grounding types."
            )
        if not self.source_semantics_excluded:
            raise ValueError("Source-semantics exclusion is mandatory.")
        if len(self.authority_range_hash) != 64:
            raise ValueError("Contract authority hash must be SHA256.")

    @property
    def reference(self) -> str:
        return f"{self.contract_id}:{self.version}:{self.semantic_hash}"


@dataclass(frozen=True, slots=True)
class TrustRoot:
    trust_root_id: str
    contract_id: str
    contract_version: str
    contract_semantic_hash: str
    trusted_scope: tuple[tuple[str, str], ...]
    permitted_channels: tuple[str, ...]
    authority_identity: str
    origin: str = TRUST_ROOT_EXTERNAL_ORIGIN

    def __post_init__(self) -> None:
        object.__setattr__(self, "trusted_scope", _tuple(self.trusted_scope))
        object.__setattr__(
            self, "permitted_channels", _tuple(self.permitted_channels)
        )
        if not all(
            (
                self.trust_root_id,
                self.contract_id,
                self.contract_version,
                self.contract_semantic_hash,
                self.authority_identity,
            )
        ):
            raise ValueError("Trust-root identity and contract are required.")
        if self.origin != TRUST_ROOT_EXTERNAL_ORIGIN:
            raise ValueError("A trust root cannot be represented as DERIVED_M.")


@dataclass(frozen=True, slots=True)
class GroundingAssertion:
    assertion_id: str
    contract_id: str
    contract_version: str
    contract_semantic_hash: str
    claimed_trust_root_id: str
    acquisition_instance_id: str
    acquisition_channel_id: str
    trace_id: str
    mechanical_scope: tuple[tuple[str, str], ...]
    provenance: tuple[str, ...]
    replay_state: ReplayState
    historically_valid: bool
    currently_applicable: bool
    integrity_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "mechanical_scope", _tuple(self.mechanical_scope)
        )
        object.__setattr__(self, "provenance", _tuple(self.provenance))
        object.__setattr__(self, "replay_state", ReplayState(self.replay_state))
        if not all(
            (
                self.assertion_id,
                self.contract_id,
                self.contract_version,
                self.contract_semantic_hash,
                self.claimed_trust_root_id,
                self.acquisition_instance_id,
                self.acquisition_channel_id,
                self.trace_id,
            )
        ):
            raise ValueError("Grounding assertion identity is incomplete.")
        if self.integrity_hash != self.expected_integrity_hash:
            raise ValueError("Grounding assertion integrity mismatch.")

    @property
    def expected_integrity_hash(self) -> str:
        return _hash_canonical(
            {
                "assertion_id": self.assertion_id,
                "contract_id": self.contract_id,
                "contract_version": self.contract_version,
                "contract_semantic_hash": self.contract_semantic_hash,
                "claimed_trust_root_id": self.claimed_trust_root_id,
                "acquisition_instance_id": self.acquisition_instance_id,
                "acquisition_channel_id": self.acquisition_channel_id,
                "trace_id": self.trace_id,
                "mechanical_scope": self.mechanical_scope,
                "provenance": self.provenance,
                "replay_state": self.replay_state.value,
                "historically_valid": self.historically_valid,
                "currently_applicable": self.currently_applicable,
            }
        )

    @classmethod
    def create(
        cls,
        *,
        assertion_id: str,
        contract_id: str,
        contract_version: str,
        contract_semantic_hash: str,
        claimed_trust_root_id: str,
        acquisition_instance_id: str,
        acquisition_channel_id: str,
        trace_id: str,
        mechanical_scope: tuple[tuple[str, str], ...],
        provenance: tuple[str, ...],
        replay_state: ReplayState = ReplayState.FRESH,
        historically_valid: bool = True,
        currently_applicable: bool = True,
    ) -> "GroundingAssertion":
        fields = {
            "assertion_id": assertion_id,
            "contract_id": contract_id,
            "contract_version": contract_version,
            "contract_semantic_hash": contract_semantic_hash,
            "claimed_trust_root_id": claimed_trust_root_id,
            "acquisition_instance_id": acquisition_instance_id,
            "acquisition_channel_id": acquisition_channel_id,
            "trace_id": trace_id,
            "mechanical_scope": _tuple(mechanical_scope),
            "provenance": _tuple(provenance),
            "replay_state": ReplayState(replay_state),
            "historically_valid": historically_valid,
            "currently_applicable": currently_applicable,
        }
        integrity_hash = _hash_canonical(
            {
                **fields,
                "replay_state": fields["replay_state"].value,
            }
        )
        return cls(integrity_hash=integrity_hash, **fields)


@dataclass(frozen=True, slots=True)
class GroundingValidationResult:
    valid: bool
    reason: str
    validation_id: str
    assertion: GroundingAssertion
    proposition: MechanicalProposition | None = None
    receipt: DerivationReceipt | None = None
    ancestry: GroundingAncestry | None = None


@dataclass(frozen=True, slots=True)
class PairwiseGroundingAssertion:
    assertion_id: str
    contract_id: str
    contract_version: str
    contract_semantic_hash: str
    claimed_trust_root_id: str
    parent_proposition_ids: tuple[str, str]
    parent_trace_ids: tuple[str, str]
    mechanical_scope: tuple[tuple[str, str], ...]
    provenance: tuple[str, ...]
    historically_valid: bool
    currently_applicable: bool
    integrity_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "parent_proposition_ids", _tuple(self.parent_proposition_ids)
        )
        object.__setattr__(self, "parent_trace_ids", _tuple(self.parent_trace_ids))
        object.__setattr__(self, "mechanical_scope", _tuple(self.mechanical_scope))
        object.__setattr__(self, "provenance", _tuple(self.provenance))
        if len(self.parent_proposition_ids) != 2 or len(self.parent_trace_ids) != 2:
            raise ValueError("Pairwise assertions require exactly two subjects.")
        if not all(
            (
                self.assertion_id,
                self.contract_id,
                self.contract_version,
                self.contract_semantic_hash,
                self.claimed_trust_root_id,
                *self.parent_proposition_ids,
                *self.parent_trace_ids,
            )
        ):
            raise ValueError("Pairwise grounding assertion identity is incomplete.")
        if self.integrity_hash != self.expected_integrity_hash:
            raise ValueError("Pairwise grounding assertion integrity mismatch.")

    @property
    def expected_integrity_hash(self) -> str:
        return _hash_canonical(
            {
                "assertion_id": self.assertion_id,
                "contract_id": self.contract_id,
                "contract_version": self.contract_version,
                "contract_semantic_hash": self.contract_semantic_hash,
                "claimed_trust_root_id": self.claimed_trust_root_id,
                "parent_proposition_ids": self.parent_proposition_ids,
                "parent_trace_ids": self.parent_trace_ids,
                "mechanical_scope": self.mechanical_scope,
                "provenance": self.provenance,
                "historically_valid": self.historically_valid,
                "currently_applicable": self.currently_applicable,
            }
        )

    @classmethod
    def create(
        cls,
        *,
        assertion_id: str,
        contract_id: str,
        contract_version: str,
        contract_semantic_hash: str,
        claimed_trust_root_id: str,
        parent_proposition_ids: tuple[str, str],
        parent_trace_ids: tuple[str, str],
        mechanical_scope: tuple[tuple[str, str], ...],
        provenance: tuple[str, ...],
        historically_valid: bool = True,
        currently_applicable: bool = True,
    ) -> "PairwiseGroundingAssertion":
        values = {
            "assertion_id": assertion_id,
            "contract_id": contract_id,
            "contract_version": contract_version,
            "contract_semantic_hash": contract_semantic_hash,
            "claimed_trust_root_id": claimed_trust_root_id,
            "parent_proposition_ids": _tuple(parent_proposition_ids),
            "parent_trace_ids": _tuple(parent_trace_ids),
            "mechanical_scope": _tuple(mechanical_scope),
            "provenance": _tuple(provenance),
            "historically_valid": historically_valid,
            "currently_applicable": currently_applicable,
        }
        return cls(integrity_hash=_hash_canonical(values), **values)


@dataclass(frozen=True, slots=True)
class PairwiseGroundingValidationResult:
    valid: bool
    reason: str
    validation_id: str
    assertion: PairwiseGroundingAssertion
    proposition: MechanicalProposition | None = None
    receipt: DerivationReceipt | None = None
    ancestry: GroundingAncestry | None = None
    genealogy: "GroundedProofGenealogy | None" = None


@dataclass(frozen=True, slots=True)
class GroundedProofGenealogy:
    genealogy_id: str
    proposition_id: str
    ancestry: GroundingAncestry
    historically_valid: bool = True


@dataclass(frozen=True, slots=True)
class GroundingRegistry:
    contracts: tuple[GroundingContract, ...] = ()
    trust_roots: tuple[TrustRoot, ...] = ()
    assertions: tuple[GroundingAssertion, ...] = ()
    grounded_premises: tuple[MechanicalProposition, ...] = ()
    pairwise_assertions: tuple[PairwiseGroundingAssertion, ...] = ()
    pairwise_grounded_premises: tuple[MechanicalProposition, ...] = ()
    revoked_contract_references: tuple[str, ...] = ()
    revoked_trust_root_ids: tuple[str, ...] = ()
    revoked_assertion_ids: tuple[str, ...] = ()
    revoked_channel_ids: tuple[str, ...] = ()
    pairwise_grounded_genealogies: tuple[GroundedProofGenealogy, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "contracts",
            "trust_roots",
            "assertions",
            "grounded_premises",
            "pairwise_assertions",
            "pairwise_grounded_premises",
            "revoked_contract_references",
            "revoked_trust_root_ids",
            "revoked_assertion_ids",
            "revoked_channel_ids",
            "pairwise_grounded_genealogies",
        ):
            object.__setattr__(self, name, _tuple(getattr(self, name)))
        for values, label in (
            (tuple(item.reference for item in self.contracts), "contract"),
            (tuple(item.trust_root_id for item in self.trust_roots), "root"),
            (tuple(item.assertion_id for item in self.assertions), "assertion"),
            (
                tuple(item.assertion_id for item in self.pairwise_assertions),
                "pairwise assertion",
            ),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"Duplicate grounding {label} identity.")
        genealogy_ids = tuple(
            item.genealogy_id for item in self.pairwise_grounded_genealogies
        )
        if len(genealogy_ids) != len(set(genealogy_ids)):
            raise ValueError("Duplicate pairwise genealogy identity.")

    @property
    def grounding_contract_count(self) -> int:
        return len(self.contracts)

    @property
    def trusted_root_count(self) -> int:
        return len(self.trust_roots)

    @property
    def grounding_assertion_count(self) -> int:
        return len(self.assertions)

    @property
    def grounded_premise_count(self) -> int:
        return len(self.grounded_premises)

    @property
    def pairwise_assertion_count(self) -> int:
        return len(self.pairwise_assertions)

    @property
    def pairwise_grounded_premise_count(self) -> int:
        return len(self.pairwise_grounded_premises)

    @property
    def pairwise_grounded_genealogy_count(self) -> int:
        return len(self.pairwise_grounded_genealogies)

    def pairwise_genealogies_for(
        self, proposition_id: str
    ) -> tuple[GroundedProofGenealogy, ...]:
        """Return every preserved pairwise path for one proposition identity."""
        return tuple(
            genealogy
            for genealogy in self.pairwise_grounded_genealogies
            if genealogy.proposition_id == proposition_id
        )

    def register_contract(
        self, contract: GroundingContract
    ) -> "GroundingRegistry":
        return replace(self, contracts=self.contracts + (contract,))

    def register_trust_root(
        self, trust_root: TrustRoot, *, externally_authorized: bool = False
    ) -> "GroundingRegistry":
        if not externally_authorized:
            raise PermissionError(
                "Trust-root registration requires explicit external "
                "authorization."
            )
        contract = self._contract(
            trust_root.contract_id,
            trust_root.contract_version,
            trust_root.contract_semantic_hash,
        )
        if contract is None:
            raise ValueError("Trust root references an unknown contract.")
        if not set(trust_root.permitted_channels).issubset(
            contract.permitted_channels
        ):
            raise ValueError("Trust root exceeds contract channel scope.")
        return replace(self, trust_roots=self.trust_roots + (trust_root,))

    def record_assertion(
        self, assertion: GroundingAssertion
    ) -> "GroundingRegistry":
        return replace(self, assertions=self.assertions + (assertion,))

    def record_pairwise_assertion(
        self, assertion: PairwiseGroundingAssertion
    ) -> "GroundingRegistry":
        return replace(
            self, pairwise_assertions=self.pairwise_assertions + (assertion,)
        )

    def validate_pairwise_assertion(
        self,
        assertion: PairwiseGroundingAssertion,
        proposition_types: FrozenPropositionTypeRegistry,
    ) -> PairwiseGroundingValidationResult:
        validation_id = _hash_canonical(
            {
                "pairwise_assertion": assertion.assertion_id,
                "integrity": assertion.integrity_hash,
            }
        )
        fail = lambda reason: PairwiseGroundingValidationResult(
            False, reason, validation_id, assertion
        )
        if assertion not in self.pairwise_assertions:
            return fail("Pairwise assertion is not preserved in history.")
        contract = self._contract(
            assertion.contract_id,
            assertion.contract_version,
            assertion.contract_semantic_hash,
        )
        if (
            contract is None
            or contract.permitted_assertion_kind
            != PAIRWISE_GROUNDING_ASSERTION_KIND
            or contract.permitted_proposition_type
            != PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES
        ):
            return fail("No exact pairwise grounding contract matches.")
        if contract.reference in self.revoked_contract_references:
            return fail("Pairwise grounding contract is revoked.")
        root = self._root(assertion.claimed_trust_root_id)
        if root is None or root.trust_root_id in self.revoked_trust_root_ids:
            return fail("No currently applicable pairwise trust root matches.")
        if (
            root.contract_id,
            root.contract_version,
            root.contract_semantic_hash,
        ) != (
            assertion.contract_id,
            assertion.contract_version,
            assertion.contract_semantic_hash,
        ):
            return fail("Trust root does not authorize the pairwise contract.")
        if assertion.mechanical_scope != root.trusted_scope:
            return fail("Pair scope is outside the exact trust-root scope.")
        names = tuple(name for name, _ in assertion.mechanical_scope)
        if len(names) != len(set(names)) or set(names) != set(
            contract.required_scope_keys
        ):
            return fail("Pair assertion lacks the exact authorized pair scope.")
        if assertion.assertion_id in self.revoked_assertion_ids:
            return fail("Pairwise assertion is revoked.")
        if not assertion.historically_valid or not assertion.currently_applicable:
            return fail("Pairwise assertion is not currently applicable.")
        by_id = {
            item.proposition_id: item
            for item in self.grounded_premises
            if item.predicate_type == PropositionType.REAL_ACQUISITION_TRACE_EXISTS
        }
        if any(item not in by_id for item in assertion.parent_proposition_ids):
            return fail("Both exact grounded trace parents are required.")
        parents = tuple(by_id[item] for item in assertion.parent_proposition_ids)
        if parents[0] is parents[1] or parents[0].proposition_id == parents[1].proposition_id:
            return fail("A trace cannot be pairwise distinct from itself.")
        if any(
            parent.origin != PropositionOrigin.GROUNDED_EXTERNAL
            or not parent.historically_valid
            or not parent.currently_applicable
            or parent.grounding_ancestry is None
            for parent in parents
        ):
            return fail("Both grounded trace parents must be currently applicable.")
        if any(
            any(
                root_id in self.revoked_trust_root_ids
                for root_id in parent.grounding_ancestry.trust_root_ids
            )
            or any(
                reference in self.revoked_contract_references
                for reference in parent.grounding_ancestry.contract_references
            )
            or any(
                assertion_id in self.revoked_assertion_ids
                for assertion_id in parent.grounding_ancestry.assertion_ids
            )
            for parent in parents
        ):
            return fail("A required grounded trace ancestry is revoked.")
        actual_trace_ids = tuple(
            parent.grounding_ancestry.trace_ids[0]
            if len(parent.grounding_ancestry.trace_ids) == 1
            else ""
            for parent in parents
        )
        if (
            actual_trace_ids != assertion.parent_trace_ids
            or actual_trace_ids[0] == actual_trace_ids[1]
        ):
            return fail("Exact non-self physical trace referents do not match.")
        try:
            proposition_types.validate_scope(
                PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES,
                assertion.mechanical_scope,
            )
        except (KeyError, ValueError) as exc:
            return fail(f"Pair proposition scope is invalid: {exc}")
        parent_receipts = tuple(
            receipt_id
            for parent in parents
            for receipt_id in parent.subject_receipt_ids
        )
        canonical_subjects = tuple(sorted(parent_receipts))
        parent_ancestry = GroundingAncestry(
            trust_root_ids=tuple(
                root_id
                for parent in parents
                for root_id in parent.grounding_ancestry.trust_root_ids
            ),
            contract_references=tuple(
                reference
                for parent in parents
                for reference in parent.grounding_ancestry.contract_references
            ),
            assertion_ids=tuple(
                item
                for parent in parents
                for item in parent.grounding_ancestry.assertion_ids
            ),
            acquisition_channel_ids=tuple(
                item
                for parent in parents
                for item in parent.grounding_ancestry.acquisition_channel_ids
            ),
            trace_ids=actual_trace_ids,
            validation_ids=tuple(
                item
                for parent in parents
                for item in parent.grounding_ancestry.validation_ids
            ),
            mechanical_scope=assertion.mechanical_scope,
        )
        ancestry = GroundingAncestry.union(
            parent_ancestry,
            GroundingAncestry(
                trust_root_ids=(root.trust_root_id,),
                contract_references=(contract.reference,),
                assertion_ids=(assertion.assertion_id,),
                trace_ids=actual_trace_ids,
                validation_ids=(validation_id,),
                mechanical_scope=assertion.mechanical_scope,
            ),
        )
        receipt = DerivationReceipt.create(
            operation_name="grounding.validate_pairwise_assertion",
            authoritative_source_file=AMENDMENT_08_SOURCE,
            authoritative_clause=(
                "Amendment 08 lines 73-153; "
                f"source_sha256={contract.authority_range_hash}"
            ),
            input_receipt_ids=canonical_subjects,
            accessible_evidence=(
                "exact pairwise trust authorization present",
                "two exact currently applicable grounded trace parents present",
                "physical-instance non-identity externally accepted",
                "no difference or source semantics inferred",
            ),
            operation_performed=(
                "Validated exact pairwise grounding contract conformance."
            ),
            resulting_difference_or_consequence=(
                "One grounded pairwise physical-instance non-identity premise."
            ),
            status="GROUNDED_EXTERNAL",
            implementation_source="m_machine/grounding.py",
            clause_id="pairwise_grounding.contract",
        )
        proposition = _construct_from_authorized_trusted_grounding(
            registry=proposition_types,
            predicate_type=(
                PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES
            ),
            mechanical_scope=assertion.mechanical_scope,
            subject_receipt_ids=canonical_subjects,
            proposition_status=PropositionStatus.ASSERTED,
            witness_status=WitnessStatus.WITNESS_FREE,
            grounding_ancestry=ancestry,
            historically_valid=True,
            currently_applicable=True,
            authorization_token=_TRUSTED_GROUNDING_CONSTRUCTOR_TOKEN,
        )
        genealogy = GroundedProofGenealogy(
            genealogy_id=validation_id,
            proposition_id=proposition.proposition_id,
            ancestry=ancestry,
            historically_valid=proposition.historically_valid,
        )
        return PairwiseGroundingValidationResult(
            True,
            "Exact pairwise grounding contract conformance validated.",
            validation_id,
            assertion,
            proposition,
            receipt,
            ancestry,
            genealogy,
        )

    def accept_pairwise_validation(
        self, validation: PairwiseGroundingValidationResult
    ) -> "GroundingRegistry":
        if (
            not validation.valid
            or validation.proposition is None
            or validation.receipt is None
        ):
            return self
        if validation.assertion not in self.pairwise_assertions:
            raise ValueError("Pairwise assertion must remain in history.")
        genealogy = validation.genealogy or GroundedProofGenealogy(
            genealogy_id=validation.validation_id,
            proposition_id=validation.proposition.proposition_id,
            ancestry=validation.ancestry
            or GroundingAncestry(
                mechanical_scope=validation.proposition.mechanical_scope
            ),
            historically_valid=validation.proposition.historically_valid,
        )
        existing_proposition = next(
            (
                item
                for item in self.pairwise_grounded_premises
                if item.proposition_id == validation.proposition.proposition_id
            ),
            None,
        )
        if genealogy.proposition_id != validation.proposition.proposition_id:
            raise ValueError(
                "Pairwise genealogy does not identify its grounded proposition."
            )
        genealogies = self.pairwise_grounded_genealogies
        existing_genealogy = next(
            (
                item
                for item in genealogies
                if item.genealogy_id == genealogy.genealogy_id
            ),
            None,
        )
        if existing_genealogy is not None and existing_genealogy != genealogy:
            raise ValueError(
                "Pairwise genealogy identity is already bound to another path."
            )
        if existing_genealogy is None:
            genealogies += (genealogy,)
        propositions = self.pairwise_grounded_premises
        if existing_proposition is None:
            propositions += (validation.proposition,)
        return replace(
            self,
            pairwise_grounded_premises=propositions,
            pairwise_grounded_genealogies=genealogies,
        )

    def validate_assertion(
        self,
        assertion: GroundingAssertion,
        proposition_types: FrozenPropositionTypeRegistry,
    ) -> GroundingValidationResult:
        reason = self._validation_failure(assertion, proposition_types)
        validation_id = _hash_canonical(
            {
                "assertion": assertion.assertion_id,
                "integrity": assertion.integrity_hash,
                "result": reason or "VALID",
            }
        )
        if reason:
            return GroundingValidationResult(
                False, reason, validation_id, assertion
            )
        contract = self._contract(
            assertion.contract_id,
            assertion.contract_version,
            assertion.contract_semantic_hash,
        )
        root = self._root(assertion.claimed_trust_root_id)
        ancestry = GroundingAncestry(
            trust_root_ids=(root.trust_root_id,),
            contract_references=(contract.reference,),
            assertion_ids=(assertion.assertion_id,),
            acquisition_channel_ids=(assertion.acquisition_channel_id,),
            trace_ids=(assertion.trace_id,),
            validation_ids=(validation_id,),
            mechanical_scope=assertion.mechanical_scope,
        )
        receipt = DerivationReceipt.create(
            operation_name="grounding.validate_assertion",
            authoritative_source_file=AMENDMENT_07_SOURCE,
            authoritative_clause=(
                "Amendment 07 lines 127-165; "
                f"contract_sha256={contract.semantic_hash}"
            ),
            input_receipt_ids=(
                root.trust_root_id,
                assertion.assertion_id,
            ),
            accessible_evidence=(
                "exact contract identity and version",
                "explicitly registered external trust root",
                "exact acquisition channel and scope",
                "assertion integrity and current applicability",
                "source semantics excluded",
            ),
            operation_performed=(
                "Validated exact conformance to the externally accepted "
                "grounding contract without source interpretation."
            ),
            resulting_difference_or_consequence=assertion.trace_id,
            status="GROUNDED_EXTERNAL",
            implementation_source="m_machine/grounding.py",
            clause_id="grounding.assertion_validation",
        )
        proposition = _construct_from_authorized_trusted_grounding(
            registry=proposition_types,
            predicate_type=PropositionType.REAL_ACQUISITION_TRACE_EXISTS,
            mechanical_scope=assertion.mechanical_scope,
            subject_receipt_ids=(receipt.receipt_id,),
            proposition_status=PropositionStatus.ASSERTED,
            witness_status=WitnessStatus.WITNESS_FREE,
            grounding_ancestry=ancestry,
            historically_valid=assertion.historically_valid,
            currently_applicable=assertion.currently_applicable,
            authorization_token=_TRUSTED_GROUNDING_CONSTRUCTOR_TOKEN,
        )
        return GroundingValidationResult(
            True,
            "Exact grounding contract conformance validated.",
            validation_id,
            assertion,
            proposition,
            receipt,
            ancestry,
        )

    def accept_validation(
        self, validation: GroundingValidationResult
    ) -> "GroundingRegistry":
        if (
            not validation.valid
            or validation.proposition is None
            or validation.receipt is None
        ):
            return self
        if validation.assertion not in self.assertions:
            raise ValueError("Grounding assertion must remain in history.")
        if validation.proposition in self.grounded_premises:
            return self
        return replace(
            self,
            grounded_premises=self.grounded_premises
            + (validation.proposition,),
        )

    def revoke_trust_root(self, root_id: str) -> "GroundingRegistry":
        if self._root(root_id) is None:
            raise KeyError(root_id)
        return replace(
            self,
            revoked_trust_root_ids=_unique(
                self.revoked_trust_root_ids + (root_id,)
            ),
        )

    def revoke_contract(self, reference: str) -> "GroundingRegistry":
        if not any(item.reference == reference for item in self.contracts):
            raise KeyError(reference)
        return replace(
            self,
            revoked_contract_references=_unique(
                self.revoked_contract_references + (reference,)
            ),
        )

    def revoke_assertion(self, assertion_id: str) -> "GroundingRegistry":
        if not any(
            item.assertion_id == assertion_id for item in self.assertions
        ) and not any(
            item.assertion_id == assertion_id
            for item in self.pairwise_assertions
        ):
            raise KeyError(assertion_id)
        return replace(
            self,
            revoked_assertion_ids=_unique(
                self.revoked_assertion_ids + (assertion_id,)
            ),
        )

    def revoke_channel(self, channel_id: str) -> "GroundingRegistry":
        if not channel_id:
            raise ValueError("Channel revocation requires an identity.")
        return replace(
            self,
            revoked_channel_ids=_unique(
                self.revoked_channel_ids + (channel_id,)
            ),
        )

    def genealogy_applicability(
        self, genealogy: GroundedProofGenealogy
    ) -> GroundingApplicability:
        reasons = []
        ancestry = genealogy.ancestry
        reasons.extend(
            f"revoked trust root: {item}"
            for item in ancestry.trust_root_ids
            if item in self.revoked_trust_root_ids
        )
        reasons.extend(
            f"revoked contract: {item}"
            for item in ancestry.contract_references
            if item in self.revoked_contract_references
        )
        reasons.extend(
            f"revoked assertion: {item}"
            for item in ancestry.assertion_ids
            if item in self.revoked_assertion_ids
        )
        reasons.extend(
            f"revoked channel: {item}"
            for item in ancestry.acquisition_channel_ids
            if item in self.revoked_channel_ids
        )
        return GroundingApplicability(
            historically_valid=genealogy.historically_valid,
            currently_applicable=not reasons,
            reasons=tuple(reasons),
        )

    def _validation_failure(
        self,
        assertion: GroundingAssertion,
        proposition_types: FrozenPropositionTypeRegistry,
    ) -> str:
        if assertion not in self.assertions:
            return "Assertion is not preserved in the grounding registry."
        contract = self._contract(
            assertion.contract_id,
            assertion.contract_version,
            assertion.contract_semantic_hash,
        )
        if contract is None:
            return "No exact grounding contract matches the assertion."
        if contract.reference in self.revoked_contract_references:
            return "Grounding contract is not currently applicable."
        root = self._root(assertion.claimed_trust_root_id)
        if root is None:
            return "No explicitly accepted trust root matches the assertion."
        if root.trust_root_id in self.revoked_trust_root_ids:
            return "Trust root is not currently applicable."
        if (
            root.contract_id != assertion.contract_id
            or root.contract_version != assertion.contract_version
            or root.contract_semantic_hash
            != assertion.contract_semantic_hash
        ):
            return "Trust root does not accept the assertion contract."
        if assertion.acquisition_channel_id not in contract.permitted_channels:
            return "Assertion channel is outside the contract."
        if assertion.acquisition_channel_id not in root.permitted_channels:
            return "Assertion channel is outside the trust-root scope."
        if assertion.acquisition_channel_id in self.revoked_channel_ids:
            return "Assertion channel is not currently applicable."
        if assertion.mechanical_scope != root.trusted_scope:
            return "Assertion scope is outside the exact trust-root scope."
        names = tuple(name for name, _ in assertion.mechanical_scope)
        if (
            len(names) != len(set(names))
            or set(names) != set(contract.required_scope_keys)
        ):
            return "Assertion does not satisfy exact contract scope semantics."
        try:
            proposition_types.validate_scope(
                PropositionType.REAL_ACQUISITION_TRACE_EXISTS,
                assertion.mechanical_scope,
            )
        except (KeyError, ValueError) as exc:
            return f"Trace proposition scope is invalid: {exc}"
        if assertion.assertion_id in self.revoked_assertion_ids:
            return "Grounding assertion is not currently applicable."
        if not assertion.historically_valid:
            return "Grounding assertion is not historically valid."
        if not assertion.currently_applicable:
            return "Grounding assertion is not currently applicable."
        if (
            assertion.replay_state == ReplayState.REPLAYED
            and not contract.allow_replay_as_current
        ):
            return "Replayed assertion cannot masquerade as current."
        return ""

    def _contract(
        self, contract_id: str, version: str, semantic_hash: str
    ) -> GroundingContract | None:
        matches = tuple(
            item
            for item in self.contracts
            if item.contract_id == contract_id
            and item.version == version
            and item.semantic_hash == semantic_hash
        )
        return matches[0] if len(matches) == 1 else None

    def _root(self, root_id: str) -> TrustRoot | None:
        matches = tuple(
            item for item in self.trust_roots if item.trust_root_id == root_id
        )
        return matches[0] if len(matches) == 1 else None


TrustedGroundingBase = GroundingRegistry


@dataclass(frozen=True, slots=True)
class GroundedExecutionState:
    access_value: Any
    grounding_base: GroundingRegistry
    validation: Any
    proof_result: Any


def default_grounding_contract(
    repository_root: Path | str = Path("."),
) -> GroundingContract:
    statement = (
        "Accept exactly one trace-scope REAL_ACQUISITION_TRACE_EXISTS "
        "proposition only from an immutable assertion under an explicitly "
        "registered matching trust root, exact contract version, permitted "
        "channel, exact scope, valid integrity, fresh current applicability, "
        "and complete provenance. Infer no source semantics, source witness, "
        "REAL_DIFFERENCE_EXISTS, or DERIVED_M."
    )
    root = Path(repository_root).resolve()
    lines = (root / AMENDMENT_07_SOURCE).read_bytes().splitlines(
        keepends=True
    )
    start, end = (127, 165)
    authority_hash = hashlib.sha256(
        b"".join(lines[start - 1 : end])
    ).hexdigest()
    return GroundingContract(
        contract_id=DEFAULT_GROUNDING_CONTRACT_ID,
        version=DEFAULT_GROUNDING_CONTRACT_VERSION,
        semantic_specification=statement,
        semantic_hash=hashlib.sha256(statement.encode("utf-8")).hexdigest(),
        permitted_assertion_kind=GROUNDING_ASSERTION_KIND,
        permitted_proposition_type=(
            PropositionType.REAL_ACQUISITION_TRACE_EXISTS
        ),
        required_scope_keys=(
            "access_snapshot",
            "acquisition_instance",
            "acquisition_channel",
            "acquisition_trace",
        ),
        permitted_channels=("EXPLICIT_ACQUISITION_CHANNEL",),
        source_semantics_excluded=True,
        allow_replay_as_current=False,
        constructor_policy=ConstructorPolicy.TRUSTED_GROUNDING_ONLY,
        authority_source=AMENDMENT_07_SOURCE,
        authority_range=(start, end),
        authority_range_hash=authority_hash,
    )


def default_pairwise_grounding_contract(
    repository_root: Path | str = Path("."),
) -> GroundingContract:
    statement = (
        "Accept exactly one symmetric DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES "
        "proposition from an immutable explicit pairwise assertion under an "
        "exact pairwise trust root, two exact currently applicable grounded "
        "trace parents, and one exact pair scope. Infer no source semantics, "
        "REAL_DIFFERENCE_EXISTS, REAL_CONSEQUENCE_EXISTS, or DERIVED_M."
    )
    root = Path(repository_root).resolve()
    lines = (root / AMENDMENT_08_SOURCE).read_bytes().splitlines(keepends=True)
    start, end = (73, 153)
    return GroundingContract(
        contract_id=PAIRWISE_GROUNDING_CONTRACT_ID,
        version=PAIRWISE_GROUNDING_CONTRACT_VERSION,
        semantic_specification=statement,
        semantic_hash=hashlib.sha256(statement.encode("utf-8")).hexdigest(),
        permitted_assertion_kind=PAIRWISE_GROUNDING_ASSERTION_KIND,
        permitted_proposition_type=(
            PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES
        ),
        required_scope_keys=(
            "access_snapshot",
            "mechanical_configuration",
            "field_context",
            "scale",
            "genealogy",
            "execution_lineage",
            "pair_scope",
        ),
        permitted_channels=(),
        source_semantics_excluded=True,
        allow_replay_as_current=False,
        constructor_policy=ConstructorPolicy.TRUSTED_GROUNDING_ONLY,
        authority_source=AMENDMENT_08_SOURCE,
        authority_range=(start, end),
        authority_range_hash=hashlib.sha256(
            b"".join(lines[start - 1 : end])
        ).hexdigest(),
    )
def default_grounding_registry(
    repository_root: Path | str = Path("."),
) -> GroundingRegistry:
    proposition_types = default_proposition_type_registry(repository_root)
    if (
        proposition_types.get(
            PropositionType.REAL_ACQUISITION_TRACE_EXISTS
        ).constructor_policy
        != ConstructorPolicy.TRUSTED_GROUNDING_ONLY
    ):
        raise ValueError("Weak trace constructor policy is not frozen.")
    return GroundingRegistry(
        contracts=(
            default_grounding_contract(repository_root),
            default_pairwise_grounding_contract(repository_root),
        )
    )