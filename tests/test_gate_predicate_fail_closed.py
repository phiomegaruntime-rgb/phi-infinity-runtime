"""Unexpected predicate failure cannot leave the gate unlocked."""
import numpy as np
import pytest
from src.gating import FirstDivergenceException, MultiAccessGating


@pytest.mark.parametrize('exception_type', [RuntimeError, KeyError, ValueError, TypeError])
def test_predicate_exception_locks_persistently(exception_type):
    flag = {'throw': True}
    def predicate(metrics):
        if flag['throw']:
            raise exception_type('deliberate test failure')
        return metrics['ok']
    gate = MultiAccessGating(predicate)
    with pytest.raises(FirstDivergenceException, match=r'k\*=0') as err:
        gate.check_trajectory({'ok': True}, 0)
    assert isinstance(err.value.__cause__, exception_type)
    assert gate.execution_locked
    flag['throw'] = False
    with pytest.raises(FirstDivergenceException, match='locked'):
        gate.check_trajectory({'ok': True}, 1)
    gate.trigger_reopen()
    assert gate.check_trajectory({'ok': True}, 2) is None


def test_numpy_ambiguous_truth_value_is_fail_closed():
    gate = MultiAccessGating(lambda _: np.array([True, False]))
    with pytest.raises(FirstDivergenceException) as err:
        gate.check_trajectory({}, 3)
    assert isinstance(err.value.__cause__, ValueError)
    assert gate.execution_locked


def test_false_predicate_error_contract_preserved():
    gate = MultiAccessGating(lambda m: m['present'])
    with pytest.raises(FirstDivergenceException, match='Constraints violated') as err:
        gate.check_trajectory({'present': False}, 42)
    assert err.value.__cause__ is None
    assert gate.execution_locked


def test_bool_conversion_failure_also_locks():
    class Unusable:
        def __bool__(self):
            raise LookupError('cannot decide')
    gate = MultiAccessGating(lambda _: Unusable())
    with pytest.raises(FirstDivergenceException) as err:
        gate.check_trajectory({}, 5)
    assert isinstance(err.value.__cause__, LookupError)
    assert gate.execution_locked
