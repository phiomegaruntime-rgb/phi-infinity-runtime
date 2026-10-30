from copy import deepcopy
import pytest
from independent_runtime.relations import resolve, investigate


def case():
    # Declared test relation, not a physical law inferred by the software.
    return {
        'fragment:exchange': {'operation': 'minimum', 'inputs': ['fragment:need', 'fragment:supply']},
        'fragment:need': {'value': '5'},
        'fragment:supply': {'access': {'inspect': 'fragment:assembly',
                                     'observation': 'Inspect the assembly to establish delivered supply and its internal dependencies.'}},
    }


def test_reports_specific_inspection_and_dependency_path():
    r = resolve(case(), 'fragment:exchange')
    a, = r.access_requests
    assert (a.fragment, a.inspect, a.reason) == ('fragment:supply', 'fragment:assembly', 'NOT_ACCESSED')
    assert a.path == ('fragment:exchange', 'fragment:supply')
    assert 'internal dependencies' in a.observation


def test_descends_into_observed_internal_relations_then_recomputes():
    network = case()
    before = deepcopy(network)
    seen = []
    def acquire(a):
        seen.append(a.fragment)
        if a.fragment == 'fragment:supply':
            return {'fragment:supply': {'operation': 'subtract', 'inputs': ['fragment:stock', 'fragment:loss']},
                    'fragment:stock': {'value': '7'},
                    'fragment:loss': {'access': {'inspect': 'fragment:contact', 'observation': 'Measure the loss at this contact.'}}}
        assert a.inspect == 'fragment:contact'
        assert a.path == ('fragment:exchange', 'fragment:supply', 'fragment:loss')
        return {'fragment:loss': {'value': '4'}}
    r = investigate(network, 'fragment:exchange', acquire, max_rounds=2)
    assert r.result.value == 3 and r.stop_reason == 'RESOLVED_WITHIN_ACCESS'
    assert seen == ['fragment:supply', 'fragment:loss']
    assert len(r.history) == 3
    assert network == before


def test_no_observation_is_not_zero_or_absence_in_reality():
    r = investigate(case(), 'fragment:exchange', lambda a: None, max_rounds=5)
    assert r.result.value is None and r.stop_reason == 'NO_FURTHER_ACCESS'
    assert r.result.access_requests[0].fragment == 'fragment:supply'
    n = case()
    n['fragment:supply'] = {'value': '0'}
    r = investigate(n, 'fragment:exchange', lambda a: pytest.fail('no further observation needed'), max_rounds=0)
    assert r.result.value == 0 and r.stop_reason == 'RESOLVED_WITHIN_ACCESS'


def test_budget_stops_access_not_reality_and_preserves_next_request():
    r = investigate(case(), 'fragment:exchange', lambda a: pytest.fail('budget is zero'), max_rounds=0)
    assert r.stop_reason == 'ACCESS_BUDGET_EXHAUSTED' and r.result.value is None
    assert r.result.access_requests


def test_unchanged_observation_does_not_loop():
    n = case()
    calls = []
    r = investigate(n, 'fragment:exchange', lambda a: calls.append(a) or n, max_rounds=100)
    assert r.stop_reason == 'NO_FURTHER_ACCESS' and len(calls) == 1


def test_cycle_and_zero_denominator_require_different_investigations():
    n = {'fragment:a': {'operation': 'add', 'inputs': ['fragment:a']}}
    assert resolve(n, 'fragment:a').access_requests[0].reason == 'CYCLIC_REPRESENTATION'
    n = {'fragment:a': {'operation': 'divide', 'inputs': ['fragment:z', 'fragment:z']}, 'fragment:z': {'value': '0'}}
    a, = resolve(n, 'fragment:a').access_requests
    assert a.reason == 'ZERO_DENOMINATOR' and 'known zero' in a.observation


def test_all_shared_dependency_paths_remain_visible():
    n = {'fragment:a': {'operation': 'add', 'inputs': ['fragment:b', 'fragment:c']},
         'fragment:b': {'operation': 'add', 'inputs': ['fragment:x']},
         'fragment:c': {'operation': 'add', 'inputs': ['fragment:x']}}
    r = resolve(n, 'fragment:a')
    assert {a.path for a in r.access_requests} == {
        ('fragment:a', 'fragment:b', 'fragment:x'), ('fragment:a', 'fragment:c', 'fragment:x')}


def test_invalid_acquisition_cannot_produce_a_value():
    with pytest.raises(ValueError):
        investigate(case(), 'fragment:exchange', lambda a: {'fragment:supply': {'value': float('nan')}}, max_rounds=1)
