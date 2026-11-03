"""Opt-in gate example. Synchronized support is in-process only.

Run: python -m examples.synchronized_gate
"""
from src.core import PhiSubstrateEngine
from src.effect_authorization import SynchronizedSupport
from src.gating import MultiAccessGating, FirstDivergenceException

support=SynchronizedSupport({'present': True})
gate=MultiAccessGating(lambda evidence: evidence['present'])
engine=PhiSubstrateEngine(n_nodes=6, seed=42)
engine.attach_gate(gate,support)
accepted=engine.step()
assert accepted['representation_status']
support.publish({'present':False})
try:
    engine.step()
except FirstDivergenceException:
    assert gate.execution_locked
else:
    raise AssertionError('Withdrawn support was not refused')
support.publish({'present':True})
gate.trigger_reopen()  # does NOT verify a new independent interval
engine.step()
print('example completed: accepted / refused / manually reopened')
