"""Executable opt-in example; calls the real native PHI engine."""

from src.core import PhiSubstrateEngine
from src.gating import FirstDivergenceException
from src.versioned_support import VersionedQuorumGate, VersionedSupport


def main():
    engine = PhiSubstrateEngine(n_nodes=8, seed=42)
    support = VersionedSupport({'a': True, 'b': True})
    gate = VersionedQuorumGate(support, ('a', 'b'))
    engine.attach_gate(gate, support, sealed=True)
    engine.step()
    print('ACCEPTED: original PHI numerical effect')

    support.publish({'a': False, 'b': True})
    try:
        engine.step()
    except FirstDivergenceException:
        print('REFUSED: withdrawal locked real effect')
    else:
        raise AssertionError('Unsupported effect unexpectedly accepted')

    try:
        gate.trigger_reopen()
    except FirstDivergenceException:
        print('REOPEN REFUSED: no newer fully positive support')
    else:
        raise AssertionError('REOPEN unexpectedly succeeded on absent support')

    support.publish({'a': True, 'b': True})
    gate.trigger_reopen()
    engine.step()
    print('ACCEPTED: fresh published support and REOPEN')


if __name__ == '__main__':
    main()
