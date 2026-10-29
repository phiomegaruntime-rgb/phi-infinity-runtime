"""Explicit allow/block registry for execution operations."""

from dataclasses import dataclass
from typing import Any, Callable, Literal

from .receipts import DerivationReceipt


OperationClass = Literal["M_ONLY", "EXTERNAL_BRIDGE"]
OperationHandler = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class OperationSpec:
    name: str
    classification: OperationClass
    handler: OperationHandler | None = None

    def __post_init__(self) -> None:
        if (
            self.classification == "M_ONLY"
            and self.handler is None
        ):
            raise ValueError("M_ONLY operations require a handler")
        if (
            self.classification == "EXTERNAL_BRIDGE"
            and self.handler is not None
        ):
            raise ValueError(
                "EXTERNAL_BRIDGE operations cannot have a handler"
            )


@dataclass(frozen=True, slots=True)
class OperationResult:
    operation_name: str
    value: Any
    receipt: DerivationReceipt


class OperationRegistry:
    """Runs only registered receipt-bearing M operations."""

    def __init__(self) -> None:
        self._specs: dict[str, OperationSpec] = {}

    def register_m_only(
        self,
        name: str,
        handler: OperationHandler,
    ) -> None:
        self._register(
            OperationSpec(
                name=name,
                classification="M_ONLY",
                handler=handler,
            )
        )

    def register_external(self, name: str) -> None:
        self._register(
            OperationSpec(
                name=name,
                classification="EXTERNAL_BRIDGE",
            )
        )

    def _register(self, spec: OperationSpec) -> None:
        if spec.name in self._specs:
            raise ValueError(f"Operation already registered: {spec.name}")
        self._specs[spec.name] = spec

    def spec(self, name: str) -> OperationSpec:
        try:
            return self._specs[name]
        except KeyError as exc:
            raise KeyError(f"Unknown M-machine operation: {name}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._specs))

    def invoke(
        self,
        name: str,
        *args: Any,
        input_receipt_ids: tuple[str, ...] = (),
        accessible_evidence: tuple[str, ...] = (),
        **kwargs: Any,
    ) -> OperationResult:
        spec = self.spec(name)
        if spec.classification == "EXTERNAL_BRIDGE":
            return OperationResult(
                operation_name=name,
                value=None,
                receipt=DerivationReceipt.create(
                    operation_name=name,
                    authoritative_source_file=(
                        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md"
                    ),
                    authoritative_clause=(
                        "Universal mechanical grammar and conditional"
                        " dependencies (lines 72-105)"
                    ),
                    input_receipt_ids=input_receipt_ids,
                    accessible_evidence=accessible_evidence,
                    operation_performed="Operation refused by registry.",
                    resulting_difference_or_consequence=(
                        "No external operation entered M continuation."
                    ),
                    status="BLOCKED_EXTERNAL",
                    implementation_source="m_machine/registry.py",
                    clause_id="m.transformations",
                ),
            )

        result = spec.handler(*args, **kwargs)
        if not isinstance(result, OperationResult):
            return OperationResult(
                operation_name=name,
                value=None,
                receipt=DerivationReceipt.create(
                    operation_name=name,
                    authoritative_source_file=(
                        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md"
                    ),
                    authoritative_clause=(
                        "Universal mechanical grammar from accessible"
                        " configuration to continuation (lines 72-105)"
                    ),
                    input_receipt_ids=input_receipt_ids,
                    accessible_evidence=accessible_evidence,
                    operation_performed=(
                        "M-only handler returned no derivation receipt."
                    ),
                    resulting_difference_or_consequence=(
                        "Continuation blocked; result discarded."
                    ),
                    status="BLOCKED_EXTERNAL",
                    implementation_source="m_machine/registry.py",
                    clause_id="m.transformations",
                ),
            )

        if result.receipt.status != "DERIVED_M":
            return result

        return result