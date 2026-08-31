
import hashlib
from pathlib import Path


FROZEN = Path(
    "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md"
)

AMENDMENT = Path(
    "docs/"
    "UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_02_"
    "ACCESSIBLE_DERIVABILITY_AND_SCALE_REOPENING.md"
)

README = Path("README.md")

SEQUENCE = Path(
    "docs/validation/"
    "CUMULATIVE_FALSIFICATION_SEQUENCE.md"
)

LEDGER = Path(
    "docs/validation/"
    "VALIDATION_LEDGER_CURRENT.md"
)

EXPECTED_FROZEN_SHA256 = (
    "0cea8129245b212c04fa776bdc1b718fabf50998a9635e1e06716504fc410f7b"
)


def _sha256(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def test_amendment_02_preserves_frozen_mother_mechanics():
    assert FROZEN.exists()

    assert (
        _sha256(FROZEN)
        ==
        EXPECTED_FROZEN_SHA256
    )


def test_accessible_derivability_and_scale_reopening_are_explicit():
    assert AMENDMENT.exists()

    text = AMENDMENT.read_text(
        encoding="utf-8"
    )

    required = [
        "Accessible Derivability Principle",
        "Scale Reopening Wall",
        "PotentiallyCalculable",
        "NotDerivable",
        "NotDistinguishable",
        "REOPEN PREVIOUS REPRESENTATIONAL CLOSURE FIRST",
        "REOPEN BEFORE IMPORTING THEORY",
        "UNRESOLVED",
        "No second fundamental causal operation has been added",
    ]

    for phrase in required:
        assert phrase in text


def test_bell_reconstruction_adds_no_signal_or_second_mechanics():
    text = AMENDMENT.read_text(
        encoding="utf-8"
    )

    required = [
        "Bell as Motivating Adversarial Reconstruction",
        "DISTANCE",
        "MECHANICAL DISCONNECTION",
        "DISTINGUISHABILITY",
        "AUTOSUFFICIENCY",
        "FRAGMENTATION",
        "FACTORIZATION",
        "M Is Not a Signal",
        "superluminal signal",
        "does not claim that the current numerical runtime has",
        "exact Bell joint probability distribution",
    ]

    for phrase in required:
        assert phrase in text


def test_wall_25_is_integrated_into_repository_genealogy():
    readme = README.read_text(
        encoding="utf-8"
    )

    sequence = SEQUENCE.read_text(
        encoding="utf-8"
    )

    ledger = LEDGER.read_text(
        encoding="utf-8"
    )

    assert (
        "<!-- PHI:ACCESSIBLE_DERIVABILITY:START -->"
        in readme
    )

    assert (
        "Accessible Derivability and Scale Reopening"
        in readme
    )

    assert (
        "25. **Accessible derivability / scale reopening**"
        in sequence
    )

    assert (
        "Bell-type spatial distinction"
        in sequence
    )

    assert (
        "<!-- PHI:AMENDMENT_02_ACCESSIBLE_DERIVABILITY:START -->"
        in ledger
    )

    assert (
        "Amendment 02"
        in ledger
    )
