"""Raw access and semantic quarantine for the M-only execution boundary."""

from dataclasses import dataclass
from typing import Any

from .receipts import DerivationReceipt


def _immutable_sequence(values: Any) -> tuple[Any, ...]:
    if values is None:
        return ()
    if isinstance(values, tuple):
        return values
    return tuple(values)


@dataclass(frozen=True, slots=True)
class HumanTranslationSpace:
    """Human semantic material kept outside mechanical generation."""

    labels: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    domain_descriptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "labels", _immutable_sequence(self.labels))
        object.__setattr__(
            self,
            "categories",
            _immutable_sequence(self.categories),
        )
        object.__setattr__(
            self,
            "domain_descriptions",
            _immutable_sequence(self.domain_descriptions),
        )


@dataclass(frozen=True, slots=True)
class RawAccessibleConfiguration:
    """An ordered, provenance-preserving container for accessible values."""

    raw_values: tuple[Any, ...]
    ordering: tuple[Any, ...] = ()
    provenance: tuple[Any, ...] = ()
    access_provenance: tuple[Any, ...] = ()
    genealogy: tuple[Any, ...] = ()
    resolution_sampling: tuple[Any, ...] = ()
    externally_imposed_constraints: tuple[Any, ...] = ()
    m_execution_access: Any = None

    def __post_init__(self) -> None:
        for name in (
            "raw_values",
            "ordering",
            "provenance",
            "access_provenance",
            "genealogy",
            "resolution_sampling",
            "externally_imposed_constraints",
        ):
            object.__setattr__(
                self,
                name,
                _immutable_sequence(getattr(self, name)),
            )


@dataclass(frozen=True, slots=True)
class DeNamedAccess:
    """Raw accessible reality plus quarantined human semantic material."""

    raw_access: RawAccessibleConfiguration
    human_translation: HumanTranslationSpace
    receipt: DerivationReceipt


def de_name(
    access: RawAccessibleConfiguration,
    human_translation: HumanTranslationSpace | None = None,
) -> DeNamedAccess:
    """Separate names/categories without deleting or changing raw access."""

    if not isinstance(access, RawAccessibleConfiguration):
        raise TypeError("de_name() requires RawAccessibleConfiguration")

    translation = human_translation or HumanTranslationSpace()
    receipt = DerivationReceipt.create(
        operation_name="DeName",
        authoritative_source_file=(
            "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md"
        ),
        authoritative_clause=(
            "ACCESSPOINTER -> DeName -> ACCESSIBLE REALITY -> M"
            " (lines 241-270)"
        ),
        input_receipt_ids=(),
        accessible_evidence=(
            "raw accessible values preserved",
            "ordering preserved",
            "provenance and access provenance preserved",
            "genealogy and imposed constraints preserved",
            "human semantic material quarantined",
        ),
        operation_performed=(
            "Isolate human semantic material from accessible reality."
        ),
        resulting_difference_or_consequence=(
            "No raw accessible value is removed or rewritten."
        ),
        status="DERIVED_M",
        implementation_source="m_machine/access.py:de_name",
        clause_id="m.denaming",
    )
    return DeNamedAccess(
        raw_access=access,
        human_translation=translation,
        receipt=receipt,
    )