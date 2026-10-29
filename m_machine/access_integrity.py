"""Non-generative access-package and relation-witness integrity."""

from dataclasses import dataclass
from typing import Any, Literal

from .receipts import DerivationReceipt


AMENDMENT_03_SOURCE = (
    "docs/"
    "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_03_ACCESS_REPRESENTATION_"
    "AND_RELATIONAL_INTEGRITY.md"
)
ACCESS_INTEGRITY_RECEIPT_STATUS = "ACCESS_INTEGRITY"

OriginStatus = Literal[
    "SUPPLIED_AS_ACCESS_STRUCTURE",
    "DERIVED_AFTER_ACCESS",
    "ORIGIN_UNRESOLVED",
]

AccessIntegrityStatus = Literal[
    "VALID",
    "ACCESSIBLE",
    "NOT_ACCESSIBLE",
    "BOUND",
    "NOT_BOUND",
    "CONNECTED",
    "NOT_CONNECTED",
    "UNRESOLVED",
    "ORIGIN_UNRESOLVED",
    "SUPPLIED_AS_ACCESS_STRUCTURE",
    "DERIVED_AFTER_ACCESS",
]


def _tuple(values: Any) -> tuple[Any, ...]:
    if values is None:
        return ()
    if isinstance(values, tuple):
        return values
    return tuple(values)


@dataclass(frozen=True, slots=True)
class AccessLocalHandle:
    """An opaque token whose scope is one access package."""

    token: str

    def __post_init__(self) -> None:
        if not isinstance(self.token, str) or not self.token:
            raise ValueError("An access-local handle requires a non-empty token.")


@dataclass(frozen=True, slots=True, eq=False)
class AccessRecord:
    """A supplied manifestation record with package-local identity."""

    value: Any


@dataclass(frozen=True, slots=True)
class LocalReferentMap:
    """Immutable exact handle-to-record mappings.

    Duplicate handle entries are retained so ambiguous input resolves to
    UNRESOLVED rather than being silently collapsed by a dictionary.
    """

    entries: tuple[tuple[AccessLocalHandle, AccessRecord], ...] = ()

    def __post_init__(self) -> None:
        entries = []
        raw_entries = self.entries.items() if isinstance(self.entries, dict) else self.entries
        for pair in raw_entries:
            if len(pair) != 2:
                raise ValueError("A referent-map entry requires handle and record.")
            handle, record = pair
            if isinstance(handle, str):
                handle = AccessLocalHandle(handle)
            if not isinstance(handle, AccessLocalHandle):
                raise TypeError("Referent-map keys must be access-local handles.")
            if not isinstance(record, AccessRecord):
                raise TypeError("Referent-map values must be AccessRecord objects.")
            entries.append((handle, record))
        object.__setattr__(self, "entries", tuple(entries))

    def resolve(self, handle: AccessLocalHandle) -> tuple[AccessRecord, ...]:
        if not isinstance(handle, AccessLocalHandle):
            return ()
        return tuple(
            record
            for candidate, record in self.entries
            if candidate == handle
        )


@dataclass(frozen=True, slots=True)
class RelationWitness:
    """A supplied witness carrying only two access-local endpoints."""

    witness_id: str
    endpoint_1: AccessLocalHandle
    endpoint_2: AccessLocalHandle

    def __post_init__(self) -> None:
        if not isinstance(self.witness_id, str) or not self.witness_id:
            raise ValueError("A relation witness requires a local witness ID.")
        for endpoint in (self.endpoint_1, self.endpoint_2):
            if not isinstance(endpoint, AccessLocalHandle):
                raise TypeError("Relation-witness endpoints must be local handles.")


@dataclass(frozen=True, slots=True)
class OriginProvenance:
    """Origin metadata, without truth or trust semantics."""

    witness_id: str
    status: OriginStatus

    def __post_init__(self) -> None:
        if self.status not in {
            "SUPPLIED_AS_ACCESS_STRUCTURE",
            "DERIVED_AFTER_ACCESS",
            "ORIGIN_UNRESOLVED",
        }:
            raise ValueError(f"Unsupported origin status: {self.status}")


