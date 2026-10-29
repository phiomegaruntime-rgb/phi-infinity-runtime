"""Non-generative operational proof semantics for frozen M rules."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import inspect
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .receipts import DerivationReceipt
from .mechanical_propositions import (
    ConstructorPolicy,
    FrozenPropositionTypeRegistry,
    MechanicalProposition,
    PropositionOrigin,
    PropositionType,
    default_proposition_type_registry,
)


AMENDMENT_05_SOURCE = (
    "docs/"
    "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_05_OPERATIONAL_DERIVATION_"
    "SEMANTICS_PROOF_KERNEL.md"
)
FIRST_MECHANICAL_INFERENCE_RULE_FRONTIER = (
    "FIRST_MECHANICAL_INFERENCE_RULE_FRONTIER"
)
RAW_MECHANICAL_BOOTSTRAP_FRONTIER = "RAW_MECHANICAL_BOOTSTRAP_FRONTIER"
POST_GROUNDING_MECHANICAL_RECONSTRUCTION_FRONTIER = (
    "POST_GROUNDING_MECHANICAL_RECONSTRUCTION_FRONTIER"
)
NON_IDENTITY_RULE_REGISTRATION_FRONTIER = (
    "NON_IDENTITY_RULE_REGISTRATION_FRONTIER"
)

ProofScope = tuple[tuple[str, str], ...]


class RuleClass(str, Enum):
    ACCESS_REPRESENTATION_RULE = "ACCESS_REPRESENTATION_RULE"
    EXECUTION_CONTROL_RULE = "EXECUTION_CONTROL_RULE"
    MECHANICAL_INFERENCE_RULE = "MECHANICAL_INFERENCE_RULE"
    FALSIFICATION_RULE = "FALSIFICATION_RULE"


def _as_tuple(values: Iterable[Any] | None) -> tuple[Any, ...]:
    if values is None:
        return ()
    if isinstance(values, tuple):
        return values
    return tuple(values)


def _is_sha256(value: str) -> bool:
    if len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def semantic_hash(specification: str) -> str:
    return hashlib.sha256(specification.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class InferenceRule:
    rule_id: str
    rule_class: RuleClass
    authority_source: str
    authority_range: tuple[int, int]
    authority_range_hash: str
    semantic_specification: str
    semantic_specification_hash: str
    premise_schema: tuple[str, ...]
    scope_constraints: tuple[str, ...]
    conclusion_schema: str
    unresolved_behavior: str
    implementation_id: str = ""
    implementation_hash: str = ""
    version: str = "1"
    separately_audited_authorization: bool = False
    authorization_audit_id: str = ""
    raw_bootstrap: str = "NO"
    falsification_boundary: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_class", RuleClass(self.rule_class))
        object.__setattr__(
            self, "premise_schema", _as_tuple(self.premise_schema)
        )
        object.__setattr__(
            self, "scope_constraints", _as_tuple(self.scope_constraints)
        )
        required = {
            "rule_id": self.rule_id,
            "authority_source": self.authority_source,
            "semantic_specification": self.semantic_specification,
            "conclusion_schema": self.conclusion_schema,
            "unresolved_behavior": self.unresolved_behavior,
            "version": self.version,
        }
        missing = tuple(name for name, value in required.items() if not value)
        if missing:
            raise ValueError(
                "Inference rule metadata is incomplete: " + ", ".join(missing)
            )
        start, end = self.authority_range
        if start < 1 or end < start:
            raise ValueError("Authority range must be a valid inclusive range.")
        if not _is_sha256(self.authority_range_hash):
            raise ValueError("Authority range hash must be a SHA256 digest.")
        if self.semantic_specification_hash != semantic_hash(
            self.semantic_specification
        ):
            raise ValueError("Semantic specification hash mismatch.")
        if bool(self.implementation_id) != bool(self.implementation_hash):
            raise ValueError(
                "Implementation identity and hash must be supplied together."
            )
        if self.implementation_hash and not _is_sha256(
            self.implementation_hash
        ):
            raise ValueError("Implementation hash must be a SHA256 digest.")
        if self.raw_bootstrap != "NO":
            raise ValueError("Registered rules cannot declare raw bootstrap.")

    @property
    def identity(self) -> tuple[str, str, str]:
        return (self.rule_id, self.version, self.semantic_specification_hash)


@dataclass(frozen=True, slots=True)
class ProofGenealogy:
    conclusion_identity: str
    parent_receipt_ids: tuple[str, ...]
    rule_id: str
    rule_hash: str


@dataclass(frozen=True, slots=True)
class ProofConflict:
    target: str
    scope: ProofScope
    conclusion_receipt_ids: tuple[str, ...]
    exact_reason: str


@dataclass(frozen=True, slots=True)
class UnresolvedTarget:
    target: str
    scope: ProofScope
    reason: str
    supporting_receipt_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProofState:
    immutable_execution_scope: ProofScope
    frozen_rule_set: "FrozenRuleRegistry"
    receipt_store: tuple[DerivationReceipt, ...] = ()
    proof_genealogies: tuple[ProofGenealogy, ...] = ()
    conflicts: tuple[ProofConflict, ...] = ()
    unresolved_targets: tuple[UnresolvedTarget, ...] = ()
    reopen_requests: tuple[Any, ...] = ()
    proposition_type_registry: FrozenPropositionTypeRegistry | None = None
    proposition_store: tuple[Any, ...] = ()
    grounding_genealogies: tuple[Any, ...] = ()

    @property
    def derived_m_count(self) -> int:
        return sum(
            receipt.status == "DERIVED_M" for receipt in self.receipt_store
        )

    def with_receipt(
        self,
        receipt: DerivationReceipt,
        genealogy: ProofGenealogy | None = None,
    ) -> "ProofState":
        genealogies = self.proof_genealogies
        if genealogy is not None and genealogy not in genealogies:
            genealogies += (genealogy,)
        receipts = self.receipt_store
        if receipt not in receipts:
            receipts += (receipt,)
        return replace(
            self,
            receipt_store=receipts,
            proof_genealogies=genealogies,
        )


@dataclass(frozen=True, slots=True)
class RuleApplicationResult:
    rule_id: str
    applied: bool
    receipt: DerivationReceipt | None
    genealogy: ProofGenealogy | None
    reason: str


@dataclass(frozen=True, slots=True)
class ProofExecutionResult:
    status: str
    state: ProofState
    new_receipts: tuple[DerivationReceipt, ...]
    frontier: str
    new_propositions: tuple[Any, ...] = ()

    @property
    def new_derived_m_count(self) -> int:
        return sum(
            receipt.status == "DERIVED_M" for receipt in self.new_receipts
        )


@dataclass(frozen=True, slots=True)
class FrozenRuleRegistry:
    rules: tuple[InferenceRule, ...] = ()
    repository_root: Path | str = Path(".")

    def __post_init__(self) -> None:
        root = Path(self.repository_root).resolve()
        object.__setattr__(self, "repository_root", root)
        object.__setattr__(self, "rules", _as_tuple(self.rules))
        identities = tuple(rule.identity for rule in self.rules)
        if len(identities) != len(set(identities)):
            raise ValueError("Frozen rule identities must be unique.")
        for rule in self.rules:
            self._verify_rule(rule)

    def _verify_rule(self, rule: InferenceRule) -> None:
        path = self.repository_root / rule.authority_source
        if not path.is_file():
            raise ValueError(
                f"Rule authority source is missing: {rule.authority_source}"
            )
        start, end = rule.authority_range
        lines = path.read_bytes().splitlines(keepends=True)
        selected = lines[start - 1 : end]
        if len(selected) != end - start + 1:
            raise ValueError("Rule authority range is incomplete.")
        actual = hashlib.sha256(b"".join(selected)).hexdigest()
        if actual != rule.authority_range_hash:
            raise ValueError("Rule authority range hash mismatch.")
        if rule.rule_class == RuleClass.MECHANICAL_INFERENCE_RULE:
            if not rule.separately_audited_authorization:
                raise ValueError(
                    "Mechanical inference rules require separate audit "
                    "authorization."
                )
            if not rule.premise_schema or not rule.scope_constraints:
                raise ValueError(
                    "Mechanical inference rule schemas must be complete."
                )
            if not rule.implementation_id or not rule.implementation_hash:
                raise ValueError(
                    "Mechanical inference rules require a frozen "
                    "implementation identity and hash."
                )

    @property
    def mechanical_rules(self) -> tuple[InferenceRule, ...]:
        return tuple(
            rule
            for rule in self.rules
            if rule.rule_class == RuleClass.MECHANICAL_INFERENCE_RULE
        )

    @property
    def mechanical_rule_count(self) -> int:
        return len(self.mechanical_rules)

    def get(self, rule_id: str) -> InferenceRule:
        matches = tuple(rule for rule in self.rules if rule.rule_id == rule_id)
        if len(matches) != 1:
            raise KeyError(f"Rule is not uniquely registered: {rule_id}")
        return matches[0]

    def register(
        self,
        rule: InferenceRule,
        implementation: Callable[..., Any] | None = None,
    ) -> "FrozenRuleRegistry":
        if implementation is not None:
            if not callable(implementation):
                raise TypeError("Rule implementation must be callable.")
            if not rule.semantic_specification:
                raise ValueError(
                    "A callback cannot define missing rule semantics."
                )
            try:
                implementation_source = inspect.getsource(implementation)
            except (OSError, TypeError) as exc:
                raise ValueError(
                    "Rule implementation source must be inspectable."
                ) from exc
            actual_implementation_hash = semantic_hash(
                implementation_source
            )
            if actual_implementation_hash != rule.implementation_hash:
                raise ValueError("Rule implementation hash mismatch.")
        return FrozenRuleRegistry(
            rules=self.rules + (rule,),
            repository_root=self.repository_root,
        )


class ProofKernel:
    """Apply only exact frozen rules; never invent mechanical content."""

    def __init__(
        self,
        registry: FrozenRuleRegistry | None = None,
        repository_root: Path | str = Path("."),
        proposition_types: FrozenPropositionTypeRegistry | None = None,
    ) -> None:
        self.registry = registry or FrozenRuleRegistry(
            repository_root=repository_root
        )
        self.proposition_types = proposition_types or (
            default_proposition_type_registry(repository_root)
        )

    def validate_proposition_type(
        self, type_id: PropositionType | str
    ) -> Any:
        return self.proposition_types.get(type_id)

    def validate_proposition_scope(
        self,
        type_id: PropositionType | str,
        scope: ProofScope,
    ) -> ProofScope:
        return self.proposition_types.validate_scope(type_id, scope)

    def admit_grounded_premise(
        self,
        proposition: MechanicalProposition,
        validation: Any,
    ) -> bool:
        if (
            not isinstance(proposition, MechanicalProposition)
            or proposition.origin != PropositionOrigin.GROUNDED_EXTERNAL
            or not proposition.historically_valid
            or not proposition.currently_applicable
            or not getattr(validation, "valid", False)
            or getattr(validation, "proposition", None) is not proposition
            or getattr(validation, "receipt", None) is None
        ):
            return False
        spec = self.proposition_types.get(proposition.predicate_type)
        if spec.constructor_policy != ConstructorPolicy.TRUSTED_GROUNDING_ONLY:
            return False
        try:
            self.proposition_types.validate_scope(
                proposition.predicate_type,
                proposition.mechanical_scope,
            )
        except (KeyError, ValueError):
            return False
        ancestry = proposition.grounding_ancestry
        validation_id = getattr(validation, "validation_id", "")
        return bool(
            ancestry
            and validation_id
            and validation_id in getattr(ancestry, "validation_ids", ())
            and getattr(ancestry, "trust_root_ids", ())
            and getattr(ancestry, "assertion_ids", ())
            and getattr(ancestry, "mechanical_scope", None)
            == proposition.mechanical_scope
        )

    @staticmethod
    def exact_proposition_match(
        proposition: MechanicalProposition,
        *,
        required_type: PropositionType,
        allowed_origins: tuple[PropositionOrigin, ...],
        exact_scope: ProofScope,
        required_subject_receipt_ids: tuple[str, ...] = (),
        require_current: bool = True,
    ) -> bool:
        """Validate an exact typed premise without inferring equivalence."""
        return bool(
            isinstance(proposition, MechanicalProposition)
            and proposition.predicate_type == PropositionType(required_type)
            and proposition.origin
            in tuple(PropositionOrigin(item) for item in allowed_origins)
            and proposition.mechanical_scope == exact_scope
            and (
                not required_subject_receipt_ids
                or proposition.subject_receipt_ids
                == tuple(required_subject_receipt_ids)
            )
            and proposition.historically_valid
            and (proposition.currently_applicable or not require_current)
        )

    @staticmethod
    def compose_grounding_ancestry(
        propositions: tuple[MechanicalProposition, ...],
        *,
        exact_scope: ProofScope,
    ) -> Any:
        """Compose only deterministic provenance sets for exact premises."""
        from .grounding import GroundingAncestry

        ancestries = tuple(
            item.grounding_ancestry
            for item in propositions
            if item.grounding_ancestry is not None
        )
        if not ancestries:
            return GroundingAncestry(mechanical_scope=exact_scope)
        return GroundingAncestry(
            trust_root_ids=tuple(
                root
                for ancestry in ancestries
                for root in ancestry.trust_root_ids
            ),
            contract_references=tuple(
                reference
                for ancestry in ancestries
                for reference in ancestry.contract_references
            ),
            assertion_ids=tuple(
                assertion
                for ancestry in ancestries
                for assertion in ancestry.assertion_ids
            ),
            acquisition_channel_ids=tuple(
                channel
                for ancestry in ancestries
                for channel in ancestry.acquisition_channel_ids
            ),
            trace_ids=tuple(
                trace
                for ancestry in ancestries
                for trace in ancestry.trace_ids
            ),
            validation_ids=tuple(
                validation
                for ancestry in ancestries
                for validation in ancestry.validation_ids
            ),
            mechanical_scope=exact_scope,
        )

    @staticmethod
    def exact_proposition_premise_match(
        rule: InferenceRule,
        propositions: tuple[MechanicalProposition, ...],
    ) -> tuple[MechanicalProposition, ...] | None:
        available = list(propositions)
        selected = []
        for schema in rule.premise_schema:
            prefix = "MECHANICAL_PROPOSITION:"
            if not schema.startswith(prefix):
                return None
            try:
                required_type = PropositionType(schema[len(prefix) :])
            except ValueError:
                return None
            match = next(
                (
                    item
                    for item in available
                    if item.predicate_type == required_type
                    and item.currently_applicable
                ),
                None,
            )
            if match is None:
                return None
            selected.append(match)
            available.remove(match)
        return tuple(selected)

    @staticmethod
    def exact_premise_match(
        rule: InferenceRule,
        receipts: tuple[DerivationReceipt, ...],
        *,
        required_receipt_ids: tuple[str, ...] = (),
    ) -> tuple[DerivationReceipt, ...] | None:
        if required_receipt_ids:
            by_id = {receipt.receipt_id: receipt for receipt in receipts}
            if any(item not in by_id for item in required_receipt_ids):
                return None
            selected = tuple(by_id[item] for item in required_receipt_ids)
        else:
            selected = receipts
        available_statuses = [receipt.status for receipt in selected]
        required_statuses = list(rule.premise_schema)
        for status in required_statuses:
            if status not in available_statuses:
                return None
            available_statuses.remove(status)
        return selected

    @staticmethod
    def scope_authorized(
        premise_scope: ProofScope,
        conclusion_scope: ProofScope,
        authorized_relations: tuple[
            tuple[ProofScope, ProofScope], ...
        ] = (),
    ) -> bool:
        return (
            premise_scope == conclusion_scope
            or (premise_scope, conclusion_scope) in authorized_relations
        )

    def accept_application(
        self,
        rule_id: str,
        premises: tuple[DerivationReceipt, ...],
        conclusion: DerivationReceipt,
        *,
        premise_scope: ProofScope,
        conclusion_scope: ProofScope,
        authorized_scope_relations: tuple[
            tuple[ProofScope, ProofScope], ...
        ] = (),
    ) -> RuleApplicationResult:
        rule = self.registry.get(rule_id)
        if self.exact_premise_match(rule, premises) is None:
            return RuleApplicationResult(
                rule_id, False, None, None, "Exact typed premises not present."
            )
        if not self.scope_authorized(
            premise_scope,
            conclusion_scope,
            authorized_scope_relations,
        ):
            return RuleApplicationResult(
                rule_id, False, None, None, "Scope transfer is not authorized."
            )
        if not set(receipt.receipt_id for receipt in premises).issubset(
            conclusion.input_receipt_ids
        ):
            return RuleApplicationResult(
                rule_id, False, None, None, "Parent provenance is incomplete."
            )
        if (
            rule.rule_class
            in {
                RuleClass.ACCESS_REPRESENTATION_RULE,
                RuleClass.EXECUTION_CONTROL_RULE,
            }
            and conclusion.status == "DERIVED_M"
        ):
            raise ValueError(
                f"{rule.rule_class.value} cannot emit DERIVED_M."
            )
        if (
            conclusion.status == "DERIVED_M"
            and rule.rule_class != RuleClass.MECHANICAL_INFERENCE_RULE
        ):
            raise ValueError(
                "Only a mechanical inference rule may emit DERIVED_M."
            )
        genealogy = ProofGenealogy(
            conclusion_identity=conclusion.receipt_id,
            parent_receipt_ids=tuple(
                receipt.receipt_id for receipt in premises
            ),
            rule_id=rule.rule_id,
            rule_hash=rule.semantic_specification_hash,
        )
        return RuleApplicationResult(
            rule_id, True, conclusion, genealogy, "Exact rule accepted."
        )

    def close(
        self,
        *,
        receipts: tuple[DerivationReceipt, ...],
        scope: ProofScope,
        target: str = "first substantive mechanical inference rule",
        authority_range: str,
        authority_range_hash: str,
        propositions: tuple[Any, ...] = (),
        grounding_validations: tuple[Any, ...] = (),
    ) -> ProofExecutionResult:
        initial_derived_ids = {
            receipt.receipt_id
            for receipt in receipts
            if receipt.status == "DERIVED_M"
        }
        admitted_validations = tuple(
            validation
            for validation in grounding_validations
            if getattr(validation, "proposition", None) is not None
            and self.admit_grounded_premise(
                validation.proposition, validation
            )
        )
        admitted_grounded = tuple(
            validation.proposition for validation in admitted_validations
        )
        proposition_by_id = {}
        for item in propositions + admitted_grounded:
            if isinstance(item, MechanicalProposition):
                proposition_by_id.setdefault(item.proposition_id, item)
        stored_propositions = tuple(proposition_by_id.values())
        grounding_genealogies = tuple(
            genealogy
            for validation in admitted_validations
            if (
                (genealogy := getattr(validation, "genealogy", None))
                is not None
            )
        )
        state = ProofState(
            immutable_execution_scope=scope,
            frozen_rule_set=self.registry,
            receipt_store=receipts,
            proposition_type_registry=self.proposition_types,
            proposition_store=stored_propositions,
            grounding_genealogies=grounding_genealogies,
        )
        registered_count = self.registry.mechanical_rule_count
        unresolved = UnresolvedTarget(
            target=target,
            scope=scope,
            reason=(
                (
                    "No authorized positive mechanical inference rule is "
                    "registered"
                    if registered_count == 0
                    else (
                        (
                            "A grounded acquisition-trace premise exists, "
                            "but no registered theorem has that exact premise"
                            if admitted_grounded
                            else "A positive mechanical theorem is registered, "
                            "but no valid raw mechanical proposition premise "
                            "exists"
                        )
                    )
                )
                + "; failure to derive is not a negative fact."
            ),
            supporting_receipt_ids=tuple(
                receipt.receipt_id for receipt in receipts
            ),
        )
        frontier_receipt = DerivationReceipt.create(
            operation_name="proof_kernel.proof_closure",
            authoritative_source_file=AMENDMENT_05_SOURCE,
            authoritative_clause=(
                f"{authority_range}; source_sha256={authority_range_hash}"
            ),
            input_receipt_ids=tuple(
                receipt.receipt_id for receipt in receipts
            ),
            accessible_evidence=(
                "exact frozen rule registry inspected",
                f"registered mechanical rule count is {registered_count}",
                "valid raw REAL_DIFFERENCE_EXISTS premise count is zero",
                (
                    f"admitted grounded acquisition-trace premise count is "
                    f"{len(admitted_grounded)}"
                ),
                "no candidate mechanism generated",
            ),
            operation_performed=(
                "Computed proof closure over the immutable access snapshot."
            ),
            resulting_difference_or_consequence=(
                "No positive raw mechanical conclusion was authorized."
            ),
            status="UNRESOLVED",
            implementation_source="m_machine/proof_kernel.py",
            clause_id="proof_kernel.current_raw_frontier",
        )
        state = replace(
            state.with_receipt(frontier_receipt),
            unresolved_targets=(unresolved,),
        )
        new_receipts = tuple(
            receipt
            for receipt in state.receipt_store
            if receipt.receipt_id not in {
                item.receipt_id for item in receipts
            }
        )
        if any(
            receipt.status == "DERIVED_M"
            and receipt.receipt_id not in initial_derived_ids
            for receipt in state.receipt_store
        ):
            raise RuntimeError(
                "Proof kernel created DERIVED_M without a mechanical rule."
            )
        has_pairwise = any(
            item.predicate_type
            == PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES
            for item in admitted_grounded
        )
        return ProofExecutionResult(
            status="UNRESOLVED",
            state=state,
            new_receipts=new_receipts,
            frontier=(
                NON_IDENTITY_RULE_REGISTRATION_FRONTIER
                if has_pairwise
                else POST_GROUNDING_MECHANICAL_RECONSTRUCTION_FRONTIER
                if admitted_grounded
                else FIRST_MECHANICAL_INFERENCE_RULE_FRONTIER
                if registered_count == 0
                else RAW_MECHANICAL_BOOTSTRAP_FRONTIER
            ),
            new_propositions=stored_propositions,
        )
