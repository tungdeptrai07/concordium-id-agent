"""HTTP server for VeriPulse Concordium Trusted Agent (port 8093)."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.concordium_agent import VeriPulseConcordiumEngine


class VeriPulseHTTPHandler(SimpleHTTPRequestHandler):
    """Serves the VeriPulse Concordium Trusted Agent UI and JSON APIs."""

    engine = VeriPulseConcordiumEngine()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._send_json(
                {
                    "status": "ok",
                    "agentId": self.engine.agent_card.agent_id,
                    "auditIntegrityValid": self.engine.verify_audit_chain_integrity(),
                }
            )
            return

        if self.path == "/api/state":
            self._send_json(self.engine.get_dashboard_state())
            return

        if self.path in {"", "/"}:
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(min(length, 128_000))
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            self._send_json({"error": "Invalid JSON body"}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            if self.path == "/api/verify_id":
                stmt = self.engine.verify_zk_identity(
                    credential_id=str(data.get("credentialId", "ccd-cred-98a7b6c5")),
                    age_over_18=bool(data.get("ageOver18", True)),
                    jurisdiction_allowed=bool(data.get("jurisdictionAllowed", True)),
                    sanctions_passed=bool(data.get("sanctionsPassed", True)),
                )
                self._send_json({"statement": asdict(stmt), "state": self.engine.get_dashboard_state()})
                return

            if self.path == "/api/execute_x402":
                result = self.engine.execute_x402_sponsored_task(
                    credential_id=str(data.get("credentialId", "ccd-cred-98a7b6c5")),
                    service_skill=str(data.get("serviceSkill", "rwa-compliance-check")),
                    task_input=str(data.get("taskInput", "Verify counterparty treasury wallet")),
                )
                self._send_json({**result, "state": self.engine.get_dashboard_state()})
                return
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)


def create_server(
    host: str = "127.0.0.1",
    port: int = 8093,
    engine: VeriPulseConcordiumEngine | None = None,
) -> ThreadingHTTPServer:
    """Create the VeriPulse Concordium HTTP server."""

    class BoundHandler(VeriPulseHTTPHandler):
        pass

    BoundHandler.engine = engine or VeriPulseConcordiumEngine()
    return ThreadingHTTPServer((host, port), BoundHandler)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8093"))
    srv = create_server(port=port)
    print(f"VeriPulse Concordium Trusted Agent running on http://127.0.0.1:{port}", flush=True)
    srv.serve_forever()
