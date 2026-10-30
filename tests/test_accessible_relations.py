from copy import deepcopy
from fractions import Fraction
import pytest
from independent_runtime.relations import resolve


def field(availability='3', need='5'):
    # This minimum rule is an EXPLICIT TEST ASSUMPTION, not derived from M,
    # and not asserted to model a cell or any physical transfer.
    return {'fragment:need': {'value': need},
            'fragment:available': {'value': availability},
            'fragment:exchange': {'operation': 'minimum',
                                  'inputs': ['fragment:need', 'fragment:available']}}


def test_similar_fragments_different_accessible_conditions_different_results():
    a, b = resolve(field('3'), 'fragment:exchange'), resolve(field('0'), 'fragment:exchange')
    assert (a.value, b.value) == (3, 0)
    assert a.network_sha256 != b.network_sha256
    assert a.status == 'COMPUTED_FROM_SUPPLIED_RELATIONS_NOT_M_DERIVED'


def test_absent_availability_is_unknown_not_zero_and_no_mutation():
    n = field()
    del n['fragment:available']
    before = deepcopy(n)
    r = resolve(n, 'fragment:exchange')
    assert r.status == 'UNRESOLVED' and r.value is None
    assert r.unresolved == ('fragment:available',)
    assert n == before


def test_nested_conditions_are_consumed_and_missing_leaf_is_reported():
    n = field()
    n['fragment:available'] = {'operation': 'subtract', 'inputs': ['fragment:stock', 'fragment:reserved']}
    n['fragment:stock'] = {'value': '7'}
    r = resolve(n, 'fragment:exchange')
    assert r.unresolved == ('fragment:reserved',)
    n['fragment:reserved'] = {'value': '5'}
    r = resolve(n, 'fragment:exchange')
    assert r.value == 2 and len(r.consumed) == 5


def test_zero_does_not_erase_a_declared_missing_dependency():
    n = field('0')
    n['fragment:exchange'] = {'operation': 'multiply', 'inputs': ['fragment:available', 'fragment:unknown']}
    assert resolve(n, 'fragment:exchange').value is None


def test_cycle_is_not_arbitrarily_assigned_a_fixed_point():
    n = field()
    n['fragment:available'] = {'operation': 'add', 'inputs': ['fragment:exchange']}
    r = resolve(n, 'fragment:exchange')
    assert r.value is None and r.unresolved == ('fragment:exchange:cyclic-relation',)


def test_exact_small_nonzero_and_fractional_relations():
    n = field('1e-400', '1')
    assert resolve(n, 'fragment:exchange').value == Fraction(1, 10**400)
    n['fragment:exchange']['operation'] = 'divide'
    r = resolve(n, 'fragment:exchange')
    assert r.value == Fraction(10**400) and r.value != 0


def test_zero_denominator_remains_unresolved():
    n = field('0')
    n['fragment:exchange']['operation'] = 'divide'
    r = resolve(n, 'fragment:exchange')
    assert r.value is None and r.unresolved == ('fragment:exchange:zero-denominator',)


def test_unrelated_context_bound_but_not_claimed_consumed():
    n = field()
    a = resolve(n, 'fragment:exchange')
    n['fragment:other'] = {'value': '91'}
    b = resolve(n, 'fragment:exchange')
    assert a.value == b.value and a.consumed == b.consumed
    assert a.network_sha256 != b.network_sha256


@pytest.mark.parametrize('value', [0.3, True, None, 'nan', 'inf', '1/0'])
def test_no_implicit_or_invalid_literal(value):
    n = field()
    n['fragment:available']['value'] = value
    with pytest.raises(ValueError):
        resolve(n, 'fragment:exchange')
