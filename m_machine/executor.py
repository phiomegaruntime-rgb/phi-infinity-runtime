"""Public receipt-gated M-only execution path."""

from dataclasses import dataclass
from typing import Any, Callable, Literal

from src.boundary import BoundaryEffectReceipt
from src.core import PhiSubstrateEngine
from src.membrane import MembraneEvaluator

from .access import DeNamedAccess, RawAccessibleConfiguration, de_name
from .access_integrity import (
    AccessPackage,
    RelationQualifiedAccess,
    de_name_access_package,
    qualify_relation_witness,
    verify_access_package,
)
from .discriminability import (
    BasisAccess,
    BasisLocalDiscriminabilitySet,
    evaluate_basis_local,
)
from .adapters import (
    native_boundary_step,
    native_compute_coupling,
    native_membrane_evaluate,
    native_step,
)
from .boot import BootVerification, verify_authoritative_boot
from .clauses import (
    AuthoritativeClause,
    AuthoritativeClauseRegistry,
    compile_authoritative_clause_registry,
)
from .receipts import DerivationReceipt
from .proof_kernel import (
    ProofKernel,
)
from .mechanical_propositions import default_proposition_type_registry
from .mechanical_rules import default_mechanical_rule_registry
from .grounding import (
    GroundedExecutionState,
    GroundingAssertion,
    GroundingRegistry,
    PairwiseGroundingAssertion,
    default_grounding_registry,
)
from .registry import OperationRegistry, OperationResult
from .scheduler import MOnlyScheduler, MRule, SchedulerResult


ExecutionStatus = Literal[
    "CONTINUATION",
    "UNRESOLVED",
    "REOPEN",
    "FIRST_DIVERGENCE",
    "BLOCKED_EXTERNAL",
]


@dataclass(frozen=True, slots=True)
class ReopenRequest:
    """Control flow exposing only the unresolved M frontier dimensions."""

    receipt_chain: tuple[str, ...] = ()
    missing_prerequisite: str = ""
    discrimination_reason: str = ""
    scale: bool = False
    field: bool = False
    boundary: bool = False
    genealogy: bool = False
    access: bool = False
    replacement_value: Any = None
    legacy_phase2_view: bool = False

    def __post_init__(self) -> None:
        if not self.receipt_chain:
            raise ValueError("A reopen request requires a receipt chain.")
        if not self.missing_prerequisite:
            raise ValueError("A missing prerequisite is required.")
        if not self.discrimination_reason:
            raise ValueError("A discrimination reason is required.")
        if self.replacement_value is not None:
            raise ValueError("REOPEN cannot contain a guessed replacement.")
        if not any(self.dimensions):
            raise ValueError(
                "A reopen request must expose at least one dimension."
            )

    @property
    def dimensions(self) -> tuple[str, ...]:
        if self.legacy_phase2_view:
            return (
                "scale",
                "field",
                "boundary",
                "genealogy",
                "access",
            )
        return self.required_dimensions

    @property
    def required_dimensions(self) -> tuple[str, ...]:
        return tuple(
            name
            for name, enabled in (
                ("scale", self.scale),
                ("field", self.field),
                ("boundary", self.boundary),
                ("genealogy", self.genealogy),
                ("access", self.access),
            )
            if enabled
        )


@dataclass(frozen=True, slots=True)
class MExecutionAccess:
    """Optional already-available native representation for M-only work."""

    engine: PhiSubstrateEngine
    cluster_indices: tuple[int, ...] = ()
    boundary_receipt: BoundaryEffectReceipt | None = None


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    status: ExecutionStatus
    value: Any
    receipts: tuple[DerivationReceipt, ...]
    reopen_request: ReopenRequest | None = None
    frontier: str | None = None

    def __post_init__(self) -> None:
        if self.status == "CONTINUATION":
            if not self.receipts:
                raise ValueError(
                    "CONTINUATION requires at least one M receipt."
                )
            if any(
                receipt.status != "DERIVED_M"
                for receipt in self.receipts
            ):
                raise ValueError(
                    "CONTINUATION cannot contain non-M receipts."
                )

    @property
    def continuation_allowed(self) -> bool:
        return self.status == "CONTINUATION"


