"""38,880 independent native C11 versus Python versioned-quorum decisions."""

import contextlib
import csv
import io
from pathlib import Path
import shutil
import subprocess

import pytest

from src.gating import FirstDivergenceException
from src.versioned_support import VersionedQuorumGate, VersionedSupport


def test_c11_exhaustive_versioned_quorum_oracle(tmp_path):
    cc = shutil.which('cc') or shutil.which('clang') or shutil.which('gcc')
    if cc is None:
        pytest.skip('No C11 compiler available')
    root = Path(__file__).resolve().parents[1]
    program = tmp_path / 'c11_versioned_quorum'
    subprocess.run([cc, '-std=c11', '-O2', '-Wall', '-Wextra', '-Wpedantic',
                    '-Werror', str(root/'verification/c11/versioned_quorum_oracle.c'),
                    '-o', str(program)], check=True, capture_output=True, text=True)
    native = subprocess.run([str(program)], check=True, capture_output=True, text=True)
    assert 'C11_VERSIONED_QUORUM_PASS sequences=7776 rows=38880' in native.stderr
    prev = -1
    rows = 0
    for row in csv.DictReader(io.StringIO(native.stdout)):
        sequence, event = int(row['sequence']), int(row['event'])
        if sequence != prev:
            assert sequence == prev + 1
            prev = sequence
            source = VersionedSupport({'a': True, 'b': True})
            gate = VersionedQuorumGate(source, ('a', 'b'))
        expected = row['result']
        if event in (1, 2, 3):
            assert expected == 'P'
            source.publish({'a': event != 2, 'b': event != 3})
        elif event == 4:
            if expected == 'R':
                gate.trigger_reopen()
            else:
                with pytest.raises(FirstDivergenceException) as error:
                    gate.trigger_reopen()
                assert ('prior refusal' if expected == 'O' else 'no newer positive') in str(error.value)
        elif expected == 'A':
            gate.check_trajectory({'a': False, 'b': False}, int(row['step']))
        else:
            with pytest.raises(FirstDivergenceException) as error:
                gate.check_trajectory({'a': True, 'b': True}, int(row['step']))
            if expected == 'L':
                assert 'locked' in str(error.value)
            elif expected == 'D':
                assert 'Constraints violated' in str(error.value)
            else:
                pytest.fail(f'Unexpected oracle decision {expected}')
        assert int(gate.execution_locked) == int(row['locked'])
        assert source.read_revision()[0] == int(row['revision'])
        assert (-1 if gate.rejected_revision is None else gate.rejected_revision) == int(row['rejected'])
        rows += 1
    assert rows == 38880
