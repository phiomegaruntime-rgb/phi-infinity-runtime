# Alex C11 independent gate-state oracle

This is the *relevant extract* of the offline C11 deterministic testing
approach, not the entire unrelated C11 algorithm-testing suite. The
`dt_mix()` fingerprint primitive was adapted from the supplied
`ALEX_MORARU_OFFLINE_C11_DETERMINISTIC_TESTERS_1.0.0_FINAL_DELTA.zip`.
The bounded gate-state generator is newly written for this contribution.
The 4^5 possible five-event traces produce 5,120 expected decisions. The
Python test independently executes PHI's actual gate against each trace.

The C11 oracle does **not** implement PHI physics, authenticate support,
or establish M. It only supplies a separate language's state-machine oracle.

On macOS or Linux:

```sh
cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror \
    verification/c11/gate_transition_oracle.c -o /tmp/phi_gate_oracle
/tmp/phi_gate_oracle > /tmp/phi_gate_transitions.csv
python -m pytest -q tests/test_c11_gate_oracle.py
```

The pytest case skips with a reason when a native C11 compiler is unavailable;
for a **verified** contribution, run it on a machine with Xcode command line
tools or equivalent. No compiled executable is committed.
