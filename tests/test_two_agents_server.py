"""End-to-end HTTP integration tests for the live 2-agent Python backend and UI."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples"))

from two_agents_server import SCHEMA_VERSION, make_server


class LiveTwoAgentsServerTests(unittest.TestCase):
    def setUp(self) -> None:
        ready = threading.Event()
        holder: dict[str, object] = {}

        def _serve() -> None:
            try:
                server = make_server(host="127.0.0.1", port=0)
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
                server.session.close()
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

    def _request(self, path: str, method: str = "GET", payload: dict | None = None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"} if data is not None else {}
        req = Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=5) as resp:
                raw = resp.read()
                return resp.status, resp.headers.get("Content-Type", ""), raw
        except HTTPError as exc:
            return exc.code, exc.headers.get("Content-Type", ""), exc.read()

    def _json(self, path: str, method: str = "GET", payload: dict | None = None):
        status, _, raw = self._request(path, method, payload)
        return status, json.loads(raw.decode("utf-8"))

    def test_root_serves_html_and_state_exposes_live_backend(self):
        status, ctype, raw = self._request("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", ctype)
        self.assertIn(b"/api/state", raw)

        s_code, state = self._json("/api/state")
        self.assertEqual(s_code, 200)
        self.assertEqual(state["schema"], SCHEMA_VERSION)
        self.assertTrue(state["replay_verified"])
        self.assertEqual(state["balances"], {"alice": 8, "bob": 2})
        self.assertEqual(state["total_resources"], 10)

    def test_cooperative_and_hostile_liar_flows_via_http(self):
        code, st = self._json("/api/session/reset", "POST", {"mode": "cooperative", "max_rounds": 4})
        self.assertEqual(code, 200)
        for _ in range(4):
            code, st = self._json("/api/round/step", "POST", {})
            self.assertEqual(code, 200)
        self.assertEqual(st["round"], 4)
        self.assertEqual(st["balances"], {"alice": 8, "bob": 2})
        self.assertEqual(st["alice"]["memory"]["observations"], 4)
        self.assertEqual(st["alice"]["memory"]["successes"], 4)
        self.assertEqual(len(st["w3_receipts"]), 4)
        self.assertTrue(st["replay_verified"])

        # Hostile liar must catch every fake COMMIT_ACK and stop at CAP = 4.
        code, st = self._json("/api/session/reset", "POST", {"mode": "hostile_liar", "max_rounds": 10})
        self.assertEqual(code, 200)
        for _ in range(10):
            code, st = self._json("/api/round/step", "POST", {})
            self.assertEqual(code, 200)
        self.assertEqual(st["alice"]["risk_budget"]["known_loss"], 4)
        self.assertEqual(st["alice"]["fake_acks_caught"], 4)
        self.assertLessEqual(st["alice"]["risk_budget"]["peak_exposure"], 4)
        self.assertEqual(st["balances"], {"alice": 4, "bob": 6})
        self.assertEqual(st["total_resources"], 10)

    def test_p7_lost_notices_lockup_vs_w3_reconciliation_rescue(self):
        # Notifications-only locks up at 4/4 pending despite honest Bob returns.
        self._json("/api/session/reset", "POST", {"mode": "lost_notices", "p7_reconcile": False, "max_rounds": 12})
        for _ in range(12):
            code, st = self._json("/api/round/step", "POST", {})
            self.assertEqual(code, 200)
        self.assertEqual(len(st["alice"]["risk_budget"]["pending"]), 4)
        self.assertEqual(st["history"][-1]["status"], "capped")
        self.assertEqual(len(st["w3_receipts"]), 8)

        # W3 Reconciliation sweeps every 3 rounds and completes all 12 rounds.
        self._json("/api/session/reset", "POST", {"mode": "lost_notices", "p7_reconcile": True, "max_rounds": 12})
        for _ in range(12):
            code, st = self._json("/api/round/step", "POST", {})
            self.assertEqual(code, 200)
        self.assertEqual(len(st["w3_receipts"]), 12)
        self.assertGreater(st["alice"]["reconciled_receipts"], 0)
        self.assertEqual(st["balances"], {"alice": 8, "bob": 2})

    def test_recovery_switches_sqlite_hm_p1e_from_static_to_fast(self):
        self._json("/api/session/reset", "POST", {"mode": "recovery", "max_rounds": 16, "recover_at": 8, "probe_interval": 2})
        for _ in range(16):
            code, st = self._json("/api/round/step", "POST", {})
            self.assertEqual(code, 200)
        self.assertEqual(st["alice"]["memory"]["estimator"], "fast")
        self.assertEqual(st["alice"]["risk_budget"]["known_loss"], 0)
        self.assertEqual(st["balances"], {"alice": 8, "bob": 2})

    def test_interactive_play_bob_endpoints(self):
        code, st = self._json("/api/session/reset", "POST", {"mode": "play_bob", "max_rounds": 6})
        self.assertEqual(code, 200)

        # Round 1: Bob accepts and returns honestly.
        code, st = self._json("/api/round/step", "POST", {})
        self.assertEqual((code, st["stage"]), (200, "awaiting_bob_reply"))
        code, st = self._json("/api/bob/reply", "POST", {"decision": "accept"})
        self.assertEqual((code, st["stage"]), (200, "awaiting_bob_return"))
        self.assertEqual(st["balances"], {"alice": 7, "bob": 3})
        code, st = self._json("/api/bob/return", "POST", {"action": "return"})
        self.assertEqual((code, st["stage"]), (200, "idle"))
        self.assertEqual(st["balances"], {"alice": 8, "bob": 2})
        self.assertEqual(st["alice"]["memory"]["successes"], 1)

        # Round 2: Bob accepts and lies with fake COMMIT_ACK -> caught via W3 ledger!
        self._json("/api/round/step", "POST", {})
        self._json("/api/bob/reply", "POST", {"decision": "accept"})
        code, st = self._json("/api/bob/return", "POST", {"action": "lie"})
        self.assertEqual(code, 200)
        self.assertEqual(st["balances"], {"alice": 7, "bob": 3})
        self.assertEqual(st["alice"]["risk_budget"]["known_loss"], 1)
        self.assertEqual(st["alice"]["fake_acks_caught"], 1)

        # Round 3: Bob declines honestly -> 0 additional loss.
        self._json("/api/round/step", "POST", {})
        code, st = self._json("/api/bob/reply", "POST", {"decision": "decline"})
        self.assertEqual((code, st["stage"]), (200, "idle"))
        self.assertEqual(st["alice"]["risk_budget"]["known_loss"], 1)

    def test_real_backend_security_attacks_and_revocation_fail_closed(self):
        for attack in ("cross_owner", "wrong_token", "spoof_verified", "replay_id"):
            with self.subTest(attack=attack):
                code, res = self._json("/api/security/test", "POST", {"attack": attack})
                self.assertEqual(code, 200)
                self.assertEqual(res["outcome"], "BLOCKED")
                self.assertTrue(res["tick_unchanged"])
                self.assertTrue(res["fingerprint_unchanged"])

        # Revoking Alice's real HMAC token blocks /api/round/step with HTTP 403!
        code, res = self._json("/api/security/test", "POST", {"attack": "toggle_revoke_alice"})
        self.assertEqual((code, res["outcome"]), (200, "REVOKED"))
        code, err = self._json("/api/round/step", "POST", {})
        self.assertEqual(code, 403)
        self.assertEqual(err["error_type"], "PermissionError")

        # Restoring token allows stepping again.
        code, res = self._json("/api/security/test", "POST", {"attack": "toggle_revoke_alice"})
        self.assertEqual((code, res["outcome"]), (200, "RESTORED"))
        code, st = self._json("/api/round/step", "POST", {})
        self.assertEqual(code, 200)
        self.assertEqual(st["round"], 1)

    def test_refuses_non_loopback_bind(self):
        with self.assertRaises(ValueError):
            make_server(host="0.0.0.0", port=0)


if __name__ == "__main__":
    unittest.main()
