"""Narrow local HTTP adapter for the TRIA Playground.

Run from an editable checkout:
    python playground/adapter.py
Then open:
    http://127.0.0.1:8765/

Trust boundary:
- accepts only a small allowlisted scenario/revocation vocabulary
- creates fresh synthetic TRIA state per request (temporary SQLite for the reference)
- returns a sanitized JSON projection
- never exposes Relationship, admin/store objects, provider credentials, or arbitrary execution
- binds to loopback by default

This is a demonstration adapter, not a production authorization service.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from reference_experience import run_reference
from sdk_scenarios import agentic_action, consent_and_revocation, contested_reality

HOST = "127.0.0.1"
PORT = 8765
MAX_BODY_BYTES = 4096
PLAYGROUND_DIR = Path(__file__).resolve().parent

_ALLOWED_SCENARIOS = {"consent", "reality", "action"}
_ALLOWED_REVOKE = {"consent", "permission"}


def _sanitize_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": str(event.get("type", "")),
            "actor": str(event.get("actor", "")),
            "sequence": int(event.get("sequence", 0)),
        }
        for event in events
    ]


def _sanitize_audit(audit: dict[str, Any]) -> dict[str, bool]:
    return {
        "chain_valid": bool(audit.get("chain_valid", False)),
        "relationship_valid": bool(audit.get("relationship_valid", False)),
    }


def run_scenario(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate an untrusted browser request and return a safe projection."""
    if set(payload) - {"scenario", "revoke", "state"}:
        raise ValueError("Only 'scenario', optional 'revoke', or 'state' are accepted.")

    scenario = payload.get("scenario")
    if not isinstance(scenario, str) or scenario not in _ALLOWED_SCENARIOS:
        raise ValueError("Unknown scenario.")

    revoke = payload.get("revoke")
    if revoke is not None and (not isinstance(revoke, str) or revoke not in _ALLOWED_REVOKE):
        raise ValueError("Unknown revocation mode.")

    state = payload.get("state")
    if "state" in payload:
        expected = {"dispute"} if scenario == "reality" else {"consent", "permission"}
        if "revoke" in payload or not isinstance(state, dict) or set(state) != expected:
            raise ValueError("State must contain exactly the scenario switches; do not combine with revoke.")
        if any(type(value) is not bool for value in state.values()):
            raise ValueError("State switches must be JSON booleans.")

    if scenario == "consent":
        raw = consent_and_revocation(revoke or "consent", state=state)
        return {
            "scenario": "consent",
            "revoked": raw["revoked"] if state is None else [key for key, active in state.items() if not active],
            "before": {
                "executed": bool(raw["before"]["executed"]),
                "reason": str(raw["before"]["reason"]),
                "outcome": str(raw["before"]["outcome"]),
            },
            "after": {
                "executed": bool(raw["after"]["executed"]),
                "reason": str(raw["after"]["reason"]),
                "outcome": str(raw["after"]["outcome"]),
            },
            "audit": _sanitize_audit(raw["audit"]),
            "events": _sanitize_events(raw["events"]),
        }

    if scenario == "action":
        raw = agentic_action(revoke or "permission", state=state)
        return {
            "scenario": "action",
            "revoked": raw["revoked"] if state is None else [key for key, active in state.items() if not active],
            "before": {
                "executed": bool(raw["before"]["executed"]),
                "reason": str(raw["before"]["reason"]),
                "outcome": str(raw["before"]["outcome"]),
            },
            "after": {
                "executed": bool(raw["after"]["executed"]),
                "reason": str(raw["after"]["reason"]),
                "outcome": str(raw["after"]["outcome"]),
            },
            "executor_calls": int(raw["executor_calls"]),
            "audit": _sanitize_audit(raw["audit"]),
            "events": _sanitize_events(raw["events"]),
        }

    raw = contested_reality(dispute=state["dispute"] if state is not None else True)
    return {
        "scenario": "reality",
        "interpretation_status": str(raw["interpretation_status"]),
        "audit": _sanitize_audit(raw["audit"]),
        "events": _sanitize_events(raw["events"]),
    }


class PlaygroundHandler(BaseHTTPRequestHandler):
    server_version = "TRIAPlayground/0.2"

    def _json(self, status: int, body: dict[str, Any]) -> None:
        encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        pages = {"/": "index.html", "/index.html": "index.html",
                 "/before-with-tria.html": "before-with-tria.html",
                 "/evaluate.html": "evaluate.html", "/evidence.html": "evidence.html"}
        if self.path in pages:
            data = (PLAYGROUND_DIR / pages[self.path]).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == "/healthz":
            self._json(200, {"status": "ok", "adapter": "tria-playground-v0.2", "state_selection": True, "reference_experience": True})
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path not in {"/api/scenario", "/api/reference"}:
            self._json(404, {"error": "not_found"})
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json(400, {"error": "invalid_content_length"})
            return
        if content_length <= 0 or content_length > MAX_BODY_BYTES:
            self._json(413, {"error": "invalid_body_size"})
            return
        if self.headers.get_content_type() != "application/json":
            self._json(415, {"error": "application_json_required"})
            return
        try:
            payload = json.loads(self.rfile.read(content_length))
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object.")
            if self.path == "/api/reference":
                if payload:
                    raise ValueError("The reference experience accepts an empty object only.")
                result = run_reference()
            else:
                result = run_scenario(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self._json(400, {"error": "invalid_request", "detail": str(exc)})
            return
        except Exception:
            # A runner/storage failure is not a confirmed SDK result. Do not expose
            # internal exception text or substitute an illustrative outcome.
            self._json(500, {"error": "sdk_run_failed"})
            return
        self._json(200, result)

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep the local demo quiet and avoid reflecting request data into logs.
        return


def serve(host: str = HOST, port: int = PORT) -> None:
    server = ThreadingHTTPServer((host, port), PlaygroundHandler)
    print(f"TRIA Playground adapter listening on http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
