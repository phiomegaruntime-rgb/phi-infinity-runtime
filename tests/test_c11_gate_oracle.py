"""Exhaustive 4^5 independent C11 transition oracle versus actual Python gate."""
import contextlib
import csv
import io
from pathlib import Path
import shutil
import subprocess

import pytest

from src.gating import FirstDivergenceException, MultiAccessGating


def test_native_c11_oracle_replay_against_real_python_gate(tmp_path):
    compiler = shutil.which('cc') or shutil.which('clang') or shutil.which('gcc')
    if compiler is None:
        pytest.skip('C11 compiler unavailable (Python gate regressions still run)')
    root=Path(__file__).resolve().parents[1]
    src=root/'verification/c11/gate_transition_oracle.c'
    executable=tmp_path/'phi_gate_oracle'
    subprocess.run([compiler,'-std=c11','-O2','-Wall','-Wextra','-Wpedantic',
                    '-Werror',str(src),'-o',str(executable)],
                   check=True,capture_output=True,text=True)
    run=subprocess.run([str(executable)],check=True,capture_output=True,text=True)
    assert 'C11_ORACLE_PASS sequences=1024 rows=5120' in run.stderr
    seq_old=-1
    rows=0
    gate=None
    for row in csv.DictReader(io.StringIO(run.stdout)):
        seq=int(row['sequence']);step=int(row['step']);event=int(row['event'])
        expected=row['result']; locked=bool(int(row['locked']))
        if seq!=seq_old:
            seq_old=seq
            assert step==0
            def pred(value):
                if value['raise_predicate']:
                    raise RuntimeError('predicate failure')
                return value['supported']
            gate=MultiAccessGating(pred)
        if event==2:
            with contextlib.redirect_stdout(io.StringIO()):gate.trigger_reopen()
            assert expected=='R'
        elif expected=='A':
            assert gate.check_trajectory({'supported':True,'raise_predicate':False},step) is None
        else:
            with pytest.raises(FirstDivergenceException) as err:
                gate.check_trajectory({'supported':event==0,
                                       'raise_predicate':event==3},step)
            if expected=='E':assert isinstance(err.value.__cause__,RuntimeError)
            if expected=='L':assert 'locked' in str(err.value)
            if expected=='D':assert 'Constraints violated' in str(err.value)
        assert gate.execution_locked==locked
        rows+=1
    assert rows==5120
