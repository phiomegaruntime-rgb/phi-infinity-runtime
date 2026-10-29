from __future__ import annotations

from pathlib import Path
import socket
import subprocess
import sys
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class ClientRun:
    pid: int
    returncode: int
    stdout: str
    stderr: str


class RuntimeOrchestrator:
    """Starts one loopback-only service and coordinates independent clients."""

    def __init__(self, database: Path, trust_config: Path):
        self.database = Path(database)
        self.trust_config = Path(trust_config)
        self.process: subprocess.Popen | None = None
        self.url: str | None = None

    def start(self, timeout: float = 10.0) -> str:
        if self.process is not None:
            raise RuntimeError("service is already started")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.url = f"http://127.0.0.1:{port}"
        self.process = subprocess.Popen(
            [
                sys.executable, "-m", "independent_runtime.service",
                "--database", str(self.database),
                "--trust-config", str(self.trust_config),
                "--host", "127.0.0.1", "--port", str(port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError("local runtime service exited before ready")
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                    return self.url
            except OSError:
                time.sleep(0.03)
        self.stop()
        raise TimeoutError("local runtime service did not become ready")

    def run_client(self, request_file: Path) -> ClientRun:
        if self.process is None or self.url is None or self.process.poll() is not None:
            raise RuntimeError("service is not running")
        process = subprocess.Popen(
            [
                sys.executable, "-m", "independent_runtime.client",
                "--url", self.url, "--request-file", str(request_file),
            ],
            capture_output=True,
            text=True,
        )
        stdout, stderr = process.communicate(timeout=15)
        return ClientRun(process.pid, process.returncode, stdout, stderr)

    def stop(self) -> None:
        if self.process is None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        self.process = None
        self.url = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()

