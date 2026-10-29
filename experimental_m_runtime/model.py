"""Frozen data model for the isolated experimental fragment runtime."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .authority import (
    AUTHORITY_SOURCE,
    EXPECTED_AUTHORITY_SHA256,
    FOUNDATION_FORMULA,
    FOUNDATION_SEMANTIC_HASH,
    FOUNDATION_VERSION,
)


M_ONLY_GRAMMAR = (
    "ACCESSIBLE_CONFIGURATION",
    "DIFFERENCE",
    "DEPENDENCY",
    "EXCHANGE",
    "TRANSFORMATION",
    "PROPAGATION",
    "CONSEQUENCE",
    "READJUSTMENT",
    "CONTINUATION",
)


class AccessDiscrimination(str, Enum):
    COMPLETE = "COMPLETE_DISCRIMINATED"
    INSUFFICIENT = "INSUFFICIENT"


class BoundaryVisibility(str, Enum):
    DISCRIMINATED = "DISCRIMINATED"
    NOT_VISIBLE = "NOT_VISIBLE"
    INSUFFICIENT = "INSUFFICIENT"


class Decision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    UNRESOLVED = "UNRESOLVED"
    REOPEN = "REOPEN"


class ContinuityClass(str, Enum):
    ONE_TO_ONE = "1→1"
    ONE_TO_ZERO = "1→0"
    ONE_TO_MANY = "1→n"
    MANY_TO_ONE = "n→1"
    UNRESOLVED = "UNRESOLVED"


class PrimitiveBasis(str, Enum):
    DERIVED_M = "DERIVED_M"
    REGISTERED_ACCESS = "REGISTERED_ACCESS"
    UNDECLARED = "UNDECLARED"


class Stage(str, Enum):
    CATEGORICAL_FOUNDATION = "CATEGORICAL_FOUNDATION"
    M_ONLY = "M_ONLY"
    CONCEPTUAL_SOLUTION = "CONCEPTUAL_SOLUTION"
    FREEZE = "FREEZE"
    EXACT_PATH = "EXACT_PATH"
    FALSE_SUFFICIENCY_ANTI_DRIFT = "FALSE_SUFFICIENCY_ANTI_DRIFT"
    CLASSIFICATION = "CLASSIFICATION"
    OUTPUT = "OUTPUT"


REQUIRED_SURFACE_ROLES = (
    "FOUNDATION",
    "M",
    "INFINITO",
    "FORMULA",
    "ALGORITHM",
    "RULE",
    "RUNTIME",
    "VERIFICATION",
    "ACCESS",
    "DISCRIMINATION",
    "BOUNDARY",
    "RECEIPT",
    "ERROR",
    "OBSERVATION",
    "OUTPUT",
    "STATUS",
    "REASON",
    "AUTHORITY",
    "AUTHORITY_HASH",
    "RUNTIME_HASH",
    "PROVENANCE",
    "ANCESTRY",
    "GENEALOGY",
    "CONTINUATION_CLASS",
    "STATEMENT",
    "GRAMMAR",
    "EXACT_PATH",
    "TYPE_OF_CONTROL",
    "OPERATOR",
    "GATE",
    "VALIDATOR",
    "ADMISSION_CRITERIA",
    "TEST_LANGUAGE",
    "TEST",
    "METADATA",
    "IMPLEMENTATION_DEPENDENCY",
)


@dataclass(frozen=True, slots=True)
class ExperimentalReceipt:
    receipt_id: str
    operation_name: str
    input_receipt_ids: tuple[str, ...]
    accessible_evidence: tuple[str, ...]
    status: Decision | str
    authority_source: str
    authority_hash: str
    digest: str
    receipt_fragment_id: str = ""
    operation_fragment_id: str = ""
    status_fragment_id: str = ""
    digest_fragment_id: str = ""
    authority_fragment_id: str = ""
    evidence_fragment_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Fragment:
    """A represented fragment; representation kind is never causal."""

    fragment_id: str
    represented_kind: str
    parent_fragment_ids: tuple[str, ...] = ()
    contained_by_fragment_ids: tuple[str, ...] = ()
    boundary_visibility: BoundaryVisibility = BoundaryVisibility.DISCRIMINATED
    provenance: tuple[str, ...] = ()
    nominal_name: str = ""

    def __post_init__(self) -> None:
        if not self.fragment_id or not self.represented_kind:
            raise ValueError("A fragment requires an id and represented kind.")
        object.__setattr__(
            self, "parent_fragment_ids", tuple(self.parent_fragment_ids)
        )
        object.__setattr__(
            self,
            "contained_by_fragment_ids",
            tuple(self.contained_by_fragment_ids),
        )
        object.__setattr__(self, "provenance", tuple(self.provenance))
        if len(self.parent_fragment_ids) != len(set(self.parent_fragment_ids)):
            raise ValueError("Fragment parent identities must be unique.")


def make_infinito_fragment(
    fragment_id: str,
    parent_fragment_ids: tuple[str, ...],
    *,
    provenance: tuple[str, ...] = (),
) -> Fragment:
    """Represent Infinito without asserting an absent external boundary."""

    if not parent_fragment_ids:
        raise ValueError("Infinito must be explicitly composed from fragments.")
    return Fragment(
        fragment_id=fragment_id,
        represented_kind="INFINITO",
        parent_fragment_ids=parent_fragment_ids,
        contained_by_fragment_ids=(fragment_id,),
        boundary_visibility=BoundaryVisibility.NOT_VISIBLE,
        provenance=provenance,
        nominal_name="Infinito",
    )


@dataclass(frozen=True, slots=True)
class ConceptualSolution:
    """The M-only solution before freeze; no domain category is a primitive."""

    solution_id: str
    grammar: tuple[str, ...] = M_ONLY_GRAMMAR
    statement: str = (
        "Every explicitly discriminable input is a fragment of one reality "
        "and one Mother Mechanics; representation kinds do not generate "
        "mechanics."
    )
    solution_fragment_id: str = ""
    statement_fragment_id: str = ""
    grammar_fragment_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "grammar", tuple(self.grammar))
        object.__setattr__(
            self, "grammar_fragment_ids", tuple(self.grammar_fragment_ids)
        )


@dataclass(frozen=True, slots=True)
class FragmentClaim:
    """A relation is represented by a fragment, not by a meta-operator."""

    subject_fragment_id: str
    relation_fragment_id: str
    object_fragment_id: str


@dataclass(frozen=True, slots=True)
class CategoricalFoundation:
    """Finite representation of the self-applicable categorical foundation."""

    foundation_id: str
    version: str = FOUNDATION_VERSION
    formula: str = FOUNDATION_FORMULA
    semantic_hash: str = FOUNDATION_SEMANTIC_HASH
    infinito_fragment_id: str = ""
    role_fragment_ids: tuple[tuple[str, str], ...] = ()
    path_fragment_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "role_fragment_ids", tuple(self.role_fragment_ids)
        )
        object.__setattr__(
            self, "path_fragment_ids", tuple(self.path_fragment_ids)
        )


@dataclass(frozen=True, slots=True)
class ContinuationPath:
    continuation_id: str
    predecessor_genealogy_id: str
    successor_fragment_id: str
    continuation_class_id: str


@dataclass(frozen=True, slots=True)
class ContinuityEvidence:
    prior_genealogy_ids: tuple[str, ...]
    continuation_paths: tuple[ContinuationPath, ...]
    access_discrimination: AccessDiscrimination
    evidence_receipt_ids: tuple[str, ...]
    provenance: tuple[str, ...]
    ancestry: tuple[str, ...]
    genealogy_fragment_ids: tuple[str, ...] = ()
    provenance_fragment_ids: tuple[str, ...] = ()
    ancestry_fragment_ids: tuple[str, ...] = ()
    classification_fragment_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "prior_genealogy_ids", tuple(self.prior_genealogy_ids)
        )
        object.__setattr__(
            self, "continuation_paths", tuple(self.continuation_paths)
        )
        object.__setattr__(
            self,
            "access_discrimination",
            AccessDiscrimination(self.access_discrimination),
        )
        object.__setattr__(
            self, "evidence_receipt_ids", tuple(self.evidence_receipt_ids)
        )
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "ancestry", tuple(self.ancestry))
        object.__setattr__(
            self, "genealogy_fragment_ids", tuple(self.genealogy_fragment_ids)
        )
        object.__setattr__(
            self,
            "provenance_fragment_ids",
            tuple(self.provenance_fragment_ids),
        )
        object.__setattr__(
            self, "ancestry_fragment_ids", tuple(self.ancestry_fragment_ids)
        )
        object.__setattr__(
            self,
            "classification_fragment_ids",
            tuple(self.classification_fragment_ids),
        )


@dataclass(frozen=True, slots=True)
class ExplanatoryPrimitive:
    concept: str
    basis: PrimitiveBasis
    receipt_ids: tuple[str, ...] = ()
    used_as_explanation: bool = True
    concept_fragment_id: str = ""
    basis_fragment_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "basis", PrimitiveBasis(self.basis))
        object.__setattr__(self, "receipt_ids", tuple(self.receipt_ids))


@dataclass(frozen=True, slots=True)
class FrozenPlan:
    solution: ConceptualSolution
    freeze_receipt: ExperimentalReceipt
    plan_fragment_id: str = ""
    freeze_fragment_id: str = ""


@dataclass(frozen=True, slots=True)
class ExperimentalProposal:
    fragments: tuple[Fragment, ...]
    continuity: ContinuityEvidence
    conceptual_solution: ConceptualSolution | None
    frozen_plan: FrozenPlan | None
    exact_path: tuple[str, ...]
    categorical_foundation: CategoricalFoundation | None = None
    claims: tuple[FragmentClaim, ...] = ()
    unrepresented_terms: tuple[object, ...] = ()
    primitives: tuple[ExplanatoryPrimitive, ...] = ()
    receipts: tuple[ExperimentalReceipt, ...] = ()
    output: Any = None
    surface_bindings: tuple[FragmentClaim, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "fragments", tuple(self.fragments))
        object.__setattr__(self, "exact_path", tuple(self.exact_path))
        object.__setattr__(self, "claims", tuple(self.claims))
        object.__setattr__(
            self, "unrepresented_terms", tuple(self.unrepresented_terms)
        )
        object.__setattr__(self, "primitives", tuple(self.primitives))
        object.__setattr__(self, "receipts", tuple(self.receipts))
        object.__setattr__(
            self, "surface_bindings", tuple(self.surface_bindings)
        )


@dataclass(frozen=True, slots=True)
class ExperimentalResult:
    decision: Decision
    stage: Stage
    classification: ContinuityClass | None
    output: Any
    reason: str
    receipts: tuple[ExperimentalReceipt, ...]
    runtime_id: str
    runtime_version: str
    authority_hash: str


@dataclass(frozen=True, slots=True)
class FragmentOutput:
    """Output envelope whose semantic fields are all fragment references."""

    output_fragment_id: str
    decision_fragment_id: str
    stage_fragment_id: str
    reason_fragment_id: str
    classification_fragment_id: str
    receipt_fragment_ids: tuple[str, ...] = ()