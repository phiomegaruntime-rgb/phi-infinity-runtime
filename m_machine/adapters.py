"""Receipt-emitting adapters for the audited native M-only operations."""

from typing import Any

from src.boundary import (
    BoundaryEffectReceipt,
    UnresolvedExternalFieldError,
    step_with_boundary,
)
from src.core import PhiSubstrateEngine
from src.membrane import MembraneEvaluator

from .clauses import AuthoritativeClause
from .receipts import DerivationReceipt
from .registry import OperationResult


def _receipt(
    *,
    operation_name: str,
    clause: AuthoritativeClause,
    implementation_source: str,
    input_receipt_ids: tuple[str, ...],
    accessible_evidence: tuple[str, ...],
    operation_performed: str,
    consequence: str,
) -> DerivationReceipt:
    return DerivationReceipt.create(
        operation_name=operation_name,
        authoritative_source_file=(
            clause.authoritative_source_file
        ),
        authoritative_clause=(
            f"{clause.source_text_reference}; "
            f"source_sha256={clause.exact_source_text_hash}"
        ),
        input_receipt_ids=input_receipt_ids,
        accessible_evidence=accessible_evidence,
        operation_performed=operation_performed,
        resulting_difference_or_consequence=consequence,
        status="DERIVED_M",
        implementation_source=implementation_source,
        clause_id=clause.clause_id,
    )


def native_step(
    engine: PhiSubstrateEngine,
    clause: AuthoritativeClause,
    *,
    input_receipt_ids: tuple[str, ...] = (),
    accessible_evidence: tuple[str, ...] = (),
) -> OperationResult:
    value = engine._step_phi_mechanics()
    return OperationResult(
        operation_name="native.step",
        value=value,
        receipt=_receipt(
            operation_name="native.step",
            clause=clause,
            implementation_source="src/core.py:35-53",
            input_receipt_ids=input_receipt_ids,
            accessible_evidence=accessible_evidence,
            operation_performed=(
                "Executed the existing native PHI mechanics step."
            ),
            consequence=(
                "Native state, stress, and geometry were transformed."
            ),
        ),
    )


def native_compute_coupling(
    engine: PhiSubstrateEngine,
    clause: AuthoritativeClause,
    *,
    input_receipt_ids: tuple[str, ...] = (),
    accessible_evidence: tuple[str, ...] = (),
) -> OperationResult:
    value = engine.compute_coupling()
    return OperationResult(
        operation_name="native.compute_coupling",
        value=value,
        receipt=_receipt(
            operation_name="native.compute_coupling",
            clause=clause,
            implementation_source="src/core.py:26-33",
            input_receipt_ids=input_receipt_ids,
            accessible_evidence=accessible_evidence,
            operation_performed=(
                "Executed the existing native coupling calculation."
            ),
            consequence=(
                "Pairwise coupling and represented differences are available."
            ),
        ),
    )


def native_membrane_evaluate(
    evaluator: MembraneEvaluator,
    engine: PhiSubstrateEngine,
    cluster_indices: Any,
    clause: AuthoritativeClause,
    *,
    input_receipt_ids: tuple[str, ...] = (),
    accessible_evidence: tuple[str, ...] = (),
) -> OperationResult:
    value = evaluator.evaluate_cluster(
        engine,
        list(cluster_indices),
    )
    return OperationResult(
        operation_name="native.membrane_evaluate",
        value=value,
        receipt=_receipt(
            operation_name="native.membrane_evaluate",
            clause=clause,
            implementation_source="src/membrane.py:12-32",
            input_receipt_ids=input_receipt_ids,
            accessible_evidence=accessible_evidence,
            operation_performed=(
                "Executed the existing native membrane evaluation."
            ),
            consequence=(
                "Represented internal/external cohesion and residual stress"
                " were evaluated."
            ),
        ),
    )


def native_boundary_step(
    engine: PhiSubstrateEngine,
    boundary_receipt: BoundaryEffectReceipt,
    clause: AuthoritativeClause,
    *,
    input_receipt_ids: tuple[str, ...] = (),
    accessible_evidence: tuple[str, ...] = (),
) -> OperationResult:
    try:
        value = step_with_boundary(
            engine,
            boundary_receipt,
            mechanical_progress=1.0,
        )
    except UnresolvedExternalFieldError:
        return OperationResult(
            operation_name="native.boundary_step",
            value=None,
            receipt=DerivationReceipt.create(
                operation_name="native.boundary_step",
                authoritative_source_file=clause.authoritative_source_file,
                authoritative_clause=(
                    f"{clause.source_text_reference}; "
                    f"source_sha256={clause.exact_source_text_hash}"
                ),
                input_receipt_ids=input_receipt_ids,
                accessible_evidence=accessible_evidence,
                operation_performed=(
                    "Blocked boundary evolution because exterior access"
                    " remains unresolved."
                ),
                resulting_difference_or_consequence=(
                    "No local state mutation or fabricated closure was"
                    " admitted."
                ),
                status="UNRESOLVED",
                implementation_source=(
                    "m_machine/adapters.py:native_boundary_step"
                ),
                clause_id=clause.clause_id,
            ),
        )
    return OperationResult(
        operation_name="native.boundary_step",
        value=value,
        receipt=_receipt(
            operation_name="native.boundary_step",
            clause=clause,
            implementation_source="src/boundary.py:334-579,581-798",
            input_receipt_ids=input_receipt_ids,
            accessible_evidence=accessible_evidence,
            operation_performed=(
                "Executed the existing resolved boundary-aware mechanics."
            ),
            consequence=(
                "Resolved boundary consequences were included in the"
                " native transformation."
            ),
        ),
    )