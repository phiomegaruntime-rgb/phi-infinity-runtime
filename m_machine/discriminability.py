"""Basis-local access discriminability with no cross-basis aggregation."""

from dataclasses import dataclass
from typing import Any, Literal

from .access_integrity import (
    AccessPackage,
    AccessRecord,
    RelationWitness,
    qualify_relation_witness,
)
from .receipts import DerivationReceipt


AMENDMENT_04_SOURCE = (
    "docs/"
    "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_04_BASIS_LOCAL_"
    "ACCESS_DISCRIMINABILITY.md"
)
ACCESS_DISCRIMINABILITY_RECEIPT_STATUS = "ACCESS_DISCRIMINABILITY"

BasisOriginStatus = Literal[
    "SUPPLIED_AS_ACCESS_BASIS",
    "DERIVED_AFTER_ACCESS",
    "BASIS_ORIGIN_UNRESOLVED",
]

OutcomeRelationStatus = Literal[
    "SEPARATELY_RESOLVED",
    "NOT_SEPARATELY_RESOLVED",
    "OUTCOME_RELATION_UNRESOLVED",
]

BasisLocalResultStatus = Literal[
    "DISCRIMINABLE_UNDER_BASIS",
    "NOT_DISCRIMINATED_UNDER_BASIS",
    "UNRESOLVED",
]


def _as_tuple(values: Any) -> tuple[Any, ...]:
    if values is None:
        return ()
    if isinstance(values, tuple):
        return values
    return tuple(values)


@dataclass(frozen=True, slots=True, eq=False)
class BasisRecord:
    """An opaque basis token scoped by its containing AccessPackage."""

    token: str

    def __post_init__(self) -> None:
        if not isinstance(self.token, str) or not self.token:
            raise ValueError("A basis record requires a non-empty token.")


@dataclass(frozen=True, slots=True)
class BasisOrigin:
    basis: BasisRecord
    status: BasisOriginStatus

    def __post_init__(self) -> None:
        if self.status not in {
            "SUPPLIED_AS_ACCESS_BASIS",
            "DERIVED_AFTER_ACCESS",
            "BASIS_ORIGIN_UNRESOLVED",
        }:
            raise ValueError(f"Unsupported basis-origin status: {self.status}")


@dataclass(frozen=True, slots=True, eq=False)
class OutcomeRecord:
    """An opaque basis-local outcome record."""

    token: str
    raw_value: Any = None

    def __post_init__(self) -> None:
        if not isinstance(self.token, str) or not self.token:
            raise ValueError("An outcome record requires a non-empty token.")


@dataclass(frozen=True, slots=True, eq=False)
class ResolutionClass:
    """An opaque class reference with no value or semantic interpretation."""

    token: str

    def __post_init__(self) -> None:
        if not isinstance(self.token, str) or not self.token:
            raise ValueError("A resolution class requires a non-empty token.")


@dataclass(frozen=True, slots=True)
class OutcomeBasisBinding:
    """Exact manifestation-to-outcome association under one basis."""

    basis: BasisRecord
    manifestation: AccessRecord
    outcome: OutcomeRecord


@dataclass(frozen=True, slots=True)
class OutcomeClassMap:
    """Supplied exact outcome-to-class references for one basis."""

    basis: BasisRecord
    entries: tuple[tuple[OutcomeRecord, ResolutionClass], ...]

    def __post_init__(self) -> None:
        entries = []
        for pair in _as_tuple(self.entries):
            if len(pair) != 2:
                raise ValueError("A class-map entry requires outcome and class.")
            outcome, resolution_class = pair
            if not isinstance(outcome, OutcomeRecord):
                raise TypeError("Class-map outcomes must be OutcomeRecord objects.")
            if not isinstance(resolution_class, ResolutionClass):
                raise TypeError("Class-map values must be ResolutionClass objects.")
            entries.append((outcome, resolution_class))
        object.__setattr__(self, "entries", tuple(entries))

    def resolve(self, outcome: OutcomeRecord) -> tuple[ResolutionClass, ...]:
        return tuple(
            resolution_class
            for candidate, resolution_class in self.entries
            if candidate is outcome
        )


@dataclass(frozen=True, slots=True)
class DirectOutcomeRelation:
    """A supplied pair relation, independent of any class map."""

    basis: BasisRecord
    first: OutcomeRecord
    second: OutcomeRecord
    status: OutcomeRelationStatus

    def __post_init__(self) -> None:
        if self.status not in {
            "SEPARATELY_RESOLVED",
            "NOT_SEPARATELY_RESOLVED",
            "OUTCOME_RELATION_UNRESOLVED",
        }:
            raise ValueError(f"Unsupported outcome-relation status: {self.status}")