@dataclass(frozen=True, slots=True)
class AccessPackage:
    """One explicitly scoped, immutable access envelope."""

    access_instance: str
    manifestations: tuple[AccessRecord, ...]
    local_referent_map: LocalReferentMap
    supplied_witnesses: tuple[RelationWitness, ...] = ()
    provenance: tuple[OriginProvenance, ...] = ()
    witness_referent_map: tuple[
        tuple[AccessLocalHandle, RelationWitness], ...
    ] = ()
    basis_access: Any = None

    def __post_init__(self) -> None:
        if not isinstance(self.access_instance, str) or not self.access_instance:
            raise ValueError("An access package requires a scoped access instance.")
        manifestations = _tuple(self.manifestations)
        if any(not isinstance(item, AccessRecord) for item in manifestations):
            raise TypeError("Manifestations must be AccessRecord objects.")
        object.__setattr__(self, "manifestations", manifestations)
        if not isinstance(self.local_referent_map, LocalReferentMap):
            object.__setattr__(
                self,
                "local_referent_map",
                LocalReferentMap(self.local_referent_map),
            )
        witnesses = _tuple(self.supplied_witnesses)
        if any(not isinstance(item, RelationWitness) for item in witnesses):
            raise TypeError("Supplied witnesses must be RelationWitness objects.")
        object.__setattr__(self, "supplied_witnesses", witnesses)
        provenance = _tuple(self.provenance)
        if any(not isinstance(item, OriginProvenance) for item in provenance):
            raise TypeError("Provenance must be OriginProvenance objects.")
        object.__setattr__(self, "provenance", provenance)
        references = []
        for pair in _tuple(self.witness_referent_map):
            if len(pair) != 2:
                raise ValueError("A witness reference requires handle and witness.")
            handle, witness = pair
            if isinstance(handle, str):
                handle = AccessLocalHandle(handle)
            if not isinstance(handle, AccessLocalHandle):
                raise TypeError("Witness-reference keys must be local handles.")
            if not isinstance(witness, RelationWitness):
                raise TypeError("Witness-reference values must be RelationWitness objects.")
            references.append((handle, witness))
        object.__setattr__(self, "witness_referent_map", tuple(references))


@dataclass(frozen=True, slots=True)
class RelationQualifiedAccess:
    """Access structure after direct relation-witness qualification."""

    package: AccessPackage
    connected_witnesses: tuple[RelationWitness, ...] = ()
    unresolved_witnesses: tuple[RelationWitness, ...] = ()
    non_direct_witnesses: tuple[RelationWitness, ...] = ()


@dataclass(frozen=True, slots=True)
class AccessIntegrityResult:
    """A non-generative result with typed Amendment 03 provenance."""

    status: AccessIntegrityStatus
    value: Any
    receipt: DerivationReceipt


def _result(
    *,
    operation_name: str,
    status: AccessIntegrityStatus,
    value: Any,
    performed: str,
    consequence: str,
    clause_id: str,
    evidence: tuple[str, ...],
) -> AccessIntegrityResult:
    receipt = DerivationReceipt.create(
        operation_name=operation_name,
        authoritative_source_file=AMENDMENT_03_SOURCE,
        authoritative_clause=(
            "Amendment 03 access representation and relational integrity"
        ),
        accessible_evidence=evidence,
        operation_performed=performed,
        resulting_difference_or_consequence=consequence,
        status=ACCESS_INTEGRITY_RECEIPT_STATUS,
        implementation_source="m_machine/access_integrity.py",
        clause_id=clause_id,
    )
    return AccessIntegrityResult(
        status=status,
        value=value,
        receipt=receipt,
    )


def verify_access_package(package: AccessPackage) -> AccessIntegrityResult:
    if not isinstance(package, AccessPackage):
        raise TypeError("verify_access_package() requires AccessPackage")
    return _result(
        operation_name="access_integrity.verify_package",
        status="VALID",
        value=package,
        performed="Verified the immutable access-package structure.",
        consequence=(
            "No membership, relation, origin, or mechanical inference was added."
        ),
        clause_id="access.package",
        evidence=(
            "scoped access instance supplied",
            "manifestations and local referent map supplied",
        ),
    )


def de_name_access_package(package: AccessPackage) -> AccessIntegrityResult:
    if not isinstance(package, AccessPackage):
        raise TypeError("de_name_access_package() requires AccessPackage")
    return _result(
        operation_name="access_integrity.de_name",
        status="VALID",
        value=package,
        performed="Kept human semantic material outside access structure.",
        consequence="Access-local referents were not changed.",
        clause_id="access.denaming",
        evidence=("access package preserved", "semantic material quarantined"),
    )


def accessible_under_a(
    package: AccessPackage,
    witness: RelationWitness,
) -> AccessIntegrityResult:
    if not isinstance(package, AccessPackage) or not isinstance(
        witness, RelationWitness
    ):
        raise TypeError("accessible_under_a() requires package and witness")
    direct = any(candidate is witness for candidate in package.supplied_witnesses)
    referenced = any(
        candidate is witness
        for _, candidate in package.witness_referent_map
    )
    status: AccessIntegrityStatus = (
        "ACCESSIBLE" if direct or referenced else "NOT_ACCESSIBLE"
    )
    return _result(
        operation_name="access_integrity.membership",
        status=status,
        value=direct or referenced,
        performed="Checked exact package membership only.",
        consequence=(
            "No outside record discovery or relation inference was performed."
        ),
        clause_id="access.membership",
        evidence=(
            "direct package membership checked",
            "local witness reference membership checked",
        ),
    )


