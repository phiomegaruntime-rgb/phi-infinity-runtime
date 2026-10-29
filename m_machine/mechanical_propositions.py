"""Non-generative, typed mechanical proposition semantics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


AMENDMENT_06_SOURCE = (
    "docs/"
    "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_06_MECHANICAL_PROPOSITION_"
    "SEMANTICS.md"
)
AMENDMENT_07_SOURCE = (
    "docs/"
    "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_07_TRUSTED_MECHANICAL_"
    "GROUNDING_ACQUISITION_SEMANTICS.md"
)
AMENDMENT_08_SOURCE = (
    "docs/"
    "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_08_PAIRWISE_TRUSTED_"
    "GROUNDING_DISTINCT_INSTANCE_SEMANTICS.md"
)


class PropositionType(str, Enum):
    REAL_DIFFERENCE_EXISTS = "REAL_DIFFERENCE_EXISTS"
    REAL_CONSEQUENCE_EXISTS = "REAL_CONSEQUENCE_EXISTS"
    MECHANICAL_EXISTENCE_PROVED = "MECHANICAL_EXISTENCE_PROVED"
    MECHANICAL_WITNESS_CONSTRUCTED = "MECHANICAL_WITNESS_CONSTRUCTED"
    REAL_ACQUISITION_TRACE_EXISTS = "REAL_ACQUISITION_TRACE_EXISTS"
    DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES = (
        "DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES"
    )


class ConstructorPolicy(str, Enum):
    NO_CONSTRUCTOR_CURRENTLY_AUTHORIZED = (
        "NO_CONSTRUCTOR_CURRENTLY_AUTHORIZED"
    )
    MECHANICAL_RULE_ONLY = "MECHANICAL_RULE_ONLY"
    FALSIFICATION_RULE_ONLY = "FALSIFICATION_RULE_ONLY"
    NATIVE_REPRESENTED_SCOPE_ONLY = "NATIVE_REPRESENTED_SCOPE_ONLY"
    TRUSTED_GROUNDING_ONLY = "TRUSTED_GROUNDING_ONLY"


class PropositionOrigin(str, Enum):
    ACCESS_REPRESENTATION = "ACCESS_REPRESENTATION"
    GROUNDED_EXTERNAL = "GROUNDED_EXTERNAL"
    DERIVED_M = "DERIVED_M"
    NATIVE_REPRESENTED = "NATIVE_REPRESENTED"


class PropositionStatus(str, Enum):
    UNINHABITED = "UNINHABITED"
    ASSERTED = "ASSERTED"
    MECHANICAL_EXISTENCE_PROVED = "MECHANICAL_EXISTENCE_PROVED"


class WitnessStatus(str, Enum):
    WITNESS_FREE = "WITNESS_FREE"
    WITNESS_CONSTRUCTED = "WITNESS_CONSTRUCTED"


def _tuple(values: Iterable[Any] | None) -> tuple[Any, ...]:
    if values is None:
        return ()
    return values if isinstance(values, tuple) else tuple(values)


def semantic_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class PropositionTypeSpec:
    type_id: PropositionType
    semantic_statement: str
    scope_schema: tuple[str, ...]
    existential: bool
    witness_bearing: bool
    constructor_policy: ConstructorPolicy
    authority_source: str
    authority_range: tuple[int, int]
    authority_range_hash: str
    semantic_specification_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "type_id", PropositionType(self.type_id))
        object.__setattr__(
            self,
            "constructor_policy",
            ConstructorPolicy(self.constructor_policy),
        )
        object.__setattr__(
            self, "scope_schema", _tuple(self.scope_schema)
        )
        if not self.semantic_statement:
            raise ValueError("Proposition semantics cannot be empty.")
        if semantic_hash(self.semantic_statement) != (
            self.semantic_specification_hash
        ):
            raise ValueError("Proposition semantic hash mismatch.")
        start, end = self.authority_range
        if start < 1 or end < start:
            raise ValueError("Invalid proposition authority range.")
        if len(self.authority_range_hash) != 64:
            raise ValueError("Proposition authority hash must be SHA256.")
        if self.witness_bearing and self.existential:
            raise ValueError(
                "Existential propositions in this layer are witness-free."
            )


@dataclass(frozen=True, slots=True)
class MechanicalProposition:
    """An authorized proposition record; direct caller construction is blocked."""

    proposition_id: str
    predicate_type: PropositionType
    mechanical_scope: tuple[tuple[str, str], ...]
    subject_receipt_ids: tuple[str, ...]
    proposition_status: PropositionStatus
    witness_status: WitnessStatus
    parent_receipt_ids: tuple[str, ...]
    proof_genealogies: tuple[Any, ...]
    origin: PropositionOrigin = PropositionOrigin.ACCESS_REPRESENTATION
    grounding_ancestry: Any = None
    historically_valid: bool = True
    currently_applicable: bool = True

    def __post_init__(self) -> None:
        raise PermissionError(
            "Mechanical propositions require an authorized constructor path."
        )

    @classmethod
    def _from_authorized_mechanical_rule(
        cls,
        *,
        proposition_id: str,
        predicate_type: PropositionType,
        mechanical_scope: tuple[tuple[str, str], ...],
        subject_receipt_ids: tuple[str, ...],
        proposition_status: PropositionStatus,
        witness_status: WitnessStatus,
        parent_receipt_ids: tuple[str, ...],
        proof_genealogies: tuple[Any, ...],
        authorization_token: object,
    ) -> "MechanicalProposition":
        if authorization_token is not _MECHANICAL_RULE_CONSTRUCTOR_TOKEN:
            raise PermissionError(
                "Mechanical-rule constructor authorization is invalid."
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "proposition_id", proposition_id)
        object.__setattr__(
            instance, "predicate_type", PropositionType(predicate_type)
        )
        object.__setattr__(
            instance, "mechanical_scope", _tuple(mechanical_scope)
        )
        object.__setattr__(
            instance, "subject_receipt_ids", _tuple(subject_receipt_ids)
        )
        object.__setattr__(
            instance,
            "proposition_status",
            PropositionStatus(proposition_status),
        )
        object.__setattr__(
            instance, "witness_status", WitnessStatus(witness_status)
        )
        object.__setattr__(
            instance, "parent_receipt_ids", _tuple(parent_receipt_ids)
        )
        object.__setattr__(
            instance, "proof_genealogies", _tuple(proof_genealogies)
        )
        object.__setattr__(instance, "origin", PropositionOrigin.DERIVED_M)
        object.__setattr__(instance, "grounding_ancestry", None)
        object.__setattr__(instance, "historically_valid", True)
        object.__setattr__(instance, "currently_applicable", True)
        return instance

    @classmethod
    def _from_authorized_trusted_grounding(
        cls,
        *,
        proposition_id: str,
        predicate_type: PropositionType,
        mechanical_scope: tuple[tuple[str, str], ...],
        subject_receipt_ids: tuple[str, ...],
        proposition_status: PropositionStatus,
        witness_status: WitnessStatus,
        grounding_ancestry: Any,
        historically_valid: bool,
        currently_applicable: bool,
        authorization_token: object,
    ) -> "MechanicalProposition":
        if authorization_token is not _TRUSTED_GROUNDING_CONSTRUCTOR_TOKEN:
            raise PermissionError(
                "Trusted-grounding constructor authorization is invalid."
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "proposition_id", proposition_id)
        object.__setattr__(
            instance, "predicate_type", PropositionType(predicate_type)
        )
        object.__setattr__(
            instance, "mechanical_scope", _tuple(mechanical_scope)
        )
        object.__setattr__(
            instance, "subject_receipt_ids", _tuple(subject_receipt_ids)
        )
        object.__setattr__(
            instance,
            "proposition_status",
            PropositionStatus(proposition_status),
        )
        object.__setattr__(
            instance, "witness_status", WitnessStatus(witness_status)
        )
        object.__setattr__(instance, "parent_receipt_ids", ())
        object.__setattr__(instance, "proof_genealogies", ())
        object.__setattr__(
            instance, "origin", PropositionOrigin.GROUNDED_EXTERNAL
        )
        object.__setattr__(instance, "grounding_ancestry", grounding_ancestry)
        object.__setattr__(
            instance, "historically_valid", bool(historically_valid)
        )
        object.__setattr__(
            instance, "currently_applicable", bool(currently_applicable)
        )
        return instance


_MECHANICAL_RULE_CONSTRUCTOR_TOKEN = object()
_TRUSTED_GROUNDING_CONSTRUCTOR_TOKEN = object()


def _construct_from_authorized_mechanical_rule(
    *,
    registry: "FrozenPropositionTypeRegistry",
    predicate_type: PropositionType,
    mechanical_scope: tuple[tuple[str, str], ...],
    subject_receipt_ids: tuple[str, ...],
    proposition_status: PropositionStatus,
    witness_status: WitnessStatus,
    parent_receipt_ids: tuple[str, ...],
    proof_genealogies: tuple[Any, ...],
    authorization_token: object,
) -> MechanicalProposition:
    if authorization_token is not _MECHANICAL_RULE_CONSTRUCTOR_TOKEN:
        raise PermissionError(
            "Mechanical-rule constructor authorization is invalid."
        )
    registry.enforce_constructor_policy(
        predicate_type,
        constructor_kind="MECHANICAL_RULE",
        raw_scope=False,
        authorized_rule=True,
    )


def _construct_from_authorized_trusted_grounding(
    *,
    registry: "FrozenPropositionTypeRegistry",
    predicate_type: PropositionType,
    mechanical_scope: tuple[tuple[str, str], ...],
    subject_receipt_ids: tuple[str, ...],
    proposition_status: PropositionStatus,
    witness_status: WitnessStatus,
    grounding_ancestry: Any,
    historically_valid: bool,
    currently_applicable: bool,
    authorization_token: object,
) -> MechanicalProposition:
    if authorization_token is not _TRUSTED_GROUNDING_CONSTRUCTOR_TOKEN:
        raise PermissionError(
            "Trusted-grounding constructor authorization is invalid."
        )
    registry.enforce_constructor_policy(
        predicate_type,
        constructor_kind="TRUSTED_GROUNDING",
        raw_scope=False,
        trusted_grounding_valid=True,
    )
    normalized_scope = registry.validate_scope(
        predicate_type, mechanical_scope
    )
    proposition_id = registry.proposition_identity(
        predicate_type,
        normalized_scope,
        subject_receipt_ids,
    )
    return MechanicalProposition._from_authorized_trusted_grounding(
        proposition_id=proposition_id,
        predicate_type=predicate_type,
        mechanical_scope=normalized_scope,
        subject_receipt_ids=subject_receipt_ids,
        proposition_status=proposition_status,
        witness_status=witness_status,
        grounding_ancestry=grounding_ancestry,
        historically_valid=historically_valid,
        currently_applicable=currently_applicable,
        authorization_token=_TRUSTED_GROUNDING_CONSTRUCTOR_TOKEN,
    )
    normalized_scope = registry.validate_scope(
        predicate_type, mechanical_scope
    )
    proposition_id = registry.proposition_identity(
        predicate_type,
        normalized_scope,
        subject_receipt_ids,
    )
    return MechanicalProposition._from_authorized_mechanical_rule(
        proposition_id=proposition_id,
        predicate_type=predicate_type,
        mechanical_scope=normalized_scope,
        subject_receipt_ids=subject_receipt_ids,
        proposition_status=proposition_status,
        witness_status=witness_status,
        parent_receipt_ids=parent_receipt_ids,
        proof_genealogies=proof_genealogies,
        authorization_token=_MECHANICAL_RULE_CONSTRUCTOR_TOKEN,
    )


@dataclass(frozen=True, slots=True)
class FrozenPropositionTypeRegistry:
    types: tuple[PropositionTypeSpec, ...]
    repository_root: Path | str = Path(".")

    def __post_init__(self) -> None:
        root = Path(self.repository_root).resolve()
        object.__setattr__(self, "repository_root", root)
        object.__setattr__(self, "types", _tuple(self.types))
        ids = tuple(spec.type_id for spec in self.types)
        if len(ids) != len(set(ids)):
            raise ValueError("Proposition type identities must be unique.")
        for spec in self.types:
            self._verify_authority(spec)

    def _verify_authority(self, spec: PropositionTypeSpec) -> None:
        path = self.repository_root / spec.authority_source
        if not path.is_file():
            raise ValueError(
                f"Proposition authority source is missing: "
                f"{spec.authority_source}"
            )
        start, end = spec.authority_range
        lines = path.read_bytes().splitlines(keepends=True)
        selected = lines[start - 1 : end]
        if len(selected) != end - start + 1:
            raise ValueError("Proposition authority range is incomplete.")
        actual = hashlib.sha256(b"".join(selected)).hexdigest()
        if actual != spec.authority_range_hash:
            raise ValueError("Proposition authority hash mismatch.")

    def get(self, type_id: PropositionType | str) -> PropositionTypeSpec:
        try:
            target = PropositionType(type_id)
        except ValueError as exc:
            raise KeyError(
                f"Unknown mechanical proposition type: {type_id}"
            ) from exc
        for spec in self.types:
            if spec.type_id == target:
                return spec
        raise KeyError(f"Unknown mechanical proposition type: {target}")

    def validate_scope(
        self,
        type_id: PropositionType | str,
        scope: tuple[tuple[str, str], ...],
    ) -> tuple[tuple[str, str], ...]:
        spec = self.get(type_id)
        normalized = _tuple(scope)
        names = tuple(name for name, _ in normalized)
        if len(names) != len(set(names)):
            raise ValueError("Mechanical proposition scope keys must be unique.")
        unknown = set(names) - set(spec.scope_schema)
        if unknown:
            raise ValueError(
                "Mechanical proposition scope contains unauthorized fields: "
                + ", ".join(sorted(unknown))
            )
        return normalized

    def proposition_identity(
        self,
        type_id: PropositionType | str,
        scope: tuple[tuple[str, str], ...],
        subject_receipt_ids: tuple[str, ...] = (),
    ) -> str:
        spec = self.get(type_id)
        normalized_scope = self.validate_scope(type_id, scope)
        canonical = json.dumps(
            {
                "type": spec.type_id.value,
                "semantic_hash": spec.semantic_specification_hash,
                "scope": normalized_scope,
                "subjects": _tuple(subject_receipt_ids),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def enforce_constructor_policy(
        self,
        type_id: PropositionType | str,
        *,
        constructor_kind: str,
        raw_scope: bool,
        authorized_rule: bool = False,
        trusted_grounding_valid: bool = False,
    ) -> None:
        spec = self.get(type_id)
        if constructor_kind == "CALLER":
            raise PermissionError(
                "Caller-supplied mechanical facts are forbidden."
            )
        if (
            spec.constructor_policy
            == ConstructorPolicy.NO_CONSTRUCTOR_CURRENTLY_AUTHORIZED
        ):
            raise PermissionError(
                f"No constructor is authorized for {spec.type_id.value}."
            )
        if spec.constructor_policy == ConstructorPolicy.MECHANICAL_RULE_ONLY:
            if constructor_kind != "MECHANICAL_RULE" or not authorized_rule:
                raise PermissionError(
                    "A registered mechanical rule is required."
                )
        elif (
            spec.constructor_policy
            == ConstructorPolicy.FALSIFICATION_RULE_ONLY
        ):
            if constructor_kind != "FALSIFICATION_RULE" or not authorized_rule:
                raise PermissionError(
                    "A registered falsification rule is required."
                )
        elif (
            spec.constructor_policy
            == ConstructorPolicy.NATIVE_REPRESENTED_SCOPE_ONLY
        ):
            if constructor_kind != "NATIVE_REPRESENTED" or raw_scope:
                raise PermissionError(
                    "Native represented propositions cannot enter raw scope."
                )
        elif (
            spec.constructor_policy
            == ConstructorPolicy.TRUSTED_GROUNDING_ONLY
        ):
            if (
                constructor_kind != "TRUSTED_GROUNDING"
                or raw_scope
                or not trusted_grounding_valid
            ):
                raise PermissionError(
                    "An exact valid assertion under an explicitly trusted "
                    "grounding contract is required."
                )

    @property
    def type_count(self) -> int:
        return len(self.types)

    @property
    def uninhabited_types(self) -> tuple[PropositionType, ...]:
        return tuple(
            spec.type_id
            for spec in self.types
            if spec.constructor_policy
            == ConstructorPolicy.NO_CONSTRUCTOR_CURRENTLY_AUTHORIZED
            or spec.constructor_policy
            in {
                ConstructorPolicy.MECHANICAL_RULE_ONLY,
                ConstructorPolicy.TRUSTED_GROUNDING_ONLY,
            }
        )

    def create_instance(self, *args: Any, **kwargs: Any) -> MechanicalProposition:
        raise PermissionError(
            "Caller-supplied mechanical proposition creation is forbidden."
        )

    def register(self, spec: PropositionTypeSpec) -> "FrozenPropositionTypeRegistry":
        return FrozenPropositionTypeRegistry(
            self.types + (spec,),
            self.repository_root,
        )


def default_proposition_type_registry(
    repository_root: Path | str = Path("."),
) -> FrozenPropositionTypeRegistry:
    authority_ranges = {
        PropositionType.REAL_DIFFERENCE_EXISTS: (48, 61),
        PropositionType.REAL_CONSEQUENCE_EXISTS: (63, 74),
        PropositionType.MECHANICAL_EXISTENCE_PROVED: (76, 92),
        PropositionType.MECHANICAL_WITNESS_CONSTRUCTED: (94, 101),
        PropositionType.REAL_ACQUISITION_TRACE_EXISTS: (69, 96),
        PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES: (54, 71),
    }
    statements = {
        PropositionType.REAL_DIFFERENCE_EXISTS: (
            "A scope-bound mechanically real difference exists; this type "
            "does not define its constructor."
        ),
        PropositionType.REAL_CONSEQUENCE_EXISTS: (
            "Frozen authority requires at least one real consequence for a "
            "qualified premise, without identifying a witness."
        ),
        PropositionType.MECHANICAL_EXISTENCE_PROVED: (
            "Mechanical existence is proven without identifying a concrete "
            "witness."
        ),
        PropositionType.MECHANICAL_WITNESS_CONSTRUCTED: (
            "A separately authorized rule identifies an exact mechanical "
            "witness."
        ),
        PropositionType.REAL_ACQUISITION_TRACE_EXISTS: (
            "A mechanically instantiated acquisition trace exists within "
            "the exact scope accepted by a valid grounding assertion under "
            "an explicitly trusted grounding contract; it establishes no "
            "source semantics or source witness."
        ),
        PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES: (
            "Two exact acquisition-trace referents, each already established "
            "through authorized trusted grounding as a mechanically "
            "instantiated acquisition trace, are externally accepted within "
            "one exact pair scope as two non-identical physical "
            "acquisition-trace instances; this asserts no real difference or "
            "source semantics."
        ),
    }
    policies = {
        PropositionType.REAL_DIFFERENCE_EXISTS: (
            ConstructorPolicy.NO_CONSTRUCTOR_CURRENTLY_AUTHORIZED
        ),
        PropositionType.REAL_CONSEQUENCE_EXISTS: (
            ConstructorPolicy.MECHANICAL_RULE_ONLY
        ),
        PropositionType.MECHANICAL_EXISTENCE_PROVED: (
            ConstructorPolicy.MECHANICAL_RULE_ONLY
        ),
        PropositionType.MECHANICAL_WITNESS_CONSTRUCTED: (
            ConstructorPolicy.MECHANICAL_RULE_ONLY
        ),
        PropositionType.REAL_ACQUISITION_TRACE_EXISTS: (
            ConstructorPolicy.TRUSTED_GROUNDING_ONLY
        ),
        PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES: (
            ConstructorPolicy.TRUSTED_GROUNDING_ONLY
        ),
    }
    authority_sources = {
        PropositionType.REAL_DIFFERENCE_EXISTS: AMENDMENT_06_SOURCE,
        PropositionType.REAL_CONSEQUENCE_EXISTS: AMENDMENT_06_SOURCE,
        PropositionType.MECHANICAL_EXISTENCE_PROVED: AMENDMENT_06_SOURCE,
        PropositionType.MECHANICAL_WITNESS_CONSTRUCTED: AMENDMENT_06_SOURCE,
        PropositionType.REAL_ACQUISITION_TRACE_EXISTS: AMENDMENT_07_SOURCE,
        PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES: (
            AMENDMENT_08_SOURCE
        ),
    }
    specs = []
    for type_id in PropositionType:
        authority_source = authority_sources[type_id]
        source = Path(repository_root).resolve() / authority_source
        lines = source.read_bytes().splitlines(keepends=True)
        start, end = authority_ranges[type_id]
        authority_hash = hashlib.sha256(
            b"".join(lines[start - 1 : end])
        ).hexdigest()
        statement = statements[type_id]
        specs.append(
            PropositionTypeSpec(
                type_id=type_id,
                semantic_statement=statement,
                scope_schema=(
                    (
                        "access_snapshot",
                        "mechanical_configuration",
                        "field_context",
                        "scale",
                        "genealogy",
                        "execution_lineage",
                        "acquisition_instance",
                        "acquisition_channel",
                        "acquisition_trace",
                    )
                    if type_id
                    == PropositionType.REAL_ACQUISITION_TRACE_EXISTS
                    else (
                        "access_snapshot",
                        "mechanical_configuration",
                        "field_context",
                        "scale",
                        "genealogy",
                        "execution_lineage",
                        "pair_scope",
                    )
                    if type_id
                    == PropositionType.DISTINCT_REAL_ACQUISITION_TRACE_INSTANCES
                    else (
                        "access_snapshot",
                        "mechanical_configuration",
                        "field_context",
                        "scale",
                        "genealogy",
                        "execution_lineage",
                    )
                ),
                existential=type_id
                in {
                    PropositionType.REAL_CONSEQUENCE_EXISTS,
                    PropositionType.MECHANICAL_EXISTENCE_PROVED,
                    PropositionType.REAL_ACQUISITION_TRACE_EXISTS,
                },
                witness_bearing=type_id
                == PropositionType.MECHANICAL_WITNESS_CONSTRUCTED,
                constructor_policy=policies[type_id],
                authority_source=authority_source,
                authority_range=(start, end),
                authority_range_hash=authority_hash,
                semantic_specification_hash=semantic_hash(statement),
            )
        )
    return FrozenPropositionTypeRegistry(tuple(specs), repository_root)
