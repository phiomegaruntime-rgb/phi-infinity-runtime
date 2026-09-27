"""Audit author-supplied 2026-09-25 outputs, without rerunning the simulator.

The three inputs are external to this repository. This gate verifies their
identity and the claims transcribed in the September status document. It does
not validate the simulator's rules or reproduce its execution.
"""

import argparse
from collections import Counter
import csv
from hashlib import sha256
from pathlib import Path


EXPECTED_SHA256 = {
    "stress_test_results.csv": "94140697379e72bd047578a35ccf09dd26b728bd346d3d49945ff1f703c7ac52",
    "stress_test.log": "4747db043a9fa2a3ada09d13a887672aa394cf65ca8260a9663f30aee39f6277",
    "stress_test_comparison.png": "373c8ccd62eadf848b0b4a1621df89f305031c038bec752e975b698ec49ddaef",
}

FIELDS = (
    "step", "pressure", "delta", "disturbance", "open_state", "open_drift",
    "open_ok", "open_corrupted", "open_event", "phi_state", "phi_R",
    "phi_ok", "phi_halted", "phi_event",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(directory):
    directory = Path(directory)
    for filename, expected in EXPECTED_SHA256.items():
        path = directory / filename
        require(path.is_file(), f"Missing input: {path}")
        actual = sha256(path.read_bytes()).hexdigest()
        require(actual == expected, f"SHA-256 mismatch: {filename}")

    with (directory / "stress_test_results.csv").open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        require(tuple(reader.fieldnames or ()) == FIELDS, "Unexpected CSV columns")
        rows = list(reader)

    require(len(rows) == 100, "Expected exactly 100 CSV cycles")
    require([int(row["step"]) for row in rows] == list(range(1, 101)),
            "Steps must be consecutive from 1 to 100")

    lines = (directory / "stress_test.log").read_text(encoding="utf-8").splitlines()
    require(len(lines) == 100, "Expected exactly 100 log entries")
    for step, (row, line) in enumerate(zip(rows, lines), 1):
        fields = [piece.split("=", 1) for piece in line.split(",")]
        require(all(len(field) == 2 for field in fields), f"Malformed log entry at step {step}")
        require(dict(fields) == row, f"CSV/log disagreement at step {step}")

    events = Counter(row["phi_event"] for row in rows)
    require(events == {"COMMIT": 20, "REJECT_NON_CONSERVATIVE": 80},
            "Unexpected PHI event counts")
    require(all(row["phi_halted"] == "0" for row in rows),
            "A PHI gate stop was recorded")
    first = next((row for row in rows if row["open_corrupted"] == "1"), None)
    require(first is not None and first["step"] == "16" and
            first["open_drift"] == "177.08721760057597",
            "Unexpected first open-control corruption")
    require(rows[-1]["phi_state"] == "106.2790943851747" and
            rows[-1]["phi_R"] == "20.696045734309212",
            "Unexpected final PHI values")

    return "100 cycles; 20 commits; 80 rejects; 0 PHI gate stops; first open corruption at 16"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path, help="Folder containing the three original output files")
    args = parser.parse_args()
    try:
        summary = audit(args.input_dir)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"ARTIFACT AUDIT FAILED: {exc}\n")
    print("ARTIFACT AUDIT PASS:", summary)
    print("Scope: identity and archived-output consistency; no simulator replay or physical validation.")


if __name__ == "__main__":
    main()
