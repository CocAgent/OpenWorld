"""Restart, exact-evidence recovery and failure controls for the persistent demo."""
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
from persistent_agents import PersistentSimulation, canonical, digest


class PersistentAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "world.sqlite3"

    def cli(self, *options):
        result = subprocess.run([sys.executable, str(ROOT/"examples/persistent_agents.py"),
                                 "--db", str(self.path), *options],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_two_separate_processes_resume_both_agents_without_duplicate_events(self):
        first = self.cli("--steps", "3")
        second = self.cli("--steps", "3")
        self.assertEqual((first["resumed_from_tick"], first["tick"]), (0, 3))
        self.assertEqual((second["resumed_from_tick"], second["tick"]), (3, 6))
        self.assertEqual(second["exact_events"], 6)
        self.assertEqual(second["memory"]["alice"]["observations"], 3)
        self.assertEqual(second["memory"]["bob"]["observations"], 3)
        self.assertEqual(sum(second["balances"].values()), 6)
        self.assertEqual(second["world_replay"], "PASS")

    def test_restarted_world_and_memory_match_uninterrupted_run(self):
        with PersistentSimulation(self.path) as sim:
            for _ in range(3):
                sim.step()
        with PersistentSimulation(self.path) as sim:
            for _ in range(3):
                sim.step()
            resumed = sim.status(history=True)
        with PersistentSimulation(Path(self.temp.name)/"reference.sqlite3") as sim:
            for _ in range(6):
                sim.step()
            uninterrupted = sim.status(history=True)
        for field in ("tick", "balances", "memory", "exact_events", "history", "world_sha256"):
            self.assertEqual(resumed[field], uninterrupted[field], field)

    def test_status_and_history_add_no_actions_or_training(self):
        first = self.cli("--steps", "3")
        status = self.cli("--status", "--history")
        self.assertEqual(status["new_cycles"], [])
        self.assertEqual(len(status["history"]), 3)
        for field in ("tick", "memory", "exact_events", "world_sha256"):
            self.assertEqual(first[field], status[field])

    def test_restart_after_adaptive_predictor_warmup_matches_one_continuous_run(self):
        with PersistentSimulation(self.path) as sim:
            for _ in range(24):
                sim.step()
        with PersistentSimulation(self.path) as sim:
            for _ in range(6):
                sim.step()
            restarted = sim.status()
        with PersistentSimulation(Path(self.temp.name)/"continuous.sqlite3") as sim:
            for _ in range(30):
                sim.step()
            continuous = sim.status()
        self.assertEqual(restarted["memory"], continuous["memory"])
        self.assertEqual(restarted["world_sha256"], continuous["world_sha256"])
        self.assertEqual(restarted["memory"]["alice"]["observations"], 15)
        self.assertEqual(restarted["memory"]["bob"]["observations"], 15)

    def test_failed_uncommitted_journal_leaves_no_world_or_memory_effect(self):
        class FailBeforeCommit(PersistentSimulation):
            def _before_journal_commit(self):
                raise RuntimeError("injected journal failure")
        with FailBeforeCommit(self.path) as sim:
            with self.assertRaisesRegex(RuntimeError, "injected"):
                sim.step()
        with PersistentSimulation(self.path) as sim:
            self.assertEqual(sim.status()["tick"], 0)
            self.assertEqual(sim.status()["exact_events"], 0)

    def test_process_exit_after_journal_commit_recovers_missing_memory_exactly_once(self):
        code = "\n".join([
            "import os, sys",
            "sys.path.insert(0, sys.argv[1])",
            "from persistent_agents import PersistentSimulation",
            "class Crash(PersistentSimulation):",
            "    def _after_journal_commit(self): os._exit(23)",
            "with Crash(sys.argv[2]) as simulation: simulation.step()",
        ])
        crashed = subprocess.run([sys.executable, "-c", code, str(ROOT/"examples"), str(self.path)],
                                 capture_output=True, text=True, timeout=30)
        self.assertEqual(crashed.returncode, 23, crashed.stderr)
        recovered = self.cli("--status")
        self.assertEqual(recovered["tick"], 1)
        self.assertEqual(recovered["exact_events"], 1)
        self.assertEqual(recovered["recovered_memory_events"], 1)
        reopened = self.cli("--status")
        self.assertEqual(reopened["recovered_memory_events"], 0)
        self.assertEqual(reopened["exact_events"], 1)
        self.assertEqual(reopened["memory"], recovered["memory"])

    def test_tampered_journal_stops_before_extending_memory(self):
        with PersistentSimulation(self.path) as sim:
            sim.step()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE persistent_demo_journal SET body='{}'")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            PersistentSimulation(self.path)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM exact_events").fetchone()[0], 1)

    def test_exit_after_memory_commit_does_not_duplicate_training_on_reopen(self):
        code = "\n".join([
            "import os, sys",
            "sys.path.insert(0, sys.argv[1])",
            "from persistent_agents import PersistentSimulation",
            "with PersistentSimulation(sys.argv[2]) as simulation:",
            "    simulation.step()",
            "    os._exit(24)",
        ])
        crashed = subprocess.run([sys.executable, "-c", code, str(ROOT/"examples"), str(self.path)],
                                 capture_output=True, text=True, timeout=30)
        self.assertEqual(crashed.returncode, 24, crashed.stderr)
        status = self.cli("--status")
        self.assertEqual(status["tick"], 1)
        self.assertEqual(status["exact_events"], 1)
        self.assertEqual(status["recovered_memory_events"], 0)
        self.assertEqual(status["memory"]["alice"]["observations"], 1)

    def test_rehashed_false_history_still_fails_policy_and_world_replay(self):
        with PersistentSimulation(self.path) as sim:
            sim.step()
        with closing(sqlite3.connect(self.path)) as db, db:
            record = json.loads(db.execute("SELECT body FROM persistent_demo_journal WHERE tick=0").fetchone()[0])
            payload = json.loads(record["payload"])
            payload["action"]["amount"] = 100
            record["payload"] = canonical(payload)
            body = canonical(record)
            db.execute("UPDATE persistent_demo_journal SET body=?,body_hash=? WHERE tick=0", (body, digest(body)))
        with self.assertRaisesRegex(ValueError, "replay mismatch"):
            PersistentSimulation(self.path)

    def test_corrupted_materialized_exact_event_is_not_silently_regenerated(self):
        with PersistentSimulation(self.path) as sim:
            sim.step()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE exact_events SET payload=?", (b"tampered",))
        with self.assertRaisesRegex(ValueError, "exact event differs"):
            PersistentSimulation(self.path)

    def test_corrupted_predictive_state_is_not_silently_regenerated(self):
        with PersistentSimulation(self.path) as sim:
            sim.step()
        with closing(sqlite3.connect(self.path)) as db, db:
            state = json.loads(db.execute("SELECT state_json FROM agent_state WHERE agent_id='alice'").fetchone()[0])
            state["successes"] = 999
            db.execute("UPDATE agent_state SET state_json=? WHERE agent_id='alice'", (json.dumps(state),))
        with self.assertRaisesRegex(ValueError, "predictive state differs"):
            PersistentSimulation(self.path)

    def test_existing_unrelated_database_is_refused_without_mutation(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE unrelated (value TEXT)")
            db.execute("INSERT INTO unrelated VALUES('synthetic-fixture')")
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "refusing to modify"):
            PersistentSimulation(self.path)
        self.assertEqual(self.path.read_bytes(), before)

    def test_concurrent_example_process_is_denied_and_lock_releases_on_close(self):
        with PersistentSimulation(self.path):
            attempted = subprocess.run([sys.executable, str(ROOT/"examples/persistent_agents.py"),
                                        "--db", str(self.path), "--status"],
                                       capture_output=True, text=True, timeout=30)
            self.assertNotEqual(attempted.returncode, 0)
            self.assertIn("another process", attempted.stderr)
        self.assertEqual(self.cli("--status")["tick"], 0)

    def test_missing_status_does_not_create_database(self):
        with self.assertRaises(FileNotFoundError):
            PersistentSimulation(self.path, create=False)
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