@dataclass(frozen=True, slots=True)
class BasisAccess:
    """All supplied basis-local access structure for one AccessPackage."""

    bases: tuple[BasisRecord, ...]
    origins: tuple[BasisOrigin, ...] = ()
    outcomes: tuple[OutcomeRecord, ...] = ()
    bindings: tuple[OutcomeBasisBinding, ...] = ()
    class_maps: tuple[OutcomeClassMap, ...] = ()
    direct_relations: tuple[DirectOutcomeRelation, ...] = ()

    def __post_init__(self) -> None:
        bases = _as_tuple(self.bases)
        if any(not isinstance(item, BasisRecord) for item in bases):
            raise TypeError("Bases must be BasisRecord objects.")
        object.__setattr__(self, "bases", bases)
        for name, expected in (
            ("origins", BasisOrigin),
            ("outcomes", OutcomeRecord),
            ("bindings", OutcomeBasisBinding),
            ("class_maps", OutcomeClassMap),
            ("direct_relations", DirectOutcomeRelation),
        ):
            values = _as_tuple(getattr(self, name))
            if any(not isinstance(item, expected) for item in values):
                raise TypeError(f"{name} contains an invalid access record.")
            object.__setattr__(self, name, values)


@dataclass(frozen=True, slots=True)
class BasisLocalDiscriminabilityResult:
    status: BasisLocalResultStatus
    basis: BasisRecord
    relation: OutcomeRelationStatus
    receipt: DerivationReceipt


@dataclass(frozen=True, slots=True)
class BasisLocalDiscriminabilitySet:
    """Independent basis-local results; deliberately not a global result."""

    connected_access: Any
    results: tuple[BasisLocalDiscriminabilityResult, ...]


def _result(
    *,
    status: BasisLocalResultStatus,
    basis: BasisRecord,
    relation: OutcomeRelationStatus,
    input_receipt_ids: tuple[str, ...],
    performed: str,
    consequence: str,
    evidence: tuple[str, ...],
) -> BasisLocalDiscriminabilityResult:
    receipt = DerivationReceipt.create(
        operation_name="access_discriminability.basis_local",
        authoritative_source_file=AMENDMENT_04_SOURCE,
        authoritative_clause=(
            "Amendment 04 basis-local access discriminability"
        ),
        input_receipt_ids=input_receipt_ids,
        accessible_evidence=evidence,
        operation_performed=performed,
        resulting_difference_or_consequence=consequence,
        status=ACCESS_DISCRIMINABILITY_RECEIPT_STATUS,
        implementation_source="m_machine/discriminability.py",
        clause_id="access04.basis_local_discriminability",
    )
    return BasisLocalDiscriminabilityResult(
        status=status,
        basis=basis,
        relation=relation,
        receipt=receipt,
    )


def _unresolved(
    *,
    basis: BasisRecord,
    input_receipt_ids: tuple[str, ...] = (),
    performed: str,
    evidence: tuple[str, ...],
) -> BasisLocalDiscriminabilityResult:
    return _result(
        status="UNRESOLVED",
        basis=basis,
        relation="OUTCOME_RELATION_UNRESOLVED",
        input_receipt_ids=input_receipt_ids,
        performed=performed,
        consequence=(
            "No basis-local discrimination was asserted and no global "
            "cross-basis result was created."
        ),
        evidence=evidence,
    )


