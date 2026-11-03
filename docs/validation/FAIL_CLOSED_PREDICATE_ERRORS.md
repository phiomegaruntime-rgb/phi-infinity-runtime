# Fail-closed predicate evaluation — limited repair

The frozen gate locked on a predicate's **false** result but not on an
exception raised while evaluating a predicate, including conversion of
ambiguous NumPy arrays to truth values. This change sets the lock and raises
`FirstDivergenceException` from that exception. A legitimate false result
retains the original refusal message and state behavior. Already-locked calls
remain blocked until the caller invokes `trigger_reopen()`.

This is **not** a mechanism for authenticating `step_metrics`, restricting
caller code, or enforcing an independent REOPEN interval. Existing predicate
truthiness semantics remain unchanged for normal successful evaluations.

Run: `python -m pytest -q tests/test_gate_independent_audit.py tests/test_gate_predicate_fail_closed.py`
