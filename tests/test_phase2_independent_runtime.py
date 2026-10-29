from __future__ import annotations

import base64
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from independent_runtime.identity import (
    CONTRACT_PATH,
    CONTRACT_SHA256,
    ROOT,
    canonical_json,
    compute_runtime_identity,
)
from independent_runtime.orchestrator import RuntimeOrchestrator
from independent_runtime.protocol import (
    decode_graph,
    encode_graph,
    make_request_graph,
)
from independent_runtime.store import (
    DurableRuntimeStore,
    RequestRejected,
    SimulatedCrash,
    TrustedIssuer,
)

SUPPORT_ID = "external-support:numerical-step-prerequisites"


def generate_keypair(tmp_path: Path) -> tuple[Path, str]:
    private = tmp_path / "issuer-private.pem"
    public = tmp_path / "issuer-public.pem"
    subprocess.run(
        ["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(private)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "openssl", "pkey", "-in", str(private), "-pubout", "-out",
            str(public),
        ],
        check=True,
        capture_output=True,
    )
    return private, public.read_text(encoding="ascii")


def signed_envelope(
    private: Path,
    *,
    action: str,
    request_id: str,
    nonce: str,
    key_id: str = "issuer-a",
    support_id: str = SUPPORT_ID,
    statement: str = "The issuer asserts that the stated support is present.",
    runtime_id: str | None = None,
) -> dict:
    identity = runtime_id or compute_runtime_identity()["runtime_sha256"]
    envelope = {
        "action": action,
        "request_id": request_id,
        "nonce": nonce,
        "key_id": key_id,
        "support_id": support_id,
        "statement": statement,
        "graph": encode_graph(make_request_graph(str(identity))),
    }
    payload = canonical_json(envelope)
    with subprocess.Popen(
        [
            "openssl", "pkeyutl", "-sign", "-inkey", str(private),
            "-rawin", "-in", "/dev/stdin",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as process:
        signature, stderr = process.communicate(payload, timeout=5)
        if process.returncode:
            raise RuntimeError(stderr.decode())
    return {**envelope, "signature": base64.b64encode(signature).decode("ascii")}


def create_store(tmp_path: Path):
    private, public = generate_keypair(tmp_path)
    store = DurableRuntimeStore(
        tmp_path / "runtime.sqlite",
        {"issuer-a": TrustedIssuer(public, (SUPPORT_ID,))},
    )
    return store, private, public


def test_completion_contract_is_pinned_and_frozen_docs_match():
    assert (ROOT / CONTRACT_PATH).read_bytes()
    from hashlib import sha256

    assert sha256((ROOT / CONTRACT_PATH).read_bytes()).hexdigest() == CONTRACT_SHA256
    identity = compute_runtime_identity()
    assert len(identity["runtime_sha256"]) == 64
    assert identity["sources"]["m_machine/proof_kernel.py"]


def test_runtime_identity_binds_actual_executable_and_source_bytes(tmp_path):
    identity = compute_runtime_identity()
    assert identity["python_executable_sha256"]
    assert identity["sources"]["src/core.py"]
    assert "python_executable_sha256" in identity


def test_signed_external_support_is_not_an_m_numeric_authorization(tmp_path):
    store, private, _ = create_store(tmp_path)
    publish = signed_envelope(
        private, action="support.publish", request_id="publish-1", nonce="n-1"
    )
    accepted = store.process(publish)
    assert "EXTERNAL_ASSERTION_RECORDED_NOT_TRUTH" in {
        node["ref"] for node in accepted["graph"]["nodes"]
    }
    before = store.snapshot()

    step = signed_envelope(
        private, action="numeric.step", request_id="step-1", nonce="n-2"
    )
    result = store.process(step)
    assert "fragment:decision:UNRESOLVED" in {
        node["ref"] for node in result["graph"]["nodes"]
    }
    assert result["state_before_sha256"] == result["state_after_sha256"]
    after = store.snapshot()
    assert after["state"] == before["state"]
    assert after["state_version"] == before["state_version"]
    assert result["frontier_fragment"].endswith(
        "FIRST_MECHANICAL_INFERENCE_RULE_FRONTIER"
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda e: e.update(signature=base64.b64encode(b"bad").decode()), "signature"),
        (lambda e: e.update(statement="altered after signing"), "signature"),
        (lambda e: e.update(key_id="unknown"), "issuer"),
        (lambda e: e.update(receipt={"status": "DERIVED_M"}), "fields"),
        (lambda e: e.update(graph={"raw": 1}), "fragment"),
    ],
)
def test_false_unknown_altered_and_nonfragment_inputs_reject(
    tmp_path, mutate, message
):
    store, private, _ = create_store(tmp_path)
    envelope = signed_envelope(
        private, action="numeric.step", request_id="bad-1", nonce="bad-nonce"
    )
    mutate(envelope)
    with pytest.raises(RequestRejected, match=message):
        store.process(envelope)
    assert store.snapshot()["audit_event_count"] == 0


