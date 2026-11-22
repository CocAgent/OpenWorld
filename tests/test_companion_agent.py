"""Unit, persistence, multi-agent delegation, security, and HTTP tests for OpenWorld Companion."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples"))

from companion_agent.memory_store import CompanionMemoryStore
from companion_agent.model_router import ModelConfig
from companion_agent.runtime import OpenWorldAgentRuntime
from openworld_agent_server import SCHEMA_VERSION, make_companion_server
from openworld_superkernel.memory_contracts import Provenance


class CompanionRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ws = Path(self.tmp.name) / "workspace"
        self.ws.mkdir()
        (self.ws / "docs").mkdir()
        (self.ws / "src").mkdir()
        (self.ws / "docs" / "ARCHITECTURE.md").write_text(
            "# OpenWorld Architecture\nIdentity is separate from model weights and permissions.\n",
            encoding="utf-8",
        )
        (self.ws / "src" / "guard.py").write_text(
            "class CapabilityAuthority:\n    pass\n",
            encoding="utf-8",
        )
        (self.ws / ".env").write_text("SECRET_KEY=do_not_expose\n", encoding="utf-8")
        self.db_path = Path(self.tmp.name) / "companion.sqlite3"

    def test_real_tools_and_atlas_peer_delegation(self):
        with OpenWorldAgentRuntime(workspace_root=self.ws, db_path=self.db_path) as rt:
            res = rt.run_turn("Read docs/ARCHITECTURE.md and ask Atlas to verify")
            kinds = [step["kind"] for step in res["trace"]]
            self.assertIn("tool_call", kinds)
            self.assertIn("delegation_request", kinds)
            self.assertIn("delegation_reply", kinds)
            self.assertIn("Identity is separate from model weights", res["answer"])
            self.assertEqual(res["answer_provenance"], "inferred")
            self.assertTrue(res["state"]["ledger_chain_verified"])
            # Both agents share the same model_ref while keeping separate identities.
            refs = {ag["agent_id"]: ag["model_ref"] for ag in res["state"]["agents"]}
            self.assertEqual(refs["nova"], refs["atlas"])

    def test_persistent_sqlite_memory_survives_restart(self):
        with OpenWorldAgentRuntime(workspace_root=self.ws, db_path=self.db_path) as rt1:
            rt1.run_turn("Remember my goal is trustworthy multi-agent memory")
            st1 = rt1.status()
            self.assertEqual(len(st1["facts"]), 1)
            self.assertTrue(st1["ledger_chain_verified"])

        # Reopen in a brand-new runtime instance against the same SQLite file.
        with OpenWorldAgentRuntime(workspace_root=self.ws, db_path=self.db_path) as rt2:
            res2 = rt2.run_turn("What do you remember about my goal?")
            self.assertIn("trustworthy multi-agent memory", res2["answer"])
            st2 = rt2.status()
            self.assertTrue(st2["ledger_chain_verified"])
            self.assertGreater(st2["ledger_count"], st1["ledger_count"])

    def test_consequential_write_requires_explicit_human_approval(self):
        with OpenWorldAgentRuntime(workspace_root=self.ws, db_path=self.db_path) as rt:
            res = rt.run_turn("Calculate (1 - 0.25/0.85) * 960 and write calc-report.md")
            self.assertEqual(len(res["pending_approvals"]), 1)
            apr = res["pending_approvals"][0]
            target_file = self.ws / "data" / "agent_notes" / "calc-report.md"
            # Must NOT exist on disk before explicit approval!
            self.assertFalse(target_file.exists())

            # Deny first test case on a second write, approve this one.
            approved_res = rt.approve_action(apr["approval_id"], approved=True)
            self.assertTrue(approved_res["executed"])
            self.assertTrue(target_file.is_file())
            written_text = target_file.read_text(encoding="utf-8")
            self.assertIn("677.647", written_text)

            # Second write explicitly denied leaves 0 file on disk.
            res2 = rt.run_turn("Write denied-note.md with summary")
            apr2 = res2["pending_approvals"][0]
            denied_res = rt.approve_action(apr2["approval_id"], approved=False)
            self.assertFalse(denied_res["executed"])
            self.assertFalse((self.ws / "data" / "agent_notes" / "denied-note.md").exists())
            self.assertTrue(rt.status()["ledger_chain_verified"])

    def test_security_sandbox_ast_math_secret_blocking_and_revocation(self):
        with OpenWorldAgentRuntime(workspace_root=self.ws, db_path=self.db_path) as rt:
            # 1. Path traversal & absolute path denied
            with self.assertRaises(PermissionError):
                rt.gateway.execute_tool(
                    agent_id="nova",
                    tool_name="read_file",
                    arguments={"path": "../../etc/passwd"},
                    read_capability=rt._caps["nova"]["read"],
                )
            with self.assertRaises(PermissionError):
                rt.gateway.execute_tool(
                    agent_id="nova",
                    tool_name="read_file",
                    arguments={"path": "/etc/passwd"},
                    read_capability=rt._caps["nova"]["read"],
                )
            # 2. Sensitive secret file `.env` denied
            with self.assertRaises(PermissionError):
                rt.gateway.execute_tool(
                    agent_id="nova",
                    tool_name="read_file",
                    arguments={"path": ".env"},
                    read_capability=rt._caps["nova"]["read"],
                )
            # 3. Code injection inside calculate denied by AST allowlist
            with self.assertRaises(ValueError):
                rt.gateway.execute_tool(
                    agent_id="nova",
                    tool_name="calculate",
                    arguments={"expression": "__import__('os').system('echo pwn')"},
                    read_capability=rt._caps["nova"]["read"],
                )
            # 4. Live capability revocation blocks Nova's tool calls (fail-closed)
            rt.revoke_agent("nova")
            res = rt.run_turn("Search CapabilityAuthority in src/")
            self.assertTrue(any(s["kind"] == "tool_denied" for s in res["trace"]))
            # Restoring capability re-enables tool access
            rt.restore_agent("nova")
            res_ok = rt.run_turn("Search CapabilityAuthority in src/")
            self.assertTrue(any(s["kind"] == "tool_result" for s in res_ok["trace"]))

    def test_memory_owner_isolation_verified_rejection_and_secret_redaction(self):
        with CompanionMemoryStore(":memory:") as store:
            with self.assertRaises(ValueError):
                store.append_ledger(
                    event_id="bad-verified",
                    owner_id="owner-a",
                    agent_id="nova",
                    event_type="note",
                    provenance=Provenance.VERIFIED,
                    payload={"claim": "forged"},
                )
            with self.assertRaises(PermissionError):
                store.save_fact(
                    owner_id="owner-a",
                    agent_id="nova",
                    fact_key="k",
                    content="v",
                    provenance=Provenance.INFERRED,
                    source_event_id="ev1",
                    requester_owner_id="owner-b",
                )
        # API key must never appear in public_info()
        cfg = ModelConfig(provider="openai", model="gpt-4o-mini", api_key="sk-secret-value-123")
        info = cfg.public_info()
        self.assertTrue(info["api_key_configured"])
        self.assertNotIn("sk-secret-value-123", json.dumps(info))


class CompanionServerHTTPTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = Path(self.tmp.name) / "http-companion.sqlite3"
        ready = threading.Event()
        holder: dict[str, object] = {}

        def _serve() -> None:
            try:
                server = make_companion_server(
                    host="127.0.0.1",
                    port=0,
                    db_path=self.db_path,
                    workspace_root=ROOT,
                )
            except BaseException as exc:
                holder["error"] = exc
                ready.set()
                return
            holder["server"] = server
            holder["port"] = server.server_address[1]
            ready.set()
            try:
                server.serve_forever(poll_interval=0.02)
            finally:
                server.runtime.close()
                server.server_close()

        self.thread = threading.Thread(target=_serve, daemon=True)
        self.thread.start()
        self.assertTrue(ready.wait(timeout=5))
        if "error" in holder:
            raise holder["error"]
        self.server = holder["server"]
        self.base = f"http://127.0.0.1:{holder['port']}"

    def tearDown(self) -> None:
        if hasattr(self, "server"):
            self.server.shutdown()
            self.thread.join(timeout=5)

    def _json(self, path: str, method: str = "GET", payload: dict | None = None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"} if data is not None else {}
        req = Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_http_ui_chat_model_switch_and_capability_revocation(self):
        with urlopen(self.base + "/", timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn(b"/api/chat", resp.read())

        code, health = self._json("/api/health")
        self.assertEqual((code, health["schema"]), (200, SCHEMA_VERSION))

        code, chat = self._json("/api/chat", "POST", {"message": "Calculate 21 * 2"})
        self.assertEqual(code, 200)
        self.assertIn("42", chat["answer"])
        self.assertTrue(chat["state"]["ledger_chain_verified"])

        # Hot-swap shared model config (redacting secret key).
        code, cfg_res = self._json(
            "/api/config/model",
            "POST",
            {"provider": "ollama", "model": "qwen2.5:7b", "api_key": "never-expose"},
        )
        self.assertEqual(code, 200)
        self.assertEqual(cfg_res["model"]["provider"], "ollama")
        self.assertNotIn("never-expose", json.dumps(cfg_res))

        # Switch back to offline and test live capability revocation.
        self._json("/api/config/model", "POST", {"provider": "offline"})
        code, rev = self._json("/api/agents/capability", "POST", {"agent_id": "atlas", "action": "revoke"})
        self.assertEqual((code, rev["revoked"]), (200, True))
        code, res = self._json("/api/chat", "POST", {"message": "Ask Atlas to verify docs/ARCHITECTURE.md"})
        self.assertEqual(code, 200)
        self.assertTrue(any(s["kind"] == "tool_denied" for s in res["trace"]))

    def test_refuses_non_loopback_host(self):
        with self.assertRaises(ValueError):
            make_companion_server(host="0.0.0.0", port=0, db_path=":memory:")


if __name__ == "__main__":
    unittest.main()
