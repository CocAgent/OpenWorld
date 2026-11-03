"""Synthetic migration rehearsal: small smoke and a bounded 20k-row CI trial."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
from hm_migration_rehearsal import SCHEMA, run


class SyntheticMigrationRehearsalTests(unittest.TestCase):
    def test_small_rehearsal_preserves_byte_and_owner_invariants(self):
        report = run(events=300, owners=3, agents_per_owner=2,
                     payload_bytes=1024)
        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["parameters"]["events"], 300)
        self.assertEqual(report["original_fingerprint"]["exact_event_count"], 300)
        self.assertEqual(report["original_fingerprint"]["agent_state_count"], 6)
        self.assertTrue(all(report["verified"].values()))
        self.assertEqual(report["status"],
                         "PASS: disposable synthetic migration rehearsal ONLY")
        for kind in ("source_initial", "migrated_online",
                     "migrated_after_checkpoint", "preserved_backup"):
            self.assertGreater(report["disk_bytes"][kind]["db"], 0)

    def test_bad_and_unbounded_input_rejected(self):
        for options in (
            {"events": True}, {"events": 99}, {"events": 100001},
            {"owners": 1}, {"owners": 33},
            {"agents_per_owner": 0}, {"agents_per_owner": 17},
            {"payload_bytes": 1023}, {"payload_bytes": 8193},
            {"payload_bytes": False},
        ):
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    run(**options)

    def test_one_command_cli_writes_new_report_only(self):
        with tempfile.TemporaryDirectory(prefix="openworld-migration-test-") as d:
            target = Path(d) / "measured.json"
            command = [
                sys.executable, str(ROOT / "benchmarks" / "hm_migration_rehearsal.py"),
                "--events", "200", "--owners", "2",
                "--agents-per-owner", "2", "--payload-bytes", "1024",
                "--out", str(target),
            ]
            proc = subprocess.run(command, cwd=ROOT, capture_output=True,
                                  text=True, timeout=90, check=True)
            report = json.loads(proc.stdout)
            self.assertEqual(report["original_fingerprint"]["exact_event_count"], 200)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), report)
            original = target.read_bytes()
            denied = subprocess.run(command, cwd=ROOT, capture_output=True,
                                    text=True, timeout=90)
            self.assertNotEqual(denied.returncode, 0)
            self.assertEqual(target.read_bytes(), original)

    @unittest.skipUnless(
        os.environ.get("OPENWORLD_SLOW_TESTS") == "1",
        "20k synthetic migration rehearsal only in full CI or explicitly opt-in",
    )
    def test_twenty_thousand_event_migration_rehearsal(self):
        report = run(events=20000, owners=12, agents_per_owner=4,
                     payload_bytes=2048)
        self.assertEqual(report["original_fingerprint"]["exact_event_count"], 20000)
        self.assertEqual(report["original_fingerprint"]["agent_state_count"], 48)
        self.assertTrue(all(report["verified"].values()))
        self.assertGreater(report["timings_seconds"]["explicit_migration_wall"], 0)
        self.assertGreater(report["disk_bytes"]["source_initial"]["db"], 0)
        original = json.dumps(report, sort_keys=True, separators=(",", ":"),
                              allow_nan=False)
        print(
            "OPENWORLD_HM_MIGRATION_SYNTHETIC_20K_SHA256="
            + hashlib.sha256(original.encode("utf-8")).hexdigest(),
            flush=True,
        )
        print("OPENWORLD_HM_MIGRATION_SYNTHETIC_20K_JSON=" + original,
              flush=True)


if __name__ == "__main__":
    unittest.main()
