import hashlib
from pathlib import Path


FROZEN_CONTRACT = Path(
    "docs/UNIVERSAL_MOTHER_MECHANICS_CURRENT.md"
)

AMENDMENT = Path(
    "docs/UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_01_MECHANICAL_ADMISSIBILITY.md"
)

EXPECTED_FROZEN_SHA256 = (
    "0cea8129245b212c04fa776bdc1b718fabf50998a9635e1e06716504fc410f7b"
)


def sha256_file(path):

    h = hashlib.sha256()

    h.update(
        path.read_bytes()
    )

    return h.hexdigest()


def test_frozen_universal_mother_mechanics_contract_is_byte_identical():

    assert FROZEN_CONTRACT.exists()

    assert (
        sha256_file(
            FROZEN_CONTRACT
        )
        ==
        EXPECTED_FROZEN_SHA256
    )


def test_mechanical_admissibility_amendment_remains_explicit():

    assert AMENDMENT.exists()

    text = AMENDMENT.read_text(
        encoding="utf-8"
    )

    required = [
        "MECHANICAL ADMISSIBILITY PRINCIPLE",
        "does **not** modify the frozen Universal Mother Mechanics",
        r"\operatorname{Persist}(X)",
        r"\operatorname{Compatible}_{\mathcal M}",
        "INCOMPATIBILITY WITH PERSISTENCE",
        "VIOLATION OF MECHANICS",
        "UNIVERSALITY FALSIFIED",
        "No second mechanics has been added",
        "not an arbitrary",
        "post-hoc explanation",
    ]

    for fragment in required:
        assert fragment in text
