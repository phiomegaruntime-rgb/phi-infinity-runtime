from __future__ import annotations

import base64
from dataclasses import dataclass
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
from typing import Any, Mapping

from m_machine.proof_kernel import (
    FIRST_MECHANICAL_INFERENCE_RULE_FRONTIER,
    ProofKernel,
)
from src.core import PhiSubstrateEngine

from .identity import (
    FROZEN_SOURCE_HASHES,
    canonical_json,
    compute_runtime_identity,
)
from .protocol import (
    FragmentProtocolError,
    decode_graph,
    encode_graph,
    make_request_graph,
    make_unresolved_output,
)


class RequestRejected(ValueError):
    pass


class SimulatedCrash(RuntimeError):
    pass


@dataclass(frozen=True)
class TrustedIssuer:
    public_key_pem: str
    allowed_support_ids: tuple[str, ...]


ENVELOPE_FIELDS = {
    "action", "request_id", "nonce", "key_id", "support_id",
    "statement", "graph", "signature",
}
ALLOWED_ACTIONS = {"support.publish", "support.revoke", "numeric.step"}


def _verify_ed25519(public_pem: str, message: bytes, signature: bytes) -> bool:
    with tempfile.TemporaryDirectory(prefix="phi-verify-") as temp:
        root = Path(temp)
        pub = root / "issuer.pem"
        msg = root / "message.bin"
        sig = root / "signature.bin"
        pub.write_text(public_pem, encoding="ascii")
        msg.write_bytes(message)
        sig.write_bytes(signature)
        result = subprocess.run(
            [
                "openssl", "pkeyutl", "-verify", "-pubin", "-inkey",
                str(pub), "-rawin", "-in", str(msg), "-sigfile", str(sig),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=5,
        )
        return result.returncode == 0


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=10, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=FULL")
    return connection


class DurableRuntimeStore:
    """SQLite decision/state transaction with immutable hash-chained audit.

    The M kernel is fixed in-process and has no positive mechanical rules.
    Consequently numeric.step is always UNRESOLVED and never changes arrays.
    """

    def __init__(
        self,
        database: str | Path,
        trusted_issuers: Mapping[str, TrustedIssuer],
    ) -> None:
        self.path = Path(database).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.identity = compute_runtime_identity()
        self.runtime_id = str(self.identity["runtime_sha256"])
        self.issuers = dict(trusted_issuers)
        self.trust_config_sha256 = sha256(
            canonical_json({
                key: {
                    "public_key_pem_sha256": sha256(
                        issuer.public_key_pem.encode("ascii")
                    ).hexdigest(),
                    "allowed_support_ids": list(issuer.allowed_support_ids),
                }
                for key, issuer in sorted(self.issuers.items())
            })
        ).hexdigest()
        self._initialize()

    def _initialize(self) -> None:
        engine = PhiSubstrateEngine(n_nodes=2, seed=13)
        state = {
            name: getattr(engine, name).tolist()
            for name in ("pos", "S", "R")
        }
        state_json = canonical_json(state).decode("utf-8")
        with _connect(self.path) as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS runtime_meta(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS numeric_state(
                    id INTEGER PRIMARY KEY CHECK(id=1),
                    state_json TEXT NOT NULL,
                    state_sha256 TEXT NOT NULL,
                    version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS requests(
                    request_id TEXT PRIMARY KEY,
                    envelope_sha256 TEXT NOT NULL,
                    envelope_json TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    state_version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS used_nonces(
                    issuer_key_id TEXT NOT NULL,
                    nonce TEXT NOT NULL,
                    request_id TEXT NOT NULL UNIQUE,
                    PRIMARY KEY(issuer_key_id, nonce)
                );
                CREATE TABLE IF NOT EXISTS support_state(
                    support_id TEXT PRIMARY KEY,
                    active INTEGER NOT NULL,
                    assertion_sha256 TEXT NOT NULL,
                    issuer_key_id TEXT NOT NULL,
                    revision INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS issuer_keys(
                    key_id TEXT PRIMARY KEY,
                    public_key_pem TEXT NOT NULL,
                    allowed_support_ids_json TEXT NOT NULL,
                    revoked INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS audit_events(
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_json TEXT NOT NULL,
                    previous_sha256 TEXT NOT NULL,
                    event_sha256 TEXT NOT NULL UNIQUE
                );
                CREATE TRIGGER IF NOT EXISTS audit_no_update
                BEFORE UPDATE ON audit_events BEGIN
                    SELECT RAISE(ABORT, 'audit is append-only');
                END;
                CREATE TRIGGER IF NOT EXISTS audit_no_delete
                BEFORE DELETE ON audit_events BEGIN
                    SELECT RAISE(ABORT, 'audit is append-only');
                END;
                CREATE TRIGGER IF NOT EXISTS requests_no_update
                BEFORE UPDATE ON requests BEGIN
                    SELECT RAISE(ABORT, 'requests are immutable');
                END;
                CREATE TRIGGER IF NOT EXISTS requests_no_delete
                BEFORE DELETE ON requests BEGIN
                    SELECT RAISE(ABORT, 'requests are immutable');
                END;
                CREATE TRIGGER IF NOT EXISTS nonce_no_update
                BEFORE UPDATE ON used_nonces BEGIN
                    SELECT RAISE(ABORT, 'nonce history is immutable');
                END;
                CREATE TRIGGER IF NOT EXISTS nonce_no_delete
                BEFORE DELETE ON used_nonces BEGIN
                    SELECT RAISE(ABORT, 'nonce history is immutable');
                END;
                """
            )
            db.execute(
                "INSERT OR IGNORE INTO numeric_state"
                "(id,state_json,state_sha256,version) VALUES(1,?,?,0)",
                (state_json, sha256(state_json.encode()).hexdigest()),
            )
            pinned = {
                "runtime_id": self.runtime_id,
                "trust_config_sha256": self.trust_config_sha256,
            }
            for key, value in pinned.items():
                row = db.execute(
                    "SELECT value FROM runtime_meta WHERE key=?", (key,)
                ).fetchone()
                if row is None:
                    db.execute(
                        "INSERT INTO runtime_meta(key,value) VALUES(?,?)",
                        (key, value),
                    )
                elif row["value"] != value:
                    raise RequestRejected(
                        f"persistent database {key} does not match runtime"
                    )
            for key_id, issuer in sorted(self.issuers.items()):
                allowed = canonical_json(
                    list(issuer.allowed_support_ids)
                ).decode()
                row = db.execute(
                    "SELECT public_key_pem,allowed_support_ids_json "
                    "FROM issuer_keys WHERE key_id=?", (key_id,)
                ).fetchone()
                if row is None:
                    db.execute(
                        "INSERT INTO issuer_keys"
                        "(key_id,public_key_pem,allowed_support_ids_json,revoked) "
                        "VALUES(?,?,?,0)",
                        (key_id, issuer.public_key_pem, allowed),
                    )
                elif (
                    row["public_key_pem"] != issuer.public_key_pem
                    or row["allowed_support_ids_json"] != allowed
                ):
                    raise RequestRejected(
                        f"issuer configuration changed for {key_id}"
                    )
            state_row = db.execute(
                "SELECT state_json,state_sha256 FROM numeric_state WHERE id=1"
            ).fetchone()
            try:
                state_digest = sha256(
                    canonical_json(json.loads(state_row["state_json"]))
                ).hexdigest()
            except (TypeError, ValueError, KeyError) as exc:
                raise RequestRejected("durable numerical state is malformed") from exc
            if state_digest != state_row["state_sha256"]:
                raise RequestRejected("durable numerical state hash mismatch")
            self._verify_audit_chain(db)

    @staticmethod
    def _verify_audit_chain(db: sqlite3.Connection) -> None:
        previous = "0" * 64
        for row in db.execute(
            "SELECT event_json,previous_sha256,event_sha256 "
            "FROM audit_events ORDER BY seq"
        ):
            actual = sha256(
                previous.encode("ascii") + row["event_json"].encode("utf-8")
            ).hexdigest()
            if row["previous_sha256"] != previous or row["event_sha256"] != actual:
                raise RequestRejected("append-only audit integrity check failed")
            previous = actual

    @staticmethod
    def _append_audit(db: sqlite3.Connection, event: dict[str, Any]) -> str:
        previous_row = db.execute(
            "SELECT event_sha256 FROM audit_events ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        previous = previous_row["event_sha256"] if previous_row else "0" * 64
        event_json = canonical_json(event).decode("utf-8")
        digest = sha256(previous.encode("ascii") + event_json.encode()).hexdigest()
        db.execute(
            "INSERT INTO audit_events(event_json,previous_sha256,event_sha256) "
            "VALUES(?,?,?)",
            (event_json, previous, digest),
        )
        return digest

    def _proof_frontier(self) -> tuple[str, str]:
        kernel = ProofKernel(repository_root=Path(__file__).resolve().parents[1])
        if kernel.registry.mechanical_rule_count != 0:
            raise RequestRejected(
                "unexpected mechanical rule registry; fail closed"
            )
        authority_hash = FROZEN_SOURCE_HASHES[
            "docs/UNIVERSAL_MOTHER_MECHANICS_AMENDMENT_05_OPERATIONAL_DERIVATION_SEMANTICS_PROOF_KERNEL.md"
        ]
        result = kernel.close(
            receipts=(),
            scope=(("target", "protected-numerical-step"),),
            target="authorization for protected numerical state advancement",
            authority_range="Amendment 05 §§2 and 10",
            authority_range_hash=authority_hash,
        )
        if result.status != "UNRESOLVED" or result.new_derived_m_count:
            raise RequestRejected("unexpected M-kernel result; fail closed")
        if result.frontier != FIRST_MECHANICAL_INFERENCE_RULE_FRONTIER:
            raise RequestRejected("unexpected M frontier; fail closed")
        unresolved = result.state.unresolved_targets[0]
        return result.frontier, unresolved.reason

    def process(self, envelope: object, *, failpoint: str | None = None) -> dict[str, Any]:
        if type(envelope) is not dict or set(envelope) != ENVELOPE_FIELDS:
            raise RequestRejected("request envelope fields are not exact")
        try:
            graph = decode_graph(envelope["graph"])
        except FragmentProtocolError as exc:
            raise RequestRejected(str(exc)) from exc
        if graph.authority.value != f"fragment:authority:{self.runtime_id}":
            raise RequestRejected("substitute authority fragment")
        if graph.machine.value != f"fragment:machine:{self.runtime_id}":
            raise RequestRejected("substitute machine fragment")
        if graph.target.value != "fragment:target:numerical-step":
            raise RequestRejected("wrong target fragment")
        expected_graph = encode_graph(make_request_graph(self.runtime_id))
        if encode_graph(graph) != expected_graph:
            raise RequestRejected("request graph contains substituted fragments")

        action = envelope["action"]
        request_id = envelope["request_id"]
        nonce = envelope["nonce"]
        key_id = envelope["key_id"]
        support_id = envelope["support_id"]
        statement = envelope["statement"]
        if type(action) is not str or action not in ALLOWED_ACTIONS:
            raise RequestRejected("unknown action")
        for label, value in (("request_id", request_id), ("nonce", nonce),
                             ("key_id", key_id), ("support_id", support_id),
                             ("statement", statement)):
            if type(value) is not str or not value.strip() or len(value) > 512:
                raise RequestRejected(f"invalid {label}")
        if support_id not in self.issuers.get(
            key_id, TrustedIssuer("", ())
        ).allowed_support_ids:
            raise RequestRejected("unknown issuer or unauthorized support scope")
        try:
            signature = base64.b64decode(envelope["signature"], validate=True)
        except Exception as exc:
            raise RequestRejected("invalid signature encoding") from exc
        payload = {key: value for key, value in envelope.items() if key != "signature"}
        payload_bytes = canonical_json(payload)
        envelope_hash = sha256(canonical_json(envelope)).hexdigest()
        issuer = self.issuers[key_id]
        if not _verify_ed25519(issuer.public_key_pem, payload_bytes, signature):
            raise RequestRejected("Ed25519 signature verification failed")

        frontier, reason = self._proof_frontier()
        with _connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT envelope_sha256,response_json FROM requests "
                "WHERE request_id=?", (request_id,)
            ).fetchone()
            if existing:
                if existing["envelope_sha256"] != envelope_hash:
                    db.rollback()
                    raise RequestRejected("request_id reused with different bytes")
                db.commit()
                return json.loads(existing["response_json"])
            active_issuer = db.execute(
                "SELECT revoked FROM issuer_keys WHERE key_id=?", (key_id,)
            ).fetchone()
            if active_issuer is None or active_issuer["revoked"]:
                db.rollback()
                raise RequestRejected("issuer key is revoked or unknown")
            replay = db.execute(
                "SELECT 1 FROM used_nonces WHERE issuer_key_id=? AND nonce=?",
                (key_id, nonce),
            ).fetchone()
            if replay:
                db.rollback()
                raise RequestRejected("replayed issuer nonce")

            state_row = db.execute(
                "SELECT state_json,state_sha256,version FROM numeric_state WHERE id=1"
            ).fetchone()
            before_hash = state_row["state_sha256"]
            outcome = "UNRESOLVED"
            receipt_id = sha256(
                canonical_json({
                    "request_id": request_id,
                    "envelope_sha256": envelope_hash,
                    "frontier": frontier,
                    "reason": reason,
                })
            ).hexdigest()

            if action == "support.publish":
                assertion_hash = sha256(
                    canonical_json({"support_id": support_id, "statement": statement})
                ).hexdigest()
                row = db.execute(
                    "SELECT revision FROM support_state WHERE support_id=?",
                    (support_id,),
                ).fetchone()
                revision = row["revision"] + 1 if row else 1
                db.execute(
                    "INSERT INTO support_state VALUES(?,?,?,?,?) "
                    "ON CONFLICT(support_id) DO UPDATE SET active=1,"
                    "assertion_sha256=excluded.assertion_sha256,"
                    "issuer_key_id=excluded.issuer_key_id,"
                    "revision=excluded.revision",
                    (support_id, 1, assertion_hash, key_id, revision),
                )
                outcome = "EXTERNAL_ASSERTION_RECORDED_NOT_TRUTH"
            elif action == "support.revoke":
                row = db.execute(
                    "SELECT active,revision FROM support_state WHERE support_id=?",
                    (support_id,),
                ).fetchone()
                if row is None or not row["active"]:
                    db.rollback()
                    raise RequestRejected("support is absent or already revoked")
                revision = row["revision"] + 1
                db.execute(
                    "UPDATE support_state SET active=0,revision=? "
                    "WHERE support_id=?",
                    (revision, support_id),
                )
                outcome = "EXTERNAL_ASSERTION_REVOKED"
            else:
                row = db.execute(
                    "SELECT active,revision FROM support_state WHERE support_id=?",
                    (support_id,),
                ).fetchone()
                if row is None or not row["active"]:
                    db.rollback()
                    raise RequestRejected("required support is missing or revoked")

            current_state = db.execute(
                "SELECT state_json,state_sha256,version FROM numeric_state WHERE id=1"
            ).fetchone()
            state_version = current_state["version"]
            support_row = db.execute(
                "SELECT active,assertion_sha256,revision FROM support_state "
                "WHERE support_id=?",
                (support_id,),
            ).fetchone()
            source_path_hash = str(
                self.identity["sources"]["src/core.py"]
            )
            entrypoint_hash = sha256(
                inspect.getsource(PhiSubstrateEngine.step).encode("utf-8")
            ).hexdigest()
            stages = {
                "conceptual": {
                    "status": "UNRESOLVED",
                    "target": "authorization for protected numerical state advancement",
                    "missing_premise": reason,
                },
                "operational_path": {
                    "status": "IDENTIFIED_NOT_AUTHORIZED",
                    "entrypoint": "src.core.PhiSubstrateEngine.step",
                    "source_file_sha256": source_path_hash,
                    "entrypoint_source_sha256": entrypoint_hash,
                },
                "numerical": {
                    "status": "NOT_EXECUTED",
                    "state_before_sha256": before_hash,
                    "state_after_sha256": current_state["state_sha256"],
                    "reason": "M authorization is UNRESOLVED; no state was changed",
                },
            }
            decision_text = {
                "support.publish": "EXTERNAL_ASSERTION_RECORDED_NOT_TRUTH",
                "support.revoke": "SUPPORT_REVOKED",
                "numeric.step": "UNRESOLVED",
            }[action]
            response_graph = make_unresolved_output(
                graph, receipt_id, decision_text
            )
            response = {
                "graph": encode_graph(response_graph),
                "outcome_fragment": f"fragment:decision:{outcome}",
                "frontier_fragment": f"fragment:frontier:{frontier}",
                "reason_fragment": f"fragment:reason:{sha256(reason.encode()).hexdigest()}",
                "state_before_sha256": before_hash,
                "state_after_sha256": current_state["state_sha256"],
                "state_version": state_version,
                "receipt_fragment": f"fragment:receipt:{receipt_id}",
                "runtime_sha256": self.runtime_id,
                "protocol_stages": stages,
            }
            # Decision, support revision, state snapshot and audit are committed
            # together. The numeric state is unchanged because M is unresolved.
            db.execute(
                "INSERT INTO used_nonces VALUES(?,?,?)",
                (key_id, nonce, request_id),
            )
            event_hash = self._append_audit(
                db,
                {
                    "request_id": request_id,
                    "request_sha256": envelope_hash,
                    "action": action,
                    "key_id": key_id,
                    "support_id": support_id,
                    "support_revision": support_row["revision"],
                    "support_active": bool(support_row["active"]),
                    "support_assertion_sha256": support_row["assertion_sha256"],
                    "outcome": outcome,
                    "m_status": "UNRESOLVED",
                    "frontier": frontier,
                    "missing_premise": reason,
                    "protocol_stages": stages,
                    "state_before_sha256": before_hash,
                    "state_after_sha256": current_state["state_sha256"],
                    "state_version": state_version,
                    "runtime_sha256": self.runtime_id,
                    "trust_config_sha256": self.trust_config_sha256,
                },
            )
            response["audit_head_sha256"] = event_hash
            response_json = canonical_json(response).decode("utf-8")
            db.execute(
                "INSERT INTO requests VALUES(?,?,?,?,?)",
                (
                    request_id,
                    envelope_hash,
                    canonical_json(envelope).decode("utf-8"),
                    response_json,
                    state_version,
                ),
            )
            if failpoint == "before_commit":
                db.rollback()
                raise SimulatedCrash("injected failure before commit")
            db.commit()
            if failpoint == "after_commit":
                raise SimulatedCrash("injected failure after commit")
            return response

    def revoke_issuer(self, key_id: str, reason: str) -> None:
        """Local operator action; never exposed through the client API."""
        if type(reason) is not str or not reason.strip():
            raise ValueError("operator revocation requires a reason")
        with _connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT revoked FROM issuer_keys WHERE key_id=?", (key_id,)
            ).fetchone()
            if row is None:
                db.rollback()
                raise RequestRejected("unknown issuer key")
            if row["revoked"]:
                db.commit()
                return
            db.execute(
                "UPDATE issuer_keys SET revoked=1 WHERE key_id=?", (key_id,)
            )
            self._append_audit(
                db,
                {
                    "action": "operator.revoke_issuer",
                    "key_id": key_id,
                    "reason_sha256": sha256(reason.encode()).hexdigest(),
                    "runtime_sha256": self.runtime_id,
                },
            )
            db.commit()

    def snapshot(self) -> dict[str, Any]:
        with _connect(self.path) as db:
            self._verify_audit_chain(db)
            row = db.execute(
                "SELECT state_json,state_sha256,version FROM numeric_state WHERE id=1"
            ).fetchone()
            calculated_state_hash = sha256(
                canonical_json(json.loads(row["state_json"]))
            ).hexdigest()
            if calculated_state_hash != row["state_sha256"]:
                raise RequestRejected("durable numerical state hash mismatch")
            count = db.execute("SELECT COUNT(*) AS n FROM audit_events").fetchone()["n"]
            supports = [
                dict(row)
                for row in db.execute(
                    "SELECT support_id,active,revision,issuer_key_id "
                    "FROM support_state ORDER BY support_id"
                )
            ]
            return {
                "state": json.loads(row["state_json"]),
                "state_sha256": row["state_sha256"],
                "state_version": row["version"],
                "audit_event_count": count,
                "supports": supports,
            }

