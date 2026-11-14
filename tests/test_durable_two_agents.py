"""Causal feedback, restart and atomicity checks for the durable two-agent lab."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))
from durable_two_agents import DurableTwoAgents, canonical, digest, settings
from two_agents import Outcome, simulate


class DurableTwoAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "pair.sqlite3"

    def cli(self, *options, success=True):
        result = subprocess.run([sys.executable, str(ROOT/"examples/durable_two_agents.py"),
                                 "--db", str(self.path), *options],
                                capture_output=True, text=True, timeout=30)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def test_separate_processes_resume_world_memory_and_delayed_notice(self):
        first = self.cli("--rounds", "3", "--delay", "2", "--drop-every", "0")
        self.assertTrue(first["channel"])
        second = self.cli("--rounds", "3")
        self.assertEqual((first["round"], second["resumed_from_round"], second["round"]), (3, 3, 6))
        self.assertEqual(second["settings"]["delay"], 2)
        status = self.cli("--status", "--history")
        self.assertEqual(len(status["history"]), 6)
        with DurableTwoAgents(Path(self.temp.name)/"continuous.sqlite3", config={"delay": 2, "drop_every": 0}) as sim:
            for _ in range(6):
                sim.step()
            continuous = sim.status(history=True)
        for key in ("world_sha256", "balances", "budget", "channel", "memory", "exact_events", "history", "duplicates_ignored"):
            self.assertEqual(status[key], continuous[key], key)
        for key in ("world_sha256", "budget", "memory", "exact_events"):
            self.assertEqual(status[key], second[key], key)

    def test_restarted_always_offer_matches_original_safe_p7_scenarios(self):
        for mode in ("notifications", "reconcile"):
            for scenario in ("cooperative", "hostile", "recovery"):
                for delay in (0, 2):
                    with self.subTest(mode=mode, scenario=scenario, delay=delay):
                        path = Path(self.temp.name)/f"{mode}-{scenario}-{delay}.sqlite3"
                        config = {"mode": mode, "scenario": scenario, "delay": delay, "policy": "always_offer"}
                        for _ in range(4):
                            with DurableTwoAgents(path, config=config) as sim:
                                for _ in range(5):
                                    sim.step()
                                result = sim.status()
                        original = simulate(mode=mode, scenario=scenario, delay=delay)
                        for key in ("sent", "returned", "actual_loss", "balances"):
                            self.assertEqual(result[key], original[key], key)
                        self.assertEqual(result["world_sha256"], original["final_fingerprint"])
                        self.assertEqual(result["budget"]["exposure"], result["budget"]["known_loss"]+len(result["budget"]["pending"]))
                        self.assertLessEqual(result["peak_actual_exposure"], 4)
                        self.assertLessEqual(result["budget"]["peak_exposure"], 4)

    def test_actual_partner_feedback_changes_memory_policy_after_restart(self):
        with DurableTwoAgents(self.path, config={"scenario": "hostile", "delay": 0, "drop_every": 0}) as sim:
            for _ in range(3):
                sim.step()
        with DurableTwoAgents(self.path) as sim:
            for _ in range(3):
                sim.step()
            result = sim.status(history=True)
            self.assertEqual(result["sent"], 2)
            self.assertEqual(result["actual_loss"], 2)
            self.assertEqual(result["memory"]["A"]["observations"], 2)
            self.assertEqual(result["memory"]["A"]["successes"], 0)
            self.assertEqual(result["memory"]["B"]["observations"], 6)
            self.assertEqual(result["memory"]["B"]["successes"], 2)
            self.assertTrue(all(not r["gift"] for r in result["history"][2:]))
            for row in sim.memory.db.execute("SELECT provenance,payload FROM exact_events"):
                self.assertEqual(row[0], "simulated")
                self.assertEqual(json.loads(row[1])["provenance"], "SIMULATED")
        with DurableTwoAgents(Path(self.temp.name)/"control.sqlite3", config={"scenario": "hostile", "policy": "always_offer", "delay": 0, "drop_every": 0}) as sim:
            for _ in range(6):
                sim.step()
            self.assertEqual(sim.status()["actual_loss"], 4)

    def crash(self, hook, exit_code, *, after_step=False):
        code = "\n".join([
            "import os, sys",
            "sys.path.insert(0, sys.argv[1])",
            "from durable_two_agents import DurableTwoAgents",
            "class Crash(DurableTwoAgents):",
            f"    def {hook}(self): os._exit({exit_code})" if not after_step else "    pass",
            "with Crash(sys.argv[2]) as simulation:",
            "    simulation.step()",
            f"    os._exit({exit_code})" if after_step else "",
        ])
        result = subprocess.run([sys.executable, "-c", code, str(ROOT/"examples"), str(self.path)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, exit_code, result.stderr)

    def test_process_exit_before_journal_commit_leaves_no_transfer_or_reservation(self):
        self.crash("_before_journal_commit", 21)
        status = self.cli("--status")
        self.assertEqual(status["round"], 0)
        self.assertEqual(status["balances"], {"A": 8, "B": 0})
        self.assertEqual(status["budget"]["pending"], [])
        self.assertEqual(status["exact_events"], 0)

    def test_process_exit_after_round_commit_recovers_reservation_queue_and_memory_once(self):
        self.crash("_after_journal_commit", 22)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM durable_pair_journal").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM exact_events").fetchone()[0], 0)
        recovered = self.cli("--status")
        self.assertEqual(recovered["round"], 1)
        self.assertEqual(recovered["budget"]["pending"], [0])
        self.assertEqual(recovered["channel"][0]["origin"], 0)
        self.assertEqual(recovered["recovered_memory_events"], 1)
        self.assertEqual(recovered["memory"]["A"]["observations"], 0)
        self.assertEqual(recovered["memory"]["B"]["observations"], 1)
        reopened = self.cli("--status")
        self.assertEqual(reopened["recovered_memory_events"], 0)
        self.assertEqual(reopened["memory"], recovered["memory"])
        self.assertEqual(reopened["budget"], recovered["budget"])

    def test_process_exit_after_memory_commit_does_not_repeat_training(self):
        self.crash("unused", 23, after_step=True)
        status = self.cli("--status")
        self.assertEqual(status["round"], 1)
        self.assertEqual(status["exact_events"], 1)
        self.assertEqual(status["recovered_memory_events"], 0)

    def test_memory_transaction_failure_rolls_back_both_agents_and_recovers(self):
        with DurableTwoAgents(self.path, config={"delay": 0, "drop_every": 0}) as sim:
            original = sim.memory.apply_batch
            sim.memory.apply_batch = lambda items, **kw: original(items, inject_failure=True, **kw)
            with self.assertRaisesRegex(RuntimeError, "injected failure"):
                sim.step()
            with self.assertRaisesRegex(RuntimeError, "close and reopen"):
                sim.step()
            self.assertEqual(sim.memory.db.execute("SELECT COUNT(*) FROM exact_events").fetchone()[0], 0)
        with DurableTwoAgents(self.path) as sim:
            result = sim.status()
            self.assertEqual(result["recovered_memory_events"], 2)
            self.assertEqual(result["exact_events"], 2)
            self.assertEqual(result["budget"]["exposure"], 0)
            self.assertEqual(result["memory"]["A"]["observations"], 1)

    def test_reconciled_receipt_then_delayed_duplicate_trains_and_releases_once(self):
        with DurableTwoAgents(self.path, config={"delay": 2, "drop_every": 0}) as sim:
            for _ in range(4):
                sim.step()
            self.assertEqual(sim.status()["reconciled"], 1)
        with DurableTwoAgents(self.path) as sim:
            sim.step()
            status = sim.status()
            self.assertEqual(status["duplicates_ignored"], 1)
            self.assertEqual(status["memory"]["A"]["observations"], 3)
            self.assertEqual(status["budget"]["pending"], [3, 4])
            self.assertEqual(status["exact_events"], 8)

    def test_foreign_origin_forged_digest_and_false_negative_are_rejected(self):
        with DurableTwoAgents(self.path) as sim:
            sim.step()
            before = sim.engine.snapshot()
            for bad in (Outcome(5, True, "fake"), Outcome(0, True, "fake"), Outcome(0, False)):
                with self.subTest(outcome=bad):
                    with self.assertRaisesRegex(ValueError, "completed recipient phase"):
                        sim.engine._receive(bad, source="notification")
                    self.assertEqual(sim.engine.snapshot(), before)

    def test_rehashed_budget_queue_or_receipt_tampering_is_rejected_before_projection(self):
        for field in ("budget", "channel", "receipt"):
            with self.subTest(field=field):
                path = Path(self.temp.name)/f"tamper-{field}.sqlite3"
                with DurableTwoAgents(path) as sim:
                    sim.step()
                with closing(sqlite3.connect(path)) as db, db:
                    body = json.loads(db.execute("SELECT body FROM durable_pair_journal").fetchone()[0])
                    if field == "budget":
                        body["state"]["budget"]["pending"] = []
                    elif field == "channel":
                        body["state"]["channel"] = []
                    else:
                        body["state"]["channel"][0]["receipt_digest"] = "forged"
                    encoded = canonical(body)
                    db.execute("UPDATE durable_pair_journal SET body=?,body_hash=?", (encoded, digest(encoded)))
                    # Model an interrupted projection as well: invalid history
                    # must never be used to restore even an otherwise valid lag.
                    db.execute("DELETE FROM exact_events")
                    db.execute("DELETE FROM agent_state")
                with self.assertRaisesRegex(ValueError, "journal replay mismatch"):
                    DurableTwoAgents(path)
                with closing(sqlite3.connect(path)) as db:
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM exact_events").fetchone()[0], 0)

    def test_corrupted_exact_or_predictive_memory_is_not_silently_rebuilt(self):
        for field in ("exact", "predictive"):
            with self.subTest(field=field):
                path = Path(self.temp.name)/f"corrupt-{field}.sqlite3"
                with DurableTwoAgents(path) as sim:
                    sim.step()
                with closing(sqlite3.connect(path)) as db, db:
                    if field == "exact":
                        db.execute("UPDATE exact_events SET payload=?", (b"corrupt",))
                    else:
                        state = json.loads(db.execute("SELECT state_json FROM agent_state").fetchone()[0])
                        state["successes"] = 999
                        db.execute("UPDATE agent_state SET state_json=?", (canonical(state),))
                with self.assertRaisesRegex(ValueError, "differs from authoritative journal"):
                    DurableTwoAgents(path)

    def test_unrelated_store_settings_mismatch_and_concurrent_writer_are_refused(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE unrelated (value TEXT)")
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "refusing to modify"):
            DurableTwoAgents(self.path)
        self.assertEqual(before, self.path.read_bytes())
        other = Path(self.temp.name)/"other.sqlite3"
        with DurableTwoAgents(other, config={"scenario": "hostile"}) as sim:
            self.path = other
            result = self.cli("--status", success=False)
            self.assertIn("another process", result.stderr)
        result = self.cli("--status", "--scenario", "cooperative", success=False)
        self.assertIn("settings differ", result.stderr)
        self.assertEqual(self.cli("--status")["round"], 0)
        self.assertEqual(self.cli("--status", "--scenario", "hostile")["settings"]["scenario"], "hostile")

    def test_partial_cross_agent_projection_is_refused_without_repair(self):
        with DurableTwoAgents(self.path, config={"delay": 0, "drop_every": 0}) as sim:
            for _ in range(3):
                sim.step()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("DELETE FROM agent_state WHERE agent_id='A'")
            db.execute("DELETE FROM exact_events WHERE agent_id='A'")
        with self.assertRaisesRegex(ValueError, "atomic round boundary"):
            DurableTwoAgents(self.path)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM exact_events").fetchone()[0], 3)

    def test_bounds_and_missing_status_do_not_create_history(self):
        self.cli("--status", success=False)
        self.assertFalse(self.path.exists())
        for config in ({"mode": "unsafe_timeout"}, {"delay": 3}, {"seed": -1}, {"policy": "invent"}):
            with self.assertRaises(ValueError):
                settings(**config)
        self.cli("--rounds", "20")
        before = self.cli("--status")
        self.cli("--rounds", "1", success=False)
        self.assertEqual(self.cli("--status")["world_sha256"], before["world_sha256"])


if __name__ == "__main__":
    unittest.main()