def test_substitute_authority_or_machine_fragment_rejects(tmp_path):
    store, private, _ = create_store(tmp_path)
    for index, field in enumerate(("authority", "machine")):
        envelope = signed_envelope(
            private,
            action="numeric.step",
            request_id=f"sub-{field}",
            nonce=f"sub-nonce-{index}",
        )
        envelope["graph"][field] = f"fragment:{field}:substitute"
        payload = {key: value for key, value in envelope.items() if key != "signature"}
        payload_bytes = canonical_json(payload)
        with subprocess.Popen(
            [
                "openssl", "pkeyutl", "-sign", "-inkey",
                str(private), "-rawin", "-in", "/dev/stdin",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as process:
            signature, _ = process.communicate(payload_bytes, timeout=5)
        envelope["signature"] = base64.b64encode(signature).decode()
        with pytest.raises(RequestRejected, match="substitute"):
            store.process(envelope)


def test_nonce_replay_duplicate_idempotency_and_issuer_revocation(tmp_path):
    store, private, _ = create_store(tmp_path)
    envelope = signed_envelope(
        private, action="support.publish", request_id="pub-1", nonce="nonce-1"
    )
    first = store.process(envelope)
    assert store.process(envelope) == first

    replay = signed_envelope(
        private, action="support.publish", request_id="pub-2", nonce="nonce-1"
    )
    with pytest.raises(RequestRejected, match="replayed"):
        store.process(replay)

    store.revoke_issuer("issuer-a", "operator rotated the trust root")
    revoked = signed_envelope(
        private, action="numeric.step", request_id="step-revoked", nonce="nonce-3"
    )
    with pytest.raises(RequestRejected, match="revoked"):
        store.process(revoked)

    restarted = DurableRuntimeStore(
        store.path,
        {"issuer-a": TrustedIssuer(store.issuers["issuer-a"].public_key_pem,
                                   (SUPPORT_ID,))},
    )
    assert restarted.snapshot()["audit_event_count"] == 2


@pytest.mark.parametrize("failpoint", ["before_commit", "after_commit"])
def test_durable_decision_state_commit_recovery(tmp_path, failpoint):
    store, private, _ = create_store(tmp_path)
    envelope = signed_envelope(
        private, action="support.publish", request_id=f"crash-{failpoint}",
        nonce=f"nonce-{failpoint}",
    )
    if failpoint == "before_commit":
        with pytest.raises(SimulatedCrash, match="before commit"):
            store.process(envelope, failpoint=failpoint)
        assert store.snapshot()["audit_event_count"] == 0
        committed = store.process(envelope)
    else:
        with pytest.raises(SimulatedCrash, match="after commit"):
            store.process(envelope, failpoint=failpoint)
        restarted = DurableRuntimeStore(
            store.path,
            {"issuer-a": TrustedIssuer(store.issuers["issuer-a"].public_key_pem,
                                       (SUPPORT_ID,))},
        )
        committed = restarted.process(envelope)
        assert restarted.snapshot()["audit_event_count"] == 1
    assert "fragment:decision:" in " ".join(
        node["ref"] for node in committed["graph"]["nodes"]
    )


def test_audit_is_append_only_and_chain_detects_tampering(tmp_path):
    store, private, _ = create_store(tmp_path)
    store.process(signed_envelope(
        private, action="support.publish", request_id="audit-1", nonce="audit-n"
    ))
    import sqlite3

    db = sqlite3.connect(store.path)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("UPDATE audit_events SET event_json='{}' WHERE seq=1")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("DELETE FROM audit_events")
    db.close()
    assert store.snapshot()["audit_event_count"] == 1


def test_two_distinct_client_processes_use_local_service_and_replay_after_restart(
    tmp_path,
):
    private, public = generate_keypair(tmp_path)
    trust_path = tmp_path / "trust.json"
    trust_path.write_text(
        json.dumps({"issuers": [{
            "key_id": "issuer-a",
            "public_key_pem": public,
            "allowed_support_ids": [SUPPORT_ID],
        }]}),
        encoding="utf-8",
    )
    database = tmp_path / "service.sqlite"
    initial = DurableRuntimeStore(
        database, {"issuer-a": TrustedIssuer(public, (SUPPORT_ID,))}
    )
    runtime_id = initial.runtime_id
    publish_path = tmp_path / "publish.json"
    publish_path.write_text(json.dumps(signed_envelope(
        private, action="support.publish", request_id="client-1",
        nonce="client-nonce-1", runtime_id=runtime_id,
    )))
    step_path = tmp_path / "step.json"
    step_path.write_text(json.dumps(signed_envelope(
        private, action="numeric.step", request_id="client-2",
        nonce="client-nonce-2", runtime_id=runtime_id,
    )))

    orchestrator = RuntimeOrchestrator(database, trust_path)
    url = orchestrator.start()
    try:
        first = orchestrator.run_client(publish_path)
        second = orchestrator.run_client(step_path)
        assert first.returncode == second.returncode == 0, (
            first.stderr, second.stderr
        )
        assert first.pid != second.pid
        output = json.loads(second.stdout)
        graph = decode_graph(output["graph"])
        assert graph.validate_closed().is_closed
        assert any(
            ref.value == "fragment:decision:UNRESOLVED"
            for ref in graph.nodes
        )
        duplicate = orchestrator.run_client(step_path)
        assert duplicate.returncode == 0
    finally:
        orchestrator.stop()

    restarted = DurableRuntimeStore(
        database, {"issuer-a": TrustedIssuer(public, (SUPPORT_ID,))}
    )
    snapshot = restarted.snapshot()
    assert snapshot["audit_event_count"] == 2
    assert snapshot["state_version"] == 0
    assert snapshot["supports"][0]["active"] == 1
    assert snapshot["state"] == initial.snapshot()["state"]


def test_service_rejects_non_loopback_bind(tmp_path):
    from independent_runtime.service import LocalRuntimeServer

    store, _, _ = create_store(tmp_path)
    with pytest.raises(ValueError, match="loopback"):
        LocalRuntimeServer(("0.0.0.0", 0), store)

