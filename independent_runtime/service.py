from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
import threading

from .store import DurableRuntimeStore, RequestRejected, TrustedIssuer


class LocalRuntimeServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address, store: DurableRuntimeStore):
        ip = ipaddress.ip_address(address[0])
        if not ip.is_loopback:
            raise ValueError("runtime service may bind to loopback only")
        self.store = store
        super().__init__(address, _handler_type())


def _handler_type():
    class Handler(BaseHTTPRequestHandler):
        server: LocalRuntimeServer

        def do_POST(self):
            if self.path != "/v1/submit":
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 1 <= length <= 1_000_000:
                    raise RequestRejected("invalid request size")
                raw = self.rfile.read(length)
                envelope = json.loads(raw)
                result = self.server.store.process(envelope)
                # The only semantic output crossing the API is the exact
                # closed fragment graph; transport metadata is not exposed.
                body = json.dumps(
                    {"graph": result["graph"]},
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except RequestRejected as exc:
                self.send_error(403, str(exc))
            except (ValueError, json.JSONDecodeError):
                self.send_error(400, "invalid request")
            except Exception:
                self.send_error(500, "runtime request failed")

        def log_message(self, fmt, *args):
            return

    return Handler


def load_issuers(path: Path) -> dict[str, TrustedIssuer]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict or set(value) != {"issuers"}:
        raise ValueError("trust config must contain only issuers")
    if type(value["issuers"]) is not list:
        raise ValueError("issuers must be a list")
    result = {}
    for item in value["issuers"]:
        if type(item) is not dict or set(item) != {
            "key_id", "public_key_pem", "allowed_support_ids"
        }:
            raise ValueError("issuer record fields are not exact")
        key_id = item["key_id"]
        allowed = item["allowed_support_ids"]
        if type(key_id) is not str or not key_id or key_id in result:
            raise ValueError("issuer key id must be unique and non-empty")
        if type(item["public_key_pem"]) is not str:
            raise ValueError("public key must be PEM text")
        if type(allowed) is not list or not allowed or any(
            type(support_id) is not str or not support_id for support_id in allowed
        ):
            raise ValueError("explicit allowed_support_ids are required")
        result[key_id] = TrustedIssuer(
            item["public_key_pem"], tuple(allowed)
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True)
    parser.add_argument("--trust-config", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    store = DurableRuntimeStore(args.database, load_issuers(Path(args.trust_config)))
    with LocalRuntimeServer((args.host, args.port), store) as server:
        print(f"ready {server.server_address[0]}:{server.server_address[1]}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()

