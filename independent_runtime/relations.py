"""Read-only evaluation of explicitly supplied, finite accessible relations.

Arithmetic is a representation supplied by the caller, not an inferred law of M.
No numerical state, authority, or support database is modified by this module.
"""
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
from typing import Mapping


@dataclass(frozen=True)
class AccessRequest:
    fragment: str
    inspect: str
    observation: str
    reason: str
    path: tuple[str, ...]


@dataclass(frozen=True)
class RelationResult:
    status: str
    value: Fraction | None
    unresolved: tuple[str, ...]
    consumed: tuple[str, ...]
    network_sha256: str
    access_requests: tuple[AccessRequest, ...] = ()


def resolve(network: Mapping[str, dict], target: str) -> RelationResult:
    """Resolve a target from exact rational literals and declared expressions.

    Nodes all have fragment identifiers. Fields describe only the current wire
    representation: either {'value': 'decimal or rational'} or
    {'operation': 'add|subtract|multiply|divide|minimum', 'inputs': [refs]}.
    All listed inputs are necessary, even in a product containing a known zero.
    The digest binds the entire supplied snapshot, including accessible context
    not used by this particular calculation. It is not an external attestation.
    """
    if type(network) is not dict or type(target) is not str:
        raise ValueError('network must be a dictionary and target a fragment reference')
    def valid_ref(ref):
        return type(ref) is str and ref.startswith('fragment:') and len(ref) > 9
    if not valid_ref(target) or any(not valid_ref(ref) for ref in network):
        raise ValueError('every reference must name a fragment')
    # Validate the whole accessible snapshot, before evaluating any target.
    for node in network.values():
        if type(node) is not dict:
            raise ValueError('invalid fragment representation')
        if set(node) == {'access'}:
            access = node['access']
            if (type(access) is not dict or set(access) != {'inspect', 'observation'}
                    or not valid_ref(access['inspect'])
                    or type(access['observation']) is not str
                    or not access['observation'].strip()):
                raise ValueError('access requires an inspection fragment and an explicit observation')
        elif set(node) == {'value'}:
            value = node['value']
            if type(value) is not str:
                raise ValueError('exact values must be strings; implicit float rounding is forbidden')
            try:
                Fraction(value)
            except (ValueError, ZeroDivisionError) as exc:
                raise ValueError('invalid exact value') from exc
        elif set(node) == {'operation', 'inputs'}:
            op, inputs = node['operation'], node['inputs']
            if type(op) is not str or op not in {'add', 'subtract', 'multiply', 'divide', 'minimum'}:
                raise ValueError('unknown supplied operation')
            if type(inputs) is not list or not inputs or any(not valid_ref(i) for i in inputs):
                raise ValueError('relation requires explicit fragment inputs')
            if op in {'subtract', 'divide'} and len(inputs) != 2:
                raise ValueError('binary relation requires exactly two inputs')
        else:
            raise ValueError('fragment must have one exact supported representation')
    # Copy via canonical bytes so mutation of caller containers cannot alter
    # the snapshot midway through traversal.
    encoded = json.dumps(network, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    snapshot = json.loads(encoded)
    digest = sha256(encoded).hexdigest()
    cache, active, consumed, missing = {}, set(), set(), set()
    requests = []

    def request(ref, reason, path, *, inspect=None, observation=None):
        requests.append(AccessRequest(
            ref, inspect or ref,
            observation or {
                'NOT_ACCESSED': 'Establish the accessible value or internal relations of this fragment; absence from this snapshot is not absence from reality.',
                'CYCLIC_REPRESENTATION': 'Examine the internal relations and accessible conditions of this cycle; no fixed point has been established by this representation.',
                'ZERO_DENOMINATOR': 'Examine the applicability of this supplied division relation to its known zero denominator; do not invent a nonzero value.',
                'REPRESENTATION_DEPTH': 'Provide sufficient computational access or a shallower equivalent representation; this limit is not a boundary of reality.',
            }[reason], reason, path,
        ))

    def visit(ref, path=()):
        path = path + (ref,)
        if ref in cache and cache[ref] is not None:
            return cache[ref]
        if ref in active:
            missing.add(ref + ':cyclic-relation')
            request(ref, 'CYCLIC_REPRESENTATION', path)
            return None
        if ref not in snapshot:
            missing.add(ref)
            request(ref, 'NOT_ACCESSED', path)
            return None
        consumed.add(ref)
        active.add(ref)
        node = snapshot[ref]
        if 'access' in node:
            missing.add(ref)
            request(ref, 'NOT_ACCESSED', path, **node['access'])
            result = None
        elif 'value' in node:
            result = Fraction(node['value'])
        else:
            values = [visit(i, path) for i in node['inputs']]
            result = None
            if all(v is not None for v in values):
                op = node['operation']
                if op == 'add':
                    result = sum(values, Fraction(0))
                elif op == 'subtract':
                    result = values[0] - values[1]
                elif op == 'multiply':
                    result = Fraction(1)
                    for value in values:
                        result *= value
                elif op == 'minimum':
                    result = min(values)
                elif values[1] == 0:
                    missing.add(ref + ':zero-denominator')
                    request(ref, 'ZERO_DENOMINATOR', path)
                else:
                    result = values[0] / values[1]
        active.remove(ref)
        cache[ref] = result
        return result

    try:
        value = visit(target)
    except RecursionError:
        # A computation limit is not a claim about the reality of the network.
        missing.add(target + ':representation-depth-exceeded')
        request(target, 'REPRESENTATION_DEPTH', (target,))
        value = None
    return RelationResult(
        'COMPUTED_FROM_SUPPLIED_RELATIONS_NOT_M_DERIVED' if value is not None else 'UNRESOLVED',
        value, tuple(sorted(missing)), tuple(sorted(consumed)), digest,
        tuple(dict.fromkeys(requests)),
    )


@dataclass(frozen=True)
class InvestigationResult:
    result: RelationResult
    history: tuple[RelationResult, ...]
    stop_reason: str


def investigate(network, target, acquire, *, max_rounds):
    """Request observation/enrichment, then descend into revealed relations.

    acquire(request) supplies a mapping of actually acquired fragment records,
    or None when current access cannot supply an answer. It must not invent
    observations. This module has no sensors and does not execute instruments.
    max_rounds is an explicit computational budget, not an ontological depth.
    The caller's network and the numerical engine are never mutated.
    """
    if type(max_rounds) is not int or max_rounds < 0 or not callable(acquire):
        raise ValueError('explicit nonnegative round budget and acquisition callable required')
    initial = resolve(network, target)
    current = json.loads(json.dumps(network))
    history = [initial]
    for _ in range(max_rounds):
        result = history[-1]
        if result.value is not None:
            return InvestigationResult(result, tuple(history), 'RESOLVED_WITHIN_ACCESS')
        # Gather only requests from this snapshot. Re-plan immediately after
        # the first enrichment: old requests may no longer be relevant.
        enriched = False
        for access in result.access_requests:
            additions = acquire(access)
            if additions is None:
                continue
            if type(additions) is not dict:
                raise ValueError('acquisition must return fragment records or None')
            candidate = {**current, **additions}
            checked = resolve(candidate, target)
            if checked.network_sha256 != result.network_sha256:
                current = json.loads(json.dumps(candidate))
                history.append(checked)
                enriched = True
                break
        if not enriched:
            return InvestigationResult(history[-1], tuple(history), 'NO_FURTHER_ACCESS')
    result = history[-1]
    return InvestigationResult(result, tuple(history),
                               'RESOLVED_WITHIN_ACCESS' if result.value is not None else 'ACCESS_BUDGET_EXHAUSTED')