class TranslationBlockedError(RuntimeError):
    """Raised when translation is requested before M derivation terminates."""


def translate_after_derivation(
    result: ExecutionResult,
    translator: Callable[[Any], Any],
) -> Any:
    """Open the translation boundary only for a complete continuation."""

    if not result.continuation_allowed:
        raise TranslationBlockedError(
            "Translation requires a completed M derivation."
        )
    return translator(result.value)


class MExecutionMachine:
    """A boot-verified, scheduler-driven M-only executor."""

    def __init__(
        self,
        repository_root: str | None = None,
        registry: OperationRegistry | None = None,
    ) -> None:
        self.boot: BootVerification = verify_authoritative_boot(
            repository_root
        )
        self.clauses: AuthoritativeClauseRegistry = (
            compile_authoritative_clause_registry(
                self.boot.repository_root
            )
        )
        if registry is not None:
            raise ValueError(
                "MExecutionMachine cannot accept an injected registry; "
                "its compiled M-only registry is mandatory."
            )
        self.registry = self._default_registry(self.clauses)
        self.scheduler = MOnlyScheduler()
        self.raw_rule_registry = default_mechanical_rule_registry(
            self.boot.repository_root
        )
        self.proposition_types = default_proposition_type_registry(
            self.boot.repository_root
        )
        self.proof_kernel = ProofKernel(
            registry=self.raw_rule_registry,
            proposition_types=self.proposition_types,
        )
        self.grounding_base = default_grounding_registry(
            self.boot.repository_root
        )
        self._membrane = MembraneEvaluator()

    @staticmethod
    def _default_registry(
        clauses: AuthoritativeClauseRegistry,
    ) -> OperationRegistry:
        registry = OperationRegistry()
        registry.register_m_only(
            "native.compute_coupling",
            lambda engine, **kwargs: native_compute_coupling(
                engine,
                clause=clauses.get("m.dependencies"),
                **kwargs,
            ),
        )
        registry.register_m_only(
            "native.step",
            lambda engine, **kwargs: native_step(
                engine,
                clause=clauses.get("m.transformations"),
                **kwargs,
            ),
        )
        registry.register_m_only(
            "native.membrane_evaluate",
            lambda evaluator, engine, cluster_indices, **kwargs: (
                native_membrane_evaluate(
                    evaluator,
                    engine,
                    cluster_indices,
                    clause=clauses.get("m.consequences"),
                    **kwargs,
                )
            ),
        )
        registry.register_m_only(
            "native.boundary_step",
            lambda engine, boundary_receipt, **kwargs: native_boundary_step(
                engine,
                boundary_receipt,
                clause=clauses.get("m.boundary_exchange"),
                **kwargs,
            ),
        )

        for name in (
            "legacy.field_bridge.reconstruct_phi_candidates",
            "scipy.optimize",
            "nearest_neighbour",
            "interpolation",
            "regression",
            "machine_learning",
            "fixed_latent_search_bounds",
            "random_inverse_search_seed",
            "external_residual_metric",
            "external_acceptance_predicate",
            "external_causal_category",
        ):
            registry.register_external(name)
        return registry

    def execute(
        self,
        access: RawAccessibleConfiguration | DeNamedAccess | AccessPackage,
    ) -> ExecutionResult:
        """Execute every currently eligible M-derived rule, then stop."""

        if isinstance(access, AccessPackage):
            return self._execute_access_package(access)

        named_access = (
            access
            if isinstance(access, DeNamedAccess)
            else de_name(access)
        )
        initial_receipts = (named_access.receipt,)
        native_access = named_access.raw_access.m_execution_access

        if native_access is None:
            rules = (
                MRule(
                    rule_id="raw.missing_representation",
                    operation_name="m.raw_difference_frontier",
                    required_operations=("DeName",),
                    handler=self._missing_representation,
                ),
            )
            scheduled = self.scheduler.run(
                initial_receipts=initial_receipts,
                rules=rules,
                context=named_access,
            )
            return self._result_from_scheduler(
                named_access,
                scheduled,
                reopen_dimensions=self._raw_reopen_dimensions(
                    named_access.raw_access
                ),
                missing_prerequisite=(
                    "M-derived difference/dependency representation"
                ),
                discrimination_reason=(
                    "Current raw access does not uniquely discriminate the"
                    " next mechanical relation."
                ),
                frontier_override="difference/dependency reconstruction",
                legacy_phase2_view=isinstance(access, DeNamedAccess),
            )

        if not isinstance(native_access, MExecutionAccess):
            rules = (
                MRule(
                    rule_id="raw.unsupported_representation",
                    operation_name="m.unsupported_representation",
                    required_operations=("DeName",),
                    handler=self._unsupported_representation,
                ),
            )
            scheduled = self.scheduler.run(
                initial_receipts=initial_receipts,
                rules=rules,
                context=named_access,
            )
            return self._result_from_scheduler(
                named_access,
                scheduled,
                reopen_dimensions=("access",),
                missing_prerequisite="recognized native M representation",
                discrimination_reason=(
                    "Current access supplies a representation that the"
                    " authoritative M adapter cannot identify."
                ),
                frontier_override="native representation",
            )

        rules = self._native_rules(native_access)
        scheduled = self.scheduler.run(
            initial_receipts=initial_receipts,
            rules=rules,
            context=named_access,
        )
        if scheduled.status == "CONTINUATION":
            values = scheduled.value_map()
            return ExecutionResult(
                status="CONTINUATION",
                value={
                    "coupling": values.get("native.compute_coupling"),
                    "transformation": values.get(
                        "native.step",
                        values.get("native.boundary_step"),
                    ),
                    **(
                        {"membrane": values["native.membrane_evaluate"]}
                        if "native.membrane_evaluate" in values
                        else {}
                    ),
                },
                receipts=scheduled.receipts,
            )

        dimensions = ("boundary", "access") if (
            native_access.boundary_receipt is not None
            and scheduled.status == "UNRESOLVED"
        ) else ("access",)
        return self._result_from_scheduler(
            named_access,
            scheduled,
            reopen_dimensions=dimensions,
            missing_prerequisite=(
                "resolved boundary consequence"
                if dimensions[0] == "boundary"
                else scheduled.frontier or "M-derived prerequisite"
            ),
            discrimination_reason=(
                "Current access cannot discriminate the unresolved"
                " continuation relation."
            ),
        )

    def execute_grounded(
        self,
        package: AccessPackage,
        assertion: GroundingAssertion,
        *,
        grounding_base: GroundingRegistry | None = None,
    ) -> ExecutionResult:
        """Explicitly validate one supplied assertion; trust nothing by default."""

        if not isinstance(package, AccessPackage):
            raise TypeError("execute_grounded() requires an AccessPackage.")
        if not isinstance(assertion, GroundingAssertion):
            raise TypeError("execute_grounded() requires a GroundingAssertion.")
        base = grounding_base or self.grounding_base
        if not isinstance(base, GroundingRegistry):
            raise TypeError("grounding_base must be a GroundingRegistry.")

        access_result = self._execute_access_package(package)
        recorded = base.record_assertion(assertion)
        validation = recorded.validate_assertion(
            assertion,
            self.proposition_types,
        )
        if not validation.valid:
            return ExecutionResult(
                status="UNRESOLVED",
                value=GroundedExecutionState(
                    access_value=access_result.value,
                    grounding_base=recorded,
                    validation=validation,
                    proof_result=None,
                ),
                receipts=access_result.receipts,
                reopen_request=None,
                frontier=access_result.frontier,
            )

        accepted = recorded.accept_validation(validation)
        proof_clause = self.clauses.get("proof_kernel.current_raw_frontier")
        proof_result = self.proof_kernel.close(
            receipts=access_result.receipts + (validation.receipt,),
            scope=assertion.mechanical_scope,
            target="post-grounding mechanical reconstruction",
            authority_range=proof_clause.source_text_reference,
            authority_range_hash=proof_clause.exact_source_text_hash,
            propositions=(validation.proposition,),
            grounding_validations=(validation,),
        )
        return ExecutionResult(
            status="UNRESOLVED",
            value=GroundedExecutionState(
                access_value=access_result.value,
                grounding_base=accepted,
                validation=validation,
                proof_result=proof_result,
            ),
            receipts=proof_result.state.receipt_store,
            reopen_request=None,
            frontier=proof_result.frontier,
        )

    def execute_pairwise_grounded(
        self,
        assertion: PairwiseGroundingAssertion,
        *,
        grounding_base: GroundingRegistry | None = None,
    ) -> GroundedExecutionState:
        """Admit one explicit pairwise premise, then stop without an M rule."""
        if not isinstance(assertion, PairwiseGroundingAssertion):
            raise TypeError(
                "execute_pairwise_grounded() requires a "
                "PairwiseGroundingAssertion."
            )
        base = grounding_base or self.grounding_base
        recorded = (
            base
            if assertion in base.pairwise_assertions
            else base.record_pairwise_assertion(assertion)
        )
        validation = recorded.validate_pairwise_assertion(
            assertion, self.proposition_types
        )
        accepted = recorded.accept_pairwise_validation(validation)
        receipts = (
            (validation.receipt,)
            if validation.valid and validation.receipt is not None
            else ()
        )
        proof_result = self.proof_kernel.close(
            receipts=receipts,
            scope=assertion.mechanical_scope,
            target="pairwise grounded non-identity premise",
            authority_range="Amendment 08 pairwise execution frontier",
            authority_range_hash=self.clauses.get(
                "pairwise_grounding.frontier"
            ).exact_source_text_hash,
            grounding_validations=(validation,),
        )
        return GroundedExecutionState(
            access_value=None,
            grounding_base=accepted,
            validation=validation,
            proof_result=proof_result,
        )

    def _execute_access_package(
        self,
        package: AccessPackage,
    ) -> ExecutionResult:
        """Qualify supplied relations, then stop before discriminability."""

        verification = verify_access_package(package)
        denamed = de_name_access_package(package)
        receipts = [verification.receipt, denamed.receipt]
        witnesses = list(package.supplied_witnesses)
        for _, witness in package.witness_referent_map:
            if not any(candidate is witness for candidate in witnesses):
                witnesses.append(witness)

        connected = []
        unresolved = []
        non_direct = []
        for witness in witnesses:
            qualification = qualify_relation_witness(package, witness)
            receipts.append(qualification.receipt)
            if qualification.status == "CONNECTED":
                connected.append(witness)
            elif qualification.status == "UNRESOLVED":
                unresolved.append(witness)
            else:
                non_direct.append(witness)

        qualified = RelationQualifiedAccess(
            package=package,
            connected_witnesses=tuple(connected),
            unresolved_witnesses=tuple(unresolved),
            non_direct_witnesses=tuple(non_direct),
        )
        if isinstance(package.basis_access, BasisAccess):
            basis_results = []
            for basis in package.basis_access.bases:
                for witness in connected:
                    first_matches = package.local_referent_map.resolve(
                        witness.endpoint_1
                    )
                    second_matches = package.local_referent_map.resolve(
                        witness.endpoint_2
                    )
                    if len(first_matches) != 1 or len(second_matches) != 1:
                        continue
                    basis_result = evaluate_basis_local(
                        package,
                        witness,
                        first_matches[0],
                        second_matches[0],
                        basis,
                    )
                    basis_results.append(basis_result)
                    receipts.append(basis_result.receipt)
            qualified_with_bases = BasisLocalDiscriminabilitySet(
                connected_access=qualified,
                results=tuple(basis_results),
            )
            proof_clause = self.clauses.get(
                "proof_kernel.current_raw_frontier"
            )
            proof_result = self.proof_kernel.close(
                receipts=tuple(receipts),
                scope=(
                    ("access", str(package.access_instance)),
                    ("basis_family", "preserved_independently"),
                ),
                authority_range=proof_clause.source_text_reference,
                authority_range_hash=proof_clause.exact_source_text_hash,
            )
            return ExecutionResult(
                status="UNRESOLVED",
                value=qualified_with_bases,
                receipts=proof_result.state.receipt_store,
                reopen_request=None,
                frontier=proof_result.frontier,
            )

        reopen = ReopenRequest(
            receipt_chain=self._receipt_ids(tuple(receipts)),
            missing_prerequisite="Discriminable_a(x,y)",
            discrimination_reason=(
                "Direct access relations are qualified, but Amendment 03 "
                "does not define whether their local referents are "
                "discriminable."
            ),
            access=True,
        )
        return ExecutionResult(
            status="UNRESOLVED",
            value=qualified,
            receipts=tuple(receipts),
            reopen_request=reopen,
            frontier="DISCRIMINABILITY_FRONTIER",
        )

    @property
    def raw_fireable_positive_mechanical_rule_count(self) -> int:
        return 0

    def _native_rules(
        self,
        native_access: MExecutionAccess,
    ) -> tuple[MRule, ...]:
        rules = [
            MRule(
                rule_id="native.coupling",
                operation_name="native.compute_coupling",
                required_operations=("DeName",),
                handler=self._run_coupling,
            ),
            MRule(
                rule_id="native.transformation",
                operation_name=(
                    "native.boundary_step"
                    if native_access.boundary_receipt is not None
                    else "native.step"
                ),
                required_operations=("native.compute_coupling",),
                handler=self._run_transformation,
            ),
        ]
        if native_access.cluster_indices:
            rules.append(
                MRule(
                    rule_id="native.membrane",
                    operation_name="native.membrane_evaluate",
                    required_operations=(
                        "native.boundary_step"
                        if native_access.boundary_receipt is not None
                        else "native.step",
                    ),
                    handler=self._run_membrane,
                )
            )
        return tuple(rules)

    def _run_coupling(
        self,
        receipts: tuple[DerivationReceipt, ...],
        context: DeNamedAccess,
    ) -> OperationResult:
        return self.registry.invoke(
            "native.compute_coupling",
            context.raw_access.m_execution_access.engine,
            input_receipt_ids=self._receipt_ids(receipts),
            accessible_evidence=("native engine state supplied",),
        )

    def _run_transformation(
        self,
        receipts: tuple[DerivationReceipt, ...],
        context: DeNamedAccess,
    ) -> OperationResult:
        native_access = context.raw_access.m_execution_access
        kwargs = {
            "input_receipt_ids": self._receipt_ids(receipts),
            "accessible_evidence": ("native engine state supplied",),
        }
        if native_access.boundary_receipt is None:
            return self.registry.invoke(
                "native.step",
                native_access.engine,
                **kwargs,
            )
        return self.registry.invoke(
            "native.boundary_step",
            native_access.engine,
            native_access.boundary_receipt,
            accessible_evidence=(
                "boundary receipt supplied",
                "boundary receipt must be resolved",
            ),
            input_receipt_ids=self._receipt_ids(receipts),
        )

    def _run_membrane(
        self,
        receipts: tuple[DerivationReceipt, ...],
        context: DeNamedAccess,
    ) -> OperationResult:
        native_access = context.raw_access.m_execution_access
        return self.registry.invoke(
            "native.membrane_evaluate",
            self._membrane,
            native_access.engine,
            native_access.cluster_indices,
            input_receipt_ids=self._receipt_ids(receipts),
            accessible_evidence=("native cluster representation supplied",),
        )

    def _missing_representation(
        self,
        receipts: tuple[DerivationReceipt, ...],
        context: DeNamedAccess,
    ) -> OperationResult:
        clause = self.clauses.get("m.differences")
        return OperationResult(
            operation_name="m.raw_difference_frontier",
            value=None,
            receipt=self._frontier_receipt(
                operation_name="m.raw_difference_frontier",
                clause=clause,
                receipts=receipts,
                evidence=(
                    "raw accessible values preserved",
                    "no M-derived native state representation supplied",
                ),
                performed=(
                    "Checked whether the raw access supplies the next"
                    " M-derived difference operation."
                ),
                consequence=(
                    "Difference discovery is partial; no guessed"
                    " transformation was created."
                ),
            ),
        )

    def _unsupported_representation(
        self,
        receipts: tuple[DerivationReceipt, ...],
        context: DeNamedAccess,
    ) -> OperationResult:
        clause = self.clauses.get("m.accessible_configuration")
        return OperationResult(
            operation_name="m.unsupported_representation",
            value=None,
            receipt=self._frontier_receipt(
                operation_name="m.unsupported_representation",
                clause=clause,
                receipts=receipts,
                evidence=("unsupported native representation supplied",),
                performed="Refused an unrecognized representation.",
                consequence=(
                    "No external conversion or guessed representation"
                    " was attempted."
                ),
            ),
        )

    def _result_from_scheduler(
        self,
        context: DeNamedAccess,
        scheduled: SchedulerResult,
        *,
        reopen_dimensions: tuple[str, ...],
        missing_prerequisite: str,
        discrimination_reason: str,
        frontier_override: str | None = None,
        legacy_phase2_view: bool = False,
    ) -> ExecutionResult:
        reopen = ReopenRequest(
            receipt_chain=self._receipt_ids(scheduled.receipts),
            missing_prerequisite=missing_prerequisite,
            discrimination_reason=discrimination_reason,
            scale="scale" in reopen_dimensions,
            field="field" in reopen_dimensions,
            boundary="boundary" in reopen_dimensions,
            genealogy="genealogy" in reopen_dimensions,
            access="access" in reopen_dimensions,
            legacy_phase2_view=legacy_phase2_view,
        )
        return ExecutionResult(
            status=scheduled.status,
            value=None,
            receipts=scheduled.receipts,
            reopen_request=reopen,
            frontier=frontier_override or scheduled.frontier,
        )

    @staticmethod
    def _receipt_ids(
        receipts: tuple[DerivationReceipt, ...],
    ) -> tuple[str, ...]:
        return tuple(receipt.receipt_id for receipt in receipts)

    @staticmethod
    def _raw_reopen_dimensions(
        access: RawAccessibleConfiguration,
    ) -> tuple[str, ...]:
        dimensions = ["access"]
        if not access.resolution_sampling:
            dimensions.append("scale")
        if not access.genealogy:
            dimensions.append("genealogy")
        if not access.provenance and not access.access_provenance:
            dimensions.append("field")
        return tuple(dimensions)

    @staticmethod
    def _frontier_receipt(
        *,
        operation_name: str,
        clause: AuthoritativeClause,
        receipts: tuple[DerivationReceipt, ...],
        evidence: tuple[str, ...],
        performed: str,
        consequence: str,
    ) -> DerivationReceipt:
        return DerivationReceipt.create(
            operation_name=operation_name,
            authoritative_source_file=clause.authoritative_source_file,
            authoritative_clause=(
                f"{clause.source_text_reference}; "
                f"source_sha256={clause.exact_source_text_hash}"
            ),
            input_receipt_ids=MExecutionMachine._receipt_ids(receipts),
            accessible_evidence=evidence,
            operation_performed=performed,
            resulting_difference_or_consequence=consequence,
            status="UNRESOLVED",
            implementation_source="m_machine/executor.py",
            clause_id=clause.clause_id,
        )