def evaluate_basis_local(
    package: AccessPackage,
    witness: RelationWitness,
    first: AccessRecord,
    second: AccessRecord,
    basis: BasisRecord,
) -> BasisLocalDiscriminabilityResult:
    """Evaluate only the supplied basis-local outcome relation."""

    if not isinstance(package, AccessPackage):
        raise TypeError("evaluate_basis_local() requires AccessPackage")
    if not isinstance(basis, BasisRecord):
        raise TypeError("evaluate_basis_local() requires BasisRecord")

    connected = qualify_relation_witness(package, witness)
    receipt_ids = (connected.receipt.receipt_id,)
    if connected.status != "CONNECTED":
        return _unresolved(
            basis=basis,
            input_receipt_ids=receipt_ids,
            performed="Required an already-qualified direct access relation.",
            evidence=("Connects_a was not CONNECTED",),
        )

    access = package.basis_access
    if not isinstance(access, BasisAccess):
        return _unresolved(
            basis=basis,
            input_receipt_ids=receipt_ids,
            performed="Looked for supplied basis-local access structure.",
            evidence=("no BasisAccess supplied in the access package",),
        )
    if not any(candidate is basis for candidate in access.bases):
        return _unresolved(
            basis=basis,
            input_receipt_ids=receipt_ids,
            performed="Checked exact basis membership in the access package.",
            evidence=("basis was not supplied under this access package",),
        )

    origin_matches = tuple(
        item.status for item in access.origins if item.basis is basis
    )
    if len(origin_matches) != 1 or origin_matches[0] != "SUPPLIED_AS_ACCESS_BASIS":
        return _unresolved(
            basis=basis,
            input_receipt_ids=receipt_ids,
            performed="Checked supplied basis origin without inferring it.",
            evidence=("basis origin was missing, ambiguous, or post-hoc",),
        )

    first_matches = tuple(
        item.outcome
        for item in access.bindings
        if item.basis is basis and item.manifestation is first
    )
    second_matches = tuple(
        item.outcome
        for item in access.bindings
        if item.basis is basis and item.manifestation is second
    )
    if len(first_matches) != 1 or len(second_matches) != 1:
        return _unresolved(
            basis=basis,
            input_receipt_ids=receipt_ids,
            performed="Resolved exact basis-local outcome bindings.",
            evidence=("one or both outcome bindings were absent or ambiguous",),
        )
    first_outcome, second_outcome = first_matches[0], second_matches[0]
    if not all(
        any(candidate is outcome for candidate in access.outcomes)
        for outcome in (first_outcome, second_outcome)
    ):
        return _unresolved(
            basis=basis,
            input_receipt_ids=receipt_ids,
            performed="Checked outcome-record membership in supplied basis access.",
            evidence=("a bound outcome was not supplied as an outcome record",),
        )

    matching_maps = tuple(item for item in access.class_maps if item.basis is basis)
    class_relation: OutcomeRelationStatus | None = None
    if matching_maps:
        if len(matching_maps) != 1:
            return _unresolved(
                basis=basis,
                input_receipt_ids=receipt_ids,
                performed="Checked that the supplied class map is unambiguous.",
                evidence=("multiple class maps were supplied for one basis",),
            )
        first_classes = matching_maps[0].resolve(first_outcome)
        second_classes = matching_maps[0].resolve(second_outcome)
        if len(first_classes) == 1 and len(second_classes) == 1:
            class_relation = (
                "NOT_SEPARATELY_RESOLVED"
                if first_classes[0] is second_classes[0]
                else "SEPARATELY_RESOLVED"
            )
        elif any((len(first_classes), len(second_classes))):
            return _unresolved(
                basis=basis,
                input_receipt_ids=receipt_ids,
                performed="Checked exact class membership for both outcomes.",
                evidence=("class membership was incomplete or ambiguous",),
            )

    matching_pairs = tuple(
        item
        for item in access.direct_relations
        if (
            item.basis is basis
            and item.first is first_outcome
            and item.second is second_outcome
        )
    )
    direct_relation: OutcomeRelationStatus | None = None
    if matching_pairs:
        if len(matching_pairs) != 1:
            return _unresolved(
                basis=basis,
                input_receipt_ids=receipt_ids,
                performed="Checked that the supplied pair relation is unambiguous.",
                evidence=("multiple direct pair relations were supplied",),
            )
        direct_relation = matching_pairs[0].status
        if direct_relation == "OUTCOME_RELATION_UNRESOLVED":
            return _unresolved(
                basis=basis,
                input_receipt_ids=receipt_ids,
                performed="Preserved the supplied unresolved pair relation.",
                evidence=("direct outcome relation was unresolved",),
            )

    if class_relation is None and direct_relation is None:
        return _unresolved(
            basis=basis,
            input_receipt_ids=receipt_ids,
            performed="Looked for a supplied class or direct pair relation.",
            evidence=("no qualifying outcome relation was supplied",),
        )
    if (
        class_relation is not None
        and direct_relation is not None
        and class_relation != direct_relation
    ):
        return _unresolved(
            basis=basis,
            input_receipt_ids=receipt_ids,
            performed="Compared supplied forms only for exact conflict detection.",
            evidence=("class map and direct pair relation conflict",),
        )

    relation = class_relation or direct_relation
    assert relation is not None
    result_status: BasisLocalResultStatus = (
        "DISCRIMINABLE_UNDER_BASIS"
        if relation == "SEPARATELY_RESOLVED"
        else "NOT_DISCRIMINATED_UNDER_BASIS"
    )
    return _result(
        status=result_status,
        basis=basis,
        relation=relation,
        input_receipt_ids=receipt_ids,
        performed=(
            "Preserved supplied basis-local outcome relation through exact "
            "access references."
        ),
        consequence=(
            "No magnitude, direction, dependency, causation, relevance, "
            "ontology, or cross-basis result was created."
        ),
        evidence=(
            "supplied basis origin",
            "exact outcome bindings",
            "supplied class or pair relation",
        ),
    )


def discriminable_under_basis(
    package: AccessPackage,
    witness: RelationWitness,
    first: AccessRecord,
    second: AccessRecord,
    basis: BasisRecord,
) -> BasisLocalDiscriminabilityResult:
    return evaluate_basis_local(package, witness, first, second, basis)