def binds_a(
    package: AccessPackage,
    reference: AccessLocalHandle,
    record: AccessRecord,
) -> AccessIntegrityResult:
    if not isinstance(package, AccessPackage):
        raise TypeError("binds_a() requires AccessPackage")
    if not isinstance(reference, AccessLocalHandle) or not isinstance(
        record, AccessRecord
    ):
        return _result(
            operation_name="access_integrity.binding",
            status="UNRESOLVED",
            value=False,
            performed="Rejected a non-local or non-record binding request.",
            consequence="No substitute endpoint was selected.",
            clause_id="access.binding",
            evidence=("binding input was not an exact local reference",),
        )
    matches = package.local_referent_map.resolve(reference)
    supplied_record = any(candidate is record for candidate in package.manifestations)
    if len(matches) != 1 or not supplied_record:
        status: AccessIntegrityStatus = "UNRESOLVED"
        value = False
    else:
        status = "BOUND" if matches[0] is record else "NOT_BOUND"
        value = status == "BOUND"
    return _result(
        operation_name="access_integrity.binding",
        status=status,
        value=value,
        performed="Resolved the handle through exact local map identity only.",
        consequence=(
            "No semantic matching, search, approximation, or ontological identity "
            "was inferred."
        ),
        clause_id="access.binding",
        evidence=("exact local referent map lookup",),
    )


def origin_a(
    package: AccessPackage,
    witness: RelationWitness,
) -> AccessIntegrityResult:
    if not isinstance(package, AccessPackage) or not isinstance(
        witness, RelationWitness
    ):
        raise TypeError("origin_a() requires package and witness")
    matches = tuple(
        item.status
        for item in package.provenance
        if item.witness_id == witness.witness_id
    )
    if len(matches) != 1:
        status: AccessIntegrityStatus = "ORIGIN_UNRESOLVED"
        value: OriginStatus = "ORIGIN_UNRESOLVED"
    else:
        value = matches[0]
        status = value
    return _result(
        operation_name="access_integrity.origin",
        status=status,
        value=value,
        performed="Preserved the supplied origin status without certifying it.",
        consequence="Origin metadata was not interpreted as physical truth.",
        clause_id="access.origin",
        evidence=("supplied origin provenance inspected",),
    )


def connects_a(
    package: AccessPackage,
    witness: RelationWitness,
    first: AccessRecord,
    second: AccessRecord,
) -> AccessIntegrityResult:
    membership = accessible_under_a(package, witness)
    first_binding = binds_a(package, witness.endpoint_1, first)
    second_binding = binds_a(package, witness.endpoint_2, second)
    origin = origin_a(package, witness)
    if membership.status != "ACCESSIBLE":
        status: AccessIntegrityStatus = "NOT_CONNECTED"
        value = False
    elif (
        first_binding.status == "UNRESOLVED"
        or second_binding.status == "UNRESOLVED"
        or origin.status == "ORIGIN_UNRESOLVED"
    ):
        status = "UNRESOLVED"
        value = False
    elif (
        first_binding.status != "BOUND"
        or second_binding.status != "BOUND"
        or origin.value != "SUPPLIED_AS_ACCESS_STRUCTURE"
    ):
        status = "NOT_CONNECTED"
        value = False
    else:
        status = "CONNECTED"
        value = True
    return _result(
        operation_name="access_integrity.connects",
        status=status,
        value=value,
        performed=(
            "Composed exact package membership, local binding, and origin "
            "provenance checks."
        ),
        consequence=(
            "Access-level relation qualification only; no dependency, exchange, "
            "causation, relevance, or continuation was generated."
        ),
        clause_id="access.relation_witness",
        evidence=(
            "exact package membership",
            "exact local endpoint binding",
            "origin status preserved",
        ),
    )


def qualify_relation_witness(
    package: AccessPackage,
    witness: RelationWitness,
) -> AccessIntegrityResult:
    """Resolve both local endpoints and compose the Connects predicate."""

    if not isinstance(package, AccessPackage) or not isinstance(
        witness, RelationWitness
    ):
        raise TypeError(
            "qualify_relation_witness() requires package and witness"
        )
    first_matches = package.local_referent_map.resolve(witness.endpoint_1)
    second_matches = package.local_referent_map.resolve(witness.endpoint_2)
    if len(first_matches) != 1 or len(second_matches) != 1:
        return _result(
            operation_name="access_integrity.connects",
            status="UNRESOLVED",
            value=False,
            performed="Attempted exact local endpoint resolution.",
            consequence=(
                "At least one endpoint was absent or ambiguous; no substitute "
                "record or relation was created."
            ),
            clause_id="access.relation_witness",
            evidence=("exact local endpoint resolution was incomplete",),
        )
    return connects_a(
        package,
        witness,
        first_matches[0],
        second_matches[0],
    )


def AccessibleUnder_a(
    package: AccessPackage,
    witness: RelationWitness,
) -> AccessIntegrityResult:
    return accessible_under_a(package, witness)


def Binds_a(
    package: AccessPackage,
    reference: AccessLocalHandle,
    record: AccessRecord,
) -> AccessIntegrityResult:
    return binds_a(package, reference, record)


def Origin_a(
    package: AccessPackage,
    witness: RelationWitness,
) -> AccessIntegrityResult:
    return origin_a(package, witness)


def Connects_a(
    package: AccessPackage,
    witness: RelationWitness,
    first: AccessRecord,
    second: AccessRecord,
) -> AccessIntegrityResult:
    return connects_a(package, witness, first, second)