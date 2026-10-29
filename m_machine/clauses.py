"""Compiled references to exact authoritative M clauses.

The registry stores source text read from the authoritative documents.  It
does not copy the theory into executable code: each entry is an execution
map with a source-range hash and a status.
"""

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Literal

from .boot import verify_authoritative_boot


ClauseStatus = Literal[
    "EXECUTABLE_EXACT",
    "EXECUTABLE_PARTIAL",
    "SPEC_GAP",
]


@dataclass(frozen=True, slots=True)
class AuthoritativeClause:
    clause_id: str
    authoritative_source_file: str
    line_start: int
    line_end: int
    exact_source_text_hash: str
    exact_source_text: str
    source_text_reference: str
    prerequisites: tuple[str, ...]
    operation_status: ClauseStatus
    implementation_reference: str | None = None
    execution_role: str = "FUNDAMENTAL_CAUSAL_MECHANICS"

    @property
    def line_range(self) -> str:
        return f"lines {self.line_start}-{self.line_end}"


@dataclass(frozen=True, slots=True)
class AuthoritativeClauseRegistry:
    entries: tuple[AuthoritativeClause, ...]

    def __post_init__(self) -> None:
        ids = tuple(entry.clause_id for entry in self.entries)
        if len(ids) != len(set(ids)):
            raise ValueError("Clause IDs must be unique.")

    def get(self, clause_id: str) -> AuthoritativeClause:
        for entry in self.entries:
            if entry.clause_id == clause_id:
                return entry
        raise KeyError(f"Unknown authoritative clause: {clause_id}")

    def status(self, clause_id: str) -> ClauseStatus:
        return self.get(clause_id).operation_status


_CLAUSE_DEFINITIONS = (
    (
        "m.accessible_configuration",
        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
        72,
        105,
        (),
        "EXECUTABLE_EXACT",
        "m_machine/access.py:RawAccessibleConfiguration",
    ),
    (
        "m.differences",
        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
        72,
        105,
        ("m.accessible_configuration",),
        "EXECUTABLE_PARTIAL",
        None,
    ),
    (
        "m.dependencies",
        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
        72,
        105,
        ("m.differences",),
        "EXECUTABLE_PARTIAL",
        None,
    ),
    (
        "m.exchanges_redistributions",
        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
        72,
        105,
        ("m.dependencies",),
        "EXECUTABLE_PARTIAL",
        None,
    ),
    (
        "m.transformations",
        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
        72,
        105,
        ("m.exchanges_redistributions",),
        "EXECUTABLE_PARTIAL",
        "m_machine/adapters.py:native_step",
    ),
    (
        "m.propagations",
        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
        72,
        105,
        ("m.transformations",),
        "EXECUTABLE_PARTIAL",
        None,
    ),
    (
        "m.consequences",
        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
        72,
        105,
        ("m.propagations",),
        "EXECUTABLE_PARTIAL",
        None,
    ),
    (
        "m.readjustment",
        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
        72,
        105,
        ("m.consequences",),
        "EXECUTABLE_PARTIAL",
        "m_machine/adapters.py:native_step",
    ),
    (
        "m.continuation",
        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
        72,
        105,
        ("m.readjustment",),
        "EXECUTABLE_PARTIAL",
        "m_machine/executor.py:ExecutionResult",
    ),
    (
        "m.denaming",
        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
        241,
        270,
        ("m.accessible_configuration",),
        "EXECUTABLE_EXACT",
        "m_machine/access.py:de_name",
    ),
    (
        "m.boundary_exchange",
        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
        147,
        176,
        ("m.dependencies", "m.consequences"),
        "EXECUTABLE_EXACT",
        "m_machine/adapters.py:native_boundary_step",
    ),
    (
        "m.consequence_preservation",
        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
        303,
        321,
        ("m.consequences",),
        "EXECUTABLE_EXACT",
        "m_machine/adapters.py:native_boundary_step",
    ),
    (
        "m.unresolved_exterior",
        "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md",
        274,
        299,
        ("m.boundary_exchange",),
        "EXECUTABLE_EXACT",
        "m_machine/executor.py:boundary frontier",
    ),
    (
        "m.reopen_wall",
        (
            "docs/"
            "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_02_ACCESSIBLE_DERIVABILITY_"
            "AND_SCALE_REOPENING.md"
        ),
        74,
        95,
        ("m.unresolved_exterior",),
        "EXECUTABLE_EXACT",
        "m_machine/executor.py:ReopenRequest",
    ),
    (
        "m.first_divergence",
        (
            "docs/"
            "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_02_ACCESSIBLE_DERIVABILITY_"
            "AND_SCALE_REOPENING.md"
        ),
        405,
        432,
        ("m.continuation",),
        "SPEC_GAP",
        None,
    ),
    (
        "m.temporal_quantitative_closure",
        "docs/TEMPORAL_BRANCH_CLOSURE_CURRENT.md",
        193,
        241,
        ("m.continuation",),
        "SPEC_GAP",
        None,
    ),
)

_AMENDMENT_03_SOURCE = (
    "docs/"
    "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_03_ACCESS_REPRESENTATION_"
    "AND_RELATIONAL_INTEGRITY.md"
)

_AMENDMENT_03_CLAUSE_DEFINITIONS = (
    (
        "access.package",
        _AMENDMENT_03_SOURCE,
        12,
        26,
        (),
        "EXECUTABLE_EXACT",
        "m_machine/access_integrity.py:AccessPackage",
    ),
    (
        "access.local_referents",
        _AMENDMENT_03_SOURCE,
        28,
        42,
        ("access.package",),
        "EXECUTABLE_EXACT",
        "m_machine/access_integrity.py:AccessLocalHandle",
    ),
    (
        "access.binding",
        _AMENDMENT_03_SOURCE,
        44,
        61,
        ("access.local_referents",),
        "EXECUTABLE_EXACT",
        "m_machine/access_integrity.py:binds_a",
    ),
    (
        "access.membership",
        _AMENDMENT_03_SOURCE,
        63,
        75,
        ("access.package",),
        "EXECUTABLE_EXACT",
        "m_machine/access_integrity.py:accessible_under_a",
    ),
    (
        "access.origin",
        _AMENDMENT_03_SOURCE,
        77,
        90,
        ("access.package",),
        "EXECUTABLE_EXACT",
        "m_machine/access_integrity.py:origin_a",
    ),
    (
        "access.relation_witness",
        _AMENDMENT_03_SOURCE,
        92,
        119,
        ("access.binding", "access.membership", "access.origin"),
        "EXECUTABLE_EXACT",
        "m_machine/access_integrity.py:connects_a",
    ),
    (
        "access.discriminability_frontier",
        _AMENDMENT_03_SOURCE,
        121,
        133,
        ("access.relation_witness",),
        "SPEC_GAP",
        "m_machine/executor.py:DISCRIMINABILITY_FRONTIER",
    ),
)

_AMENDMENT_04_SOURCE = (
    "docs/"
    "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_04_BASIS_LOCAL_"
    "ACCESS_DISCRIMINABILITY.md"
)

_AMENDMENT_04_CLAUSE_DEFINITIONS = (
    (
        "access04.basis_origin",
        _AMENDMENT_04_SOURCE,
        11,
        26,
        ("access.package",),
        "EXECUTABLE_EXACT",
        "m_machine/discriminability.py:BasisRecord",
    ),
    (
        "access04.outcome_representation",
        _AMENDMENT_04_SOURCE,
        28,
        41,
        ("access04.basis_origin",),
        "EXECUTABLE_EXACT",
        "m_machine/discriminability.py:OutcomeBasisBinding",
    ),
    (
        "access04.relation_forms",
        _AMENDMENT_04_SOURCE,
        43,
        68,
        ("access04.outcome_representation",),
        "EXECUTABLE_EXACT",
        "m_machine/discriminability.py:OutcomeClassMap",
    ),
    (
        "access04.resolution_class",
        _AMENDMENT_04_SOURCE,
        70,
        93,
        ("access04.relation_forms",),
        "EXECUTABLE_EXACT",
        "m_machine/discriminability.py:ResolutionClass",
    ),
    (
        "access04.numerical_firewall",
        _AMENDMENT_04_SOURCE,
        95,
        105,
        ("access04.relation_forms",),
        "EXECUTABLE_EXACT",
        "m_machine/discriminability.py:evaluate_basis_local",
    ),
    (
        "access04.basis_local_discriminability",
        _AMENDMENT_04_SOURCE,
        107,
        136,
        ("access04.outcome_representation", "access04.relation_forms"),
        "EXECUTABLE_EXACT",
        "m_machine/discriminability.py:evaluate_basis_local",
    ),
    (
        "access04.multiple_basis_safety",
        _AMENDMENT_04_SOURCE,
        138,
        149,
        ("access04.basis_local_discriminability",),
        "EXECUTABLE_EXACT",
        "m_machine/executor.py:BasisLocalDiscriminabilitySet",
    ),
    (
        "access04.mechanics_firewall",
        _AMENDMENT_04_SOURCE,
        151,
        168,
        ("access04.basis_local_discriminability",),
        "SPEC_GAP",
        "m_machine/executor.py:GLOBAL_DISCRIMINABILITY_FRONTIER",
    ),
)

_AMENDMENT_05_SOURCE = (
    "docs/"
    "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_05_OPERATIONAL_DERIVATION_"
    "SEMANTICS_PROOF_KERNEL.md"
)

_AMENDMENT_05_CLAUSE_DEFINITIONS = (
    (
        "proof_kernel.separation",
        _AMENDMENT_05_SOURCE,
        1,
        31,
        (),
        "EXECUTABLE_EXACT",
        "m_machine/proof_kernel.py:ProofKernel",
    ),
    (
        "proof_kernel.rule_classes",
        _AMENDMENT_05_SOURCE,
        33,
        52,
        ("proof_kernel.separation",),
        "EXECUTABLE_EXACT",
        "m_machine/proof_kernel.py:RuleClass",
    ),
    (
        "proof_kernel.registration_firewall",
        _AMENDMENT_05_SOURCE,
        54,
        80,
        ("proof_kernel.rule_classes",),
        "EXECUTABLE_EXACT",
        "m_machine/proof_kernel.py:FrozenRuleRegistry",
    ),
    (
        "proof_kernel.provenance_history",
        _AMENDMENT_05_SOURCE,
        82,
        100,
        ("proof_kernel.registration_firewall",),
        "EXECUTABLE_EXACT",
        "m_machine/proof_kernel.py:ProofState",
    ),
    (
        "proof_kernel.closure_conflict",
        _AMENDMENT_05_SOURCE,
        102,
        145,
        ("proof_kernel.provenance_history",),
        "EXECUTABLE_EXACT",
        "m_machine/proof_kernel.py:ProofKernel.close",
    ),
    (
        "proof_kernel.current_raw_frontier",
        _AMENDMENT_05_SOURCE,
        147,
        184,
        ("proof_kernel.closure_conflict",),
        "EXECUTABLE_EXACT",
        "m_machine/executor.py:RAW_MECHANICAL_BOOTSTRAP_FRONTIER",
    ),
)

_AMENDMENT_06_SOURCE = (
    "docs/"
    "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_06_MECHANICAL_PROPOSITION_"
    "SEMANTICS.md"
)

_AMENDMENT_06_CLAUSE_DEFINITIONS = (
    (
        "proposition_types.separation",
        _AMENDMENT_06_SOURCE,
        1,
        46,
        (),
        "EXECUTABLE_EXACT",
        "m_machine/mechanical_propositions.py:PropositionType",
    ),
    (
        "proposition_types.real_difference",
        _AMENDMENT_06_SOURCE,
        48,
        61,
        ("proposition_types.separation",),
        "EXECUTABLE_EXACT",
        "m_machine/mechanical_propositions.py:MechanicalProposition",
    ),
    (
        "proposition_types.consequence_existence",
        _AMENDMENT_06_SOURCE,
        63,
        74,
        ("proposition_types.real_difference",),
        "EXECUTABLE_EXACT",
        "m_machine/mechanical_propositions.py:PropositionTypeSpec",
    ),
    (
        "proposition_types.witness_separation",
        _AMENDMENT_06_SOURCE,
        76,
        101,
        ("proposition_types.consequence_existence",),
        "EXECUTABLE_EXACT",
        "m_machine/mechanical_propositions.py:WitnessStatus",
    ),
    (
        "proposition_types.registry",
        _AMENDMENT_06_SOURCE,
        103,
        137,
        ("proposition_types.witness_separation",),
        "EXECUTABLE_EXACT",
        "m_machine/mechanical_propositions.py:FrozenPropositionTypeRegistry",
    ),
    (
        "proposition_types.scope_identity",
        _AMENDMENT_06_SOURCE,
        139,
        150,
        ("proposition_types.registry",),
        "EXECUTABLE_EXACT",
        "m_machine/mechanical_propositions.py:FrozenPropositionTypeRegistry",
    ),
    (
        "proposition_types.raw_firewall",
        _AMENDMENT_06_SOURCE,
        152,
        176,
        ("proposition_types.scope_identity",),
        "EXECUTABLE_EXACT",
        "m_machine/proof_kernel.py:ProofKernel",
    ),
)

_AMENDMENT_07_SOURCE = (
    "docs/"
    "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_07_TRUSTED_MECHANICAL_"
    "GROUNDING_ACQUISITION_SEMANTICS.md"
)

_AMENDMENT_07_CLAUSE_DEFINITIONS = (
    (
        "grounding.separation",
        _AMENDMENT_07_SOURCE,
        20,
        67,
        (),
        "EXECUTABLE_EXACT",
        "m_machine/grounding.py:GroundingRegistry",
    ),
    (
        "grounding.trace_proposition",
        _AMENDMENT_07_SOURCE,
        69,
        96,
        ("grounding.separation",),
        "EXECUTABLE_EXACT",
        "m_machine/mechanical_propositions.py:PropositionType",
    ),
    (
        "grounding.contract_trust",
        _AMENDMENT_07_SOURCE,
        98,
        125,
        ("grounding.separation",),
        "EXECUTABLE_EXACT",
        "m_machine/grounding.py:GroundingContract",
    ),
    (
        "grounding.assertion_validation",
        _AMENDMENT_07_SOURCE,
        127,
        165,
        ("grounding.contract_trust",),
        "EXECUTABLE_EXACT",
        "m_machine/grounding.py:GroundingRegistry.validate_assertion",
    ),
    (
        "grounding.provenance_admission",
        _AMENDMENT_07_SOURCE,
        167,
        191,
        ("grounding.assertion_validation",),
        "EXECUTABLE_EXACT",
        "m_machine/proof_kernel.py:ProofKernel.admit_grounded_premise",
    ),
    (
        "grounding.history",
        _AMENDMENT_07_SOURCE,
        193,
        214,
        ("grounding.provenance_admission",),
        "EXECUTABLE_EXACT",
        "m_machine/grounding.py:GroundingApplicability",
    ),
    (
        "grounding.source_firewall",
        _AMENDMENT_07_SOURCE,
        216,
        237,
        ("grounding.assertion_validation",),
        "EXECUTABLE_EXACT",
        "m_machine/grounding.py:GroundingValidationResult",
    ),
    (
        "grounding.execution_frontier",
        _AMENDMENT_07_SOURCE,
        239,
        258,
        ("grounding.provenance_admission",),
        "EXECUTABLE_EXACT",
        "m_machine/executor.py:MExecutionMachine.execute_grounded",
    ),
)

_AMENDMENT_08_SOURCE = (
    "docs/"
    "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_08_PAIRWISE_TRUSTED_"
    "GROUNDING_DISTINCT_INSTANCE_SEMANTICS.md"
)

_AMENDMENT_08_CLAUSE_DEFINITIONS = (
    (
        "pairwise_grounding.semantics",
        _AMENDMENT_08_SOURCE,
        16,
        71,
        (),
        "EXECUTABLE_EXACT",
        "m_machine/mechanical_propositions.py:PropositionType",
    ),
    (
        "pairwise_grounding.contract",
        _AMENDMENT_08_SOURCE,
        73,
        153,
        ("pairwise_grounding.semantics",),
        "EXECUTABLE_EXACT",
        "m_machine/grounding.py:PairwiseGroundingAssertion",
    ),
    (
        "pairwise_grounding.firewalls",
        _AMENDMENT_08_SOURCE,
        155,
        182,
        ("pairwise_grounding.contract",),
        "EXECUTABLE_EXACT",
        "m_machine/grounding.py:GroundingRegistry.validate_pairwise_assertion",
    ),
    (
        "pairwise_grounding.kernel_support",
        _AMENDMENT_08_SOURCE,
        184,
        216,
        ("pairwise_grounding.firewalls",),
        "EXECUTABLE_EXACT",
        "m_machine/proof_kernel.py:ProofKernel",
    ),
    (
        "pairwise_grounding.frontier",
        _AMENDMENT_08_SOURCE,
        218,
        232,
        ("pairwise_grounding.kernel_support",),
        "EXECUTABLE_EXACT",
        "m_machine/proof_kernel.py:NON_IDENTITY_RULE_REGISTRATION_FRONTIER",
    ),
)


def _exact_source_text(
    root: Path,
    source_file: str,
    line_start: int,
    line_end: int,
) -> str:
    path = root / source_file
    try:
        lines = path.read_bytes().splitlines(keepends=True)
        selected = lines[line_start - 1 : line_end]
    except IndexError as exc:
        raise ValueError(
            f"Invalid authoritative range: {source_file}:{line_start}-{line_end}"
        ) from exc
    if len(selected) != line_end - line_start + 1:
        raise ValueError(
            f"Authoritative range is incomplete: "
            f"{source_file}:{line_start}-{line_end}"
        )
    return b"".join(selected).decode("utf-8")


def compile_authoritative_clause_registry(
    repository_root: str | Path | None = None,
) -> AuthoritativeClauseRegistry:
    """Compile exact source ranges after authoritative boot verification."""

    verification = verify_authoritative_boot(repository_root)
    root = verification.repository_root
    entries = []
    for (
        clause_id,
        source_file,
        line_start,
        line_end,
        prerequisites,
        operation_status,
        implementation_reference,
    ) in (
        _CLAUSE_DEFINITIONS
        + _AMENDMENT_03_CLAUSE_DEFINITIONS
        + _AMENDMENT_04_CLAUSE_DEFINITIONS
        + _AMENDMENT_05_CLAUSE_DEFINITIONS
        + _AMENDMENT_06_CLAUSE_DEFINITIONS
        + _AMENDMENT_07_CLAUSE_DEFINITIONS
        + _AMENDMENT_08_CLAUSE_DEFINITIONS
    ):
        source_text = _exact_source_text(
            root,
            source_file,
            line_start,
            line_end,
        )
        entries.append(
            AuthoritativeClause(
                clause_id=clause_id,
                authoritative_source_file=source_file,
                line_start=line_start,
                line_end=line_end,
                exact_source_text_hash=hashlib.sha256(
                    source_text.encode("utf-8")
                ).hexdigest(),
                exact_source_text=source_text,
                source_text_reference=(
                    f"{source_file}:lines {line_start}-{line_end}"
                ),
                prerequisites=tuple(prerequisites),
                operation_status=operation_status,
                implementation_reference=implementation_reference,
                execution_role=(
                    (
                        "NON_GENERATIVE_GROUNDING_SUBSTRATE"
                        if clause_id
                        in {
                            "grounding.assertion_validation",
                            "grounding.provenance_admission",
                            "grounding.history",
                        }
                        else (
                            "EXTERNAL_EPISTEMIC_ACQUISITION_INTERFACE"
                            if clause_id
                            in {
                                "grounding.trace_proposition",
                                "grounding.source_firewall",
                                "grounding.execution_frontier",
                            }
                            else "TRUSTED_GROUNDING_SEMANTICS"
                        )
                    )
                    if source_file == _AMENDMENT_07_SOURCE
                    else (
                        "NON_GENERATIVE_PAIRWISE_GROUNDING_SUBSTRATE"
                        if clause_id
                        in {
                            "pairwise_grounding.firewalls",
                            "pairwise_grounding.kernel_support",
                            "pairwise_grounding.frontier",
                        }
                        else (
                            "EXTERNAL_EPISTEMIC_ACQUISITION_STRUCTURAL_INTERFACE"
                            if clause_id == "pairwise_grounding.contract"
                            else "PAIRWISE_TRUSTED_GROUNDING_SEMANTICS"
                        )
                    )
                    if source_file == _AMENDMENT_08_SOURCE
                    else "OPERATIONAL_SEMANTICS"
                    if source_file == _AMENDMENT_05_SOURCE
                    else (
                        "MECHANICAL_PROPOSITION_SEMANTICS"
                        if source_file == _AMENDMENT_06_SOURCE
                        else (
                            "ACCESS_REPRESENTATION"
                            if source_file in {
                            _AMENDMENT_03_SOURCE,
                            _AMENDMENT_04_SOURCE,
                        }
                            else "FUNDAMENTAL_CAUSAL_MECHANICS"
                        )
                    )
                ),
            )
        )
    return AuthoritativeClauseRegistry(entries=tuple(entries))