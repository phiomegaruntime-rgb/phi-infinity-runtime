
import subprocess
import sys


def execute(command, title):

    print()
    print("=" * 78)
    print(title)
    print("=" * 78)

    result = subprocess.run(
        command,
        text=True,
    )

    if result.returncode != 0:
        raise SystemExit(
            result.returncode
        )


execute(
    [
        sys.executable,
        "-m",
        "pytest",
        "-q",
    ],
    "PERMANENT REGRESSION SUITE",
)


execute(
    [
        sys.executable,
        "validation/gates/rho_emergence_gate.py",
    ],
    "RHO EMERGENCE VALIDATION",
)


execute(
    [
        sys.executable,
        "main.py",
    ],
    "MAIN DEMO",
)


print()
print("=" * 78)
print("ALL CURRENT PHI-INFINITY VALIDATION GATES PASSED")
print("=" * 78)
