from __future__ import annotations

import base64
import inspect
import json
from hashlib import sha256
from pathlib import Path
import subprocess
import sqlite3
import tempfile

import numpy as np
import pytest

from independent_runtime.identity import canonical_json, compute_runtime_identity
from independent_runtime.protocol import decode_graph, encode_graph, make_request_graph
from independent_runtime.store import (
    DurableRuntimeStore, RequestRejected, SimulatedCrash, TrustedIssuer,
)
from src.core import PhiSubstrateEngine

NAMES = ("sigma", "alpha", "beta", "lmbda", "gamma", "mu", "eta")
SCOPE = "PhiSubstrateEngine.parameter."


def _keypair(tmp_path):
    private, public = tmp_path / "private.pem", tmp_path / "public.pem"
    subprocess.run(["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(private)], check=True)
    subprocess.run(["openssl", "pkey", "-in", str(private), "-pubout", "-out", str(public)], check=True)
    return private, public.read_text()


def _sign(private, payload):
    with tempfile.TemporaryDirectory() as directory:
        message, signature = Path(directory) / "m", Path(directory) / "s"
        message.write_bytes(canonical_json(payload))
        subprocess.run(
            ["openssl", "pkeyutl", "-sign", "-inkey", str(private), "-rawin",
             "-in", str(message), "-out", str(signature)], check=True
        )
        return base64.b64encode(signature.read_bytes()).decode()


def _setup(tmp_path, values):
    private, public = _keypair(tmp_path)
    support_ids = tuple(f"dep:{name}" for name in NAMES) + ("equations:step",)
    store = DurableRuntimeStore(
        tmp_path / "runtime.sqlite", {"issuer-a": TrustedIssuer(public, support_ids)}
    )
    model_hash = sha256(inspect.getsource(PhiSubstrateEngine).encode()).hexdigest()
    source_hash = store.identity["sources"]["src/core.py"]
    dependencies = []
    for name in NAMES:
        support_id = f"dep:{name}"
        claim = {
            "name": name, "value": values[name], "scope": SCOPE + name,
            "model_sha256": model_hash, "source_sha256": source_hash,
        }
        statement = canonical_json(claim).decode()
        publish = {
            "action": "support.publish", "request_id": f"pub-{name}",
            "nonce": f"nonce-pub-{name}", "key_id": "issuer-a",
            "support_id": support_id, "statement": statement,
            "graph": encode_graph(make_request_graph(store.runtime_id)),
        }
        publish["signature"] = _sign(private, publish)
        store.process(publish)
        dependencies.append({
            **claim, "support_id": support_id, "revision": 1,
            "assertion_statement": statement,
        })
    return store, private, model_hash, source_hash, dependencies


def _request(store, private, dependencies, *, state=None, version=None, progress=1.0):
    snapshot = store.snapshot()
    manifest = {
        "expected_state_sha256": state or snapshot["state_sha256"],
        "expected_state_version": snapshot["state_version"] if version is None else version,
        "mechanical_progress": progress,
        "dependencies": dependencies,
    }
    envelope = {
        "action": "equations.step.attested", "request_id": "equations-step",
        "nonce": "equations-nonce", "key_id": "issuer-a",
        "support_id": "equations:step",
        "statement": canonical_json(manifest).decode(),
        "graph": encode_graph(make_request_graph(store.runtime_id)),
    }
    envelope["signature"] = _sign(private, envelope)
    return envelope


def _control(store, private, action, request_id, nonce, support_id, statement="test"):
    envelope = {
        "action": action, "request_id": request_id, "nonce": nonce,
        "key_id": "issuer-a", "support_id": support_id, "statement": statement,
        "graph": encode_graph(make_request_graph(store.runtime_id)),
    }
    envelope["signature"] = _sign(private, envelope)
    return envelope


def _values(mu):
    return {"sigma": 1.2, "alpha": 0.04, "beta": 0.25, "lmbda": 0.01,
            "gamma": 0.3, "mu": mu, "eta": 0.01}


def _install_independently_reported_state(store):
    state = {
        "pos": [[-1.0, 0.0], [1.0, 0.0]],
        "S": [[2.0, 1.0, 0.5], [1.1, 2.0, 0.7]],
        "R": [0.1, 0.2],
    }
    encoded = canonical_json(state).decode()
    with sqlite3.connect(store.path) as db:
        db.execute(
            "UPDATE numeric_state SET state_json=?,state_sha256=?,version=0 WHERE id=1",
            (encoded, sha256(encoded.encode()).hexdigest()),
        )
    return state


def test_attested_two_node_step_matches_original_engine(tmp_path):
    values = _values(0.05)
    store, private, model_hash, source_hash, dependencies = _setup(tmp_path, values)
    initial = _install_independently_reported_state(store)
    before = store.snapshot()
    request = _request(store, private, dependencies)
    result = store.process(request)
    reference = PhiSubstrateEngine(n_nodes=2, seed=13, **values)
    reference.pos = np.asarray(before["state"]["pos"])
    reference.S = np.asarray(before["state"]["S"])
    reference.R = np.asarray(before["state"]["R"])
    reference.step()
    assert result["m_status"] == "UNRESOLVED"
    assert result["status"] == "EQUATIONS_EXECUTED_EXTERNAL_ATTESTATIONS_NOT_M_AUTHORIZATION"
    assert result["dependencies_used"][0]["model_sha256"] == model_hash
    assert result["dependencies_used"][0]["source_sha256"] == source_hash
    assert result["state_before_sha256"] == before["state_sha256"]
    assert result["state_after"] == {
        "pos": reference.pos.tolist(), "S": reference.S.tolist(), "R": reference.R.tolist()
    }
    assert result["state_after"]["S"][0][0] - initial["S"][0][0] == pytest.approx(
        -0.002733781888455633, abs=1e-15
    )
    assert sum(row[0] for row in result["state_after"]["S"]) == pytest.approx(3.1)
    assert result["state_version_after"] == before["state_version"] + 1
    assert store.process(request) == result
    assert store.snapshot()["state_version"] == 1
    output_graph = decode_graph(result["graph"])
    assert output_graph.validate_closed().is_closed
    assert any(
        ref.value.startswith("fragment:dependency:mu:provenance")
        for ref in output_graph.path
    )
    assert any(ref.value.startswith("fragment:transformation:") for ref in output_graph.path)
    assert any(ref.value == "fragment:dependency:mu:issuer_key_id:issuer-a"
               for ref in output_graph.nodes)
    assert any(ref.value == "fragment:execution:mechanical-progress:1.0"
               for ref in output_graph.path)
    assert any(ref.value == "fragment:execution:state-version-after:1"
               for ref in output_graph.path)
    assert any(ref.value.startswith("fragment:dependency:mu:assertion_sha256:")
               for ref in output_graph.nodes)


def test_known_zero_mu_does_not_block_independent_geometry_change(tmp_path):
    values = _values(0.0)
    store, private, _, _, dependencies = _setup(tmp_path, values)
    _install_independently_reported_state(store)
    before = store.snapshot()
    result = store.process(_request(store, private, dependencies))
    assert next(d for d in result["dependencies_used"] if d["name"] == "mu")["value"] == 0.0
    assert result["state_after"]["pos"] != before["state"]["pos"]
    assert result["state_after"]["S"] == before["state"]["S"]


@pytest.mark.parametrize(
    "mutation",
    ["missing", "value", "scope", "model", "source", "revision", "state", "issuer"],
)
def test_invalid_or_unavailable_dependency_rejects_without_state_change(tmp_path, mutation):
    store, private, _, _, dependencies = _setup(tmp_path, _values(0.05))
    before = store.snapshot()
    items = [dict(item) for item in dependencies]
    if mutation == "missing":
        items.pop()
    elif mutation == "value":
        items[0]["value"] += 1
    elif mutation == "scope":
        items[0]["scope"] = "wrong"
    elif mutation == "model":
        items[0]["model_sha256"] = "0" * 64
    elif mutation == "source":
        items[0]["source_sha256"] = "0" * 64
    elif mutation == "revision":
        items[0]["revision"] += 1
    elif mutation == "issuer":
        items[0]["support_id"] = "not-allowlisted"
    error = RequestRejected
    kwargs = {}
    if mutation == "state":
        kwargs["state"] = "0" * 64
    with pytest.raises(error):
        store.process(_request(store, private, items, **kwargs))
    assert store.snapshot()["state_sha256"] == before["state_sha256"]
    assert store.snapshot()["state_version"] == before["state_version"]


@pytest.mark.parametrize("failpoint", ["before_commit", "after_commit"])
def test_attested_step_transaction_recovers_before_or_after_commit(tmp_path, failpoint):
    store, private, _, _, dependencies = _setup(tmp_path, _values(0.05))
    _install_independently_reported_state(store)
    request = _request(store, private, dependencies)
    before = store.snapshot()
    if failpoint == "before_commit":
        with pytest.raises(SimulatedCrash, match="before commit"):
            store.process(request, failpoint=failpoint)
        assert store.snapshot()["state_sha256"] == before["state_sha256"]
        result = store.process(request)
    else:
        with pytest.raises(SimulatedCrash, match="after commit"):
            store.process(request, failpoint=failpoint)
        result = store.process(request)
    assert store.snapshot()["state_version"] == 1
    assert result["state_version_after"] == 1


def test_reentrant_dependency_revocation_discards_provisional_calculation(
    tmp_path, monkeypatch
):
    store, private, _, _, dependencies = _setup(tmp_path, _values(0.05))
    before = store.snapshot()
    request = _request(store, private, dependencies)
    revoke = _control(
        store, private, "support.revoke", "revoke-mu", "revoke-mu-nonce", "dep:mu"
    )
    original_step = PhiSubstrateEngine.step
    retained = {}

    def revoke_inside_calculation(engine, mechanical_progress=1.0):
        retained["arrays"] = (engine.pos, engine.S, engine.R)
        retained["before"] = (engine.pos.copy(), engine.S.copy(), engine.R.copy())
        store.process(revoke)
        return original_step(engine, mechanical_progress)

    monkeypatch.setattr(PhiSubstrateEngine, "step", revoke_inside_calculation)
    with pytest.raises(RequestRejected, match="dependency missing, changed, or revoked: mu"):
        store.process(request)
    after = store.snapshot()
    assert after["state_sha256"] == before["state_sha256"]
    assert after["state_version"] == before["state_version"]
    assert after["supports"][[s["support_id"] for s in after["supports"]].index("dep:mu")]["active"] == 0
    assert all(array is not None for array in retained["arrays"])


def test_calculation_error_discards_candidate_and_preserves_durable_arrays(
    tmp_path, monkeypatch
):
    store, private, _, _, dependencies = _setup(tmp_path, _values(0.05))
    _install_independently_reported_state(store)
    before = store.snapshot()
    request = _request(store, private, dependencies)
    retained = {}

    def mutate_then_fail(engine, mechanical_progress=1.0):
        retained["refs"] = (engine.pos, engine.S, engine.R)
        retained["ids"] = tuple(map(id, retained["refs"]))
        engine.pos[0, 0] += 123.0
        raise RuntimeError("injected calculation failure")

    monkeypatch.setattr(PhiSubstrateEngine, "step", mutate_then_fail)
    with pytest.raises(RuntimeError, match="injected calculation failure"):
        store.process(request)
    after = store.snapshot()
    assert after["state"] == before["state"]
    assert after["state_sha256"] == before["state_sha256"]
    assert after["state_version"] == before["state_version"]
    assert tuple(map(id, retained["refs"])) == retained["ids"]


def test_overflow_candidate_is_rejected_without_publishing(tmp_path):
    store, private, _, _, dependencies = _setup(tmp_path, _values(1e308))
    _install_independently_reported_state(store)
    before = store.snapshot()
    with np.errstate(all="ignore"):
        with pytest.raises(RequestRejected, match="non-finite"):
            store.process(_request(store, private, dependencies))
    assert store.snapshot() == before


def test_actual_initial_bytes_must_match_signed_hash(tmp_path):
    store, private, _, _, dependencies = _setup(tmp_path, _values(.05))
    request = _request(store, private, dependencies)
    before = store.snapshot()
    corrupted = before["state"]
    corrupted["S"][0][0] += 1
    with sqlite3.connect(store.path) as db:
        db.execute("UPDATE numeric_state SET state_json=? WHERE id=1",
                   (canonical_json(corrupted).decode(),))
    with pytest.raises(RequestRejected, match="hash|invalid"):
        store.process(request)
    with sqlite3.connect(store.path) as db:
        assert db.execute("SELECT version FROM numeric_state").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM requests WHERE request_id='equations-step'").fetchone()[0] == 0


def test_concurrent_duplicate_returns_same_committed_result(tmp_path, monkeypatch):
    from threading import Barrier
    from concurrent.futures import ThreadPoolExecutor
    store, private, _, _, dependencies = _setup(tmp_path, _values(.05))
    request = _request(store, private, dependencies)
    rendezvous = Barrier(2)
    original = PhiSubstrateEngine.step

    def together(engine, mechanical_progress=1.):
        rendezvous.wait(timeout=5)
        return original(engine, mechanical_progress)

    monkeypatch.setattr(PhiSubstrateEngine, "step", together)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = [future.result(timeout=10) for future in
                         [pool.submit(store.process, request), pool.submit(store.process, request)]]
    assert first == second
    assert store.snapshot()["state_version"] == 1


def test_two_real_http_clients_execute_successive_attested_steps(tmp_path):
    from independent_runtime.orchestrator import RuntimeOrchestrator
    store, private, _, _, dependencies = _setup(tmp_path, _values(.05))
    issuer = store.issuers["issuer-a"]
    trust = tmp_path / "trust.json"
    trust.write_text(json.dumps({"issuers": [{"key_id": "issuer-a",
        "public_key_pem": issuer.public_key_pem,
        "allowed_support_ids": list(issuer.allowed_support_ids)}]}))
    orchestrator = RuntimeOrchestrator(store.path, trust)
    orchestrator.start()
    try:
        requests = []
        runs = []
        for number in range(2):
            request = _request(store, private, dependencies)
            request.update(request_id=f"http-step-{number}", nonce=f"http-nonce-{number}")
            request["signature"] = _sign(private, {k:v for k,v in request.items() if k != "signature"})
            path = tmp_path / f"step-{number}.json"
            path.write_text(json.dumps(request))
            result = orchestrator.run_client(path)
            assert result.returncode == 0, result.stderr
            graph = decode_graph(json.loads(result.stdout)["graph"])
            assert any(ref.value == "fragment:decision:EQUATIONS_EXECUTED_NOT_M_AUTHORIZED"
                       for ref in graph.nodes)
            runs.append(result)
            requests.append(request)
        assert runs[0].pid != runs[1].pid
        assert store.snapshot()["state_version"] == 2
        # A newly signed request bound to the first state must fail.
        stale = dict(requests[0])
        stale.update(request_id="http-stale", nonce="http-stale-nonce")
        stale["signature"] = _sign(private, {k:v for k,v in stale.items() if k != "signature"})
        with pytest.raises(RequestRejected, match="state or revision changed"):
            store.process(stale)
    finally:
        orchestrator.stop()
    restarted = DurableRuntimeStore(store.path, store.issuers)
    assert restarted.snapshot()["state_version"] == 2


def test_reentrant_state_change_discards_stale_outer_calculation(tmp_path, monkeypatch):
    store, private, _, _, dependencies = _setup(tmp_path, _values(.05))
    outer = _request(store, private, dependencies)
    inner = dict(outer)
    inner.update(request_id="inner-step", nonce="inner-nonce")
    inner["signature"] = _sign(private, {k:v for k,v in inner.items() if k != "signature"})
    original = PhiSubstrateEngine.step
    committed = {}

    def advance_during_calculation(engine, mechanical_progress=1.):
        if not committed:
            committed["started"] = True
            committed["result"] = store.process(inner)
        return original(engine, mechanical_progress)

    monkeypatch.setattr(PhiSubstrateEngine, "step", advance_during_calculation)
    with pytest.raises(RequestRejected, match="state or revision changed"):
        store.process(outer)
    assert store.snapshot()["state_version"] == 1
    assert store.snapshot()["state_sha256"] == committed["result"]["state_after_sha256"]
