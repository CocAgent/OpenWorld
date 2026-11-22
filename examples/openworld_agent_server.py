"""Local loopback HTTP server for the OpenWorld Companion + Multi-Agent Studio.

Binds strictly to 127.0.0.1 / localhost using stdlib single-threaded HTTPServer
(matching SQLite's thread affinity). Persists real agent memory, exact ledger,
and tool audit logs to a local SQLite database across restarts.

No secret material is ever persisted to SQLite or returned in API responses.
"""
from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples"))

from companion_agent.model_router import ModelConfig
from companion_agent.runtime import OpenWorldAgentRuntime

SCHEMA_VERSION = "openworld.companion-studio.v1"
UI_FILE = Path(__file__).resolve().parent / "web" / "companion_ui.html"
MAX_BODY_BYTES = 32768


def make_companion_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8780,
    db_path: str | Path = "data/openworld-companion.sqlite3",
    workspace_root: str | Path = ROOT,
    model_config: ModelConfig | None = None,
) -> HTTPServer:
    if host not in ("127.0.0.1", "localhost"):
        raise ValueError("companion server must bind strictly to 127.0.0.1 or localhost")

    runtime = OpenWorldAgentRuntime(
        workspace_root=workspace_root,
        db_path=db_path,
        model_config=model_config or ModelConfig.from_env(),
    )

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return None

        def _send_bytes(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, status: int, data: dict) -> None:
            body = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self._send_bytes(status, "application/json; charset=utf-8", body)

        def _read_json(self) -> dict:
            raw_len = self.headers.get("Content-Length", "0")
            try:
                length = int(raw_len)
            except ValueError as exc:
                raise ValueError("invalid Content-Length") from exc
            if length < 0 or length > MAX_BODY_BYTES:
                raise ValueError("request body out of bounds")
            if length == 0:
                return {}
            raw = self.rfile.read(length)
            try:
                parsed = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("invalid JSON payload") from exc
            if not isinstance(parsed, dict):
                raise ValueError("expected JSON object")
            return parsed

        def do_HEAD(self) -> None:
            path = urlparse(self.path).path
            if path in ("/", "/index.html") and UI_FILE.is_file():
                body = UI_FILE.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                return
            if path in ("/api/health", "/api/status"):
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                return
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path in ("/", "/index.html"):
                if not UI_FILE.is_file():
                    self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "UI file missing"})
                    return
                self._send_bytes(HTTPStatus.OK, "text/html; charset=utf-8", UI_FILE.read_bytes())
                return
            if path == "/api/health":
                self._send_json(HTTPStatus.OK, {"ok": True, "schema": SCHEMA_VERSION})
                return
            if path == "/api/status":
                self._send_json(HTTPStatus.OK, runtime.status())
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            try:
                body = self._read_json()
                if path == "/api/chat":
                    result = runtime.run_turn(str(body.get("message") or ""))
                    self._send_json(HTTPStatus.OK, result)
                    return
                if path == "/api/approvals/resolve":
                    aid = str(body.get("approval_id") or "")
                    approved = bool(body.get("approved"))
                    result = runtime.approve_action(aid, approved=approved)
                    self._send_json(HTTPStatus.OK, result)
                    return
                if path == "/api/config/model":
                    cfg = ModelConfig(
                        provider=str(body.get("provider") or "offline"),
                        model=str(body.get("model") or ""),
                        base_url=str(body.get("base_url") or ""),
                        api_key=str(body.get("api_key") or ""),
                        temperature=float(body.get("temperature") if body.get("temperature") is not None else 0.2),
                    )
                    info = runtime.configure_model(cfg)
                    self._send_json(HTTPStatus.OK, {"model": info, "state": runtime.status()})
                    return
                if path == "/api/agents/capability":
                    agent_id = str(body.get("agent_id") or "")
                    action = str(body.get("action") or "")
                    if action == "revoke":
                        res = runtime.revoke_agent(agent_id)
                    elif action == "restore":
                        res = runtime.restore_agent(agent_id)
                    else:
                        raise ValueError("action must be 'revoke' or 'restore'")
                    self._send_json(HTTPStatus.OK, {**res, "state": runtime.status()})
                    return
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            except PermissionError as exc:
                self._send_json(
                    HTTPStatus.FORBIDDEN,
                    {"error": str(exc), "error_type": "PermissionError", "state": runtime.status()},
                )
            except (ValueError, TypeError, RuntimeError) as exc:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": str(exc), "error_type": type(exc).__name__, "state": runtime.status()},
                )

    server = HTTPServer((host, port), Handler)
    server.runtime = runtime  # type: ignore[attr-defined]
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", choices=("127.0.0.1", "localhost"))
    parser.add_argument("--port", type=int, default=8780)
    parser.add_argument("--db", default="data/openworld-companion.sqlite3")
    parser.add_argument("--provider", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    args = parser.parse_args()

    cfg = ModelConfig.from_env(provider=args.provider, model=args.model, base_url=args.base_url)
    server = make_companion_server(
        host=args.host, port=args.port, db_path=args.db, model_config=cfg
    )
    actual_port = server.server_address[1]
    print(
        f"OpenWorld Companion Studio listening on http://{args.host}:{actual_port} "
        f"(model={cfg.model_ref}, db={args.db})",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.runtime.close()  # type: ignore[attr-defined]
        server.server_close()


if __name__ == "__main__":
    main()
