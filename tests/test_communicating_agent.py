"""Unit, behavioral, and adversarial security tests for communicating_agent.py."""
from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples"))

from communicating_agent import (
    AgentGenome,
    AgentIdentity,
    BoundedCommunicationHub,
    CommunicatingAgent,
    DEFAULT_OWNER,
    MAX_PAYLOAD_BYTES,
    MessageDraft,
    Performative,
    SCHEMA_VERSION,
    TransferDraft,
    run_communication_session,
)
from openworld_superkernel.hyper_memory_p1e import HyperMemoryP1e
from openworld_superkernel.memory_contracts import Provenance
from openworld_superkernel.risk_budget import CAP
from openworld_superkernel.world_fixture import Agent, create_world


class CommunicatingAgentScenarioTests(unittest.TestCase):
    def test_cooperative_session_replays_conserves_and_isolates_inferred_notes(self):
        result = run_communication_session(scenario="cooperative", rounds=6, seed=2026)
        self.assertEqual(result["schema"], SCHEMA_VERSION)
        self.assertTrue(result["replay_verified"])
        self.assertEqual(result["provenance"], "simulated")
        self.assertEqual(result["initial_total_resources"], 14)
        self.assertEqual(result["final_total_resources"], 14)
        self.assertEqual(result["balances"], {"alice": 8, "bob": 2, "carol": 4})

        alice = result["agents"]["alice"]
        bob = result["agents"]["bob"]
        carol = result["agents"]["carol"]
        # Multiple identities share one policy reference without sharing memory.
        self.assertEqual(
            alice["identity"]["model_ref"], bob["identity"]["model_ref"]
        )
        self.assertEqual(alice["risk_budget"]["known_loss"], 0)
        self.assertEqual(alice["risk_budget"]["exposure"], 0)
        self.assertEqual(alice["memory_prediction"]["observations"], 6)
        self.assertEqual(alice["memory_prediction"]["successes"], 6)
        self.assertEqual(alice["memory_prediction"]["provenance"], "inferred")
        self.assertEqual(alice["relationships"]["bob"]["returns_confirmed"], 6)

        # Carol receives INFERRED reputation notes without mutating her direct memory.
        self.assertEqual(carol["memory_prediction"]["observations"], 0)
        self.assertEqual(
            carol["relationships"]["bob"]["inferred_notes_count"], 6
        )
        self.assertEqual(
            carol["relationships"]["bob"]["last_inferred_note"]["claim_provenance"],
            "inferred",
        )

    def test_hostile_refuse_causes_zero_loss_through_dialogue(self):
        result = run_communication_session(
            scenario="hostile_refuse", rounds=8, probe_interval=4, seed=2026
        )
        self.assertTrue(result["replay_verified"])
        self.assertEqual(result["balances"], {"alice": 8, "bob": 2, "carol": 4})
        alice = result["agents"]["alice"]
        self.assertEqual(alice["risk_budget"]["known_loss"], 0)
        self.assertEqual(alice["risk_budget"]["peak_exposure"], 0)
        self.assertEqual(alice["relationships"]["bob"]["transfers_sent"], 0)
        self.assertGreaterEqual(alice["relationships"]["bob"]["proposals_declined"], 2)

    def test_hostile_liar_fake_ack_and_injection_caught_and_capped(self):
        result = run_communication_session(
            scenario="hostile_liar", rounds=20, probe_interval=2, seed=2026
        )
        self.assertTrue(result["replay_verified"])
        self.assertEqual(result["final_total_resources"], 14)
        alice = result["agents"]["alice"]
        rel_bob = alice["relationships"]["bob"]
        # Alice catches every false COMMIT_ACK via authoritative W3 receipt lookup.
        self.assertEqual(rel_bob["transfers_sent"], CAP)
        self.assertEqual(rel_bob["returns_confirmed"], 0)
        self.assertEqual(rel_bob["unreturned_losses"], CAP)
        self.assertEqual(rel_bob["unverified_acks_rejected"], CAP)
        # Hard cap holds even with aggressive probe_interval and payload injection.
        self.assertEqual(alice["risk_budget"]["known_loss"], CAP)
        self.assertLessEqual(alice["risk_budget"]["peak_exposure"], CAP)
        self.assertEqual(result["balances"]["alice"], 8 - CAP)
        self.assertEqual(result["balances"]["bob"], 2 + CAP)

    def test_recovery_detects_regime_shift_and_switches_hm_p1e_to_fast(self):
        result = run_communication_session(
            scenario="recovery",
            rounds=20,
            recover_at=10,
            probe_interval=2,
            seed=2026,
        )
        self.assertTrue(result["replay_verified"])
        self.assertEqual(result["balances"], {"alice": 8, "bob": 2, "carol": 4})
        alice = result["agents"]["alice"]
        self.assertEqual(alice["risk_budget"]["known_loss"], 0)
        self.assertGreaterEqual(alice["relationships"]["bob"]["returns_confirmed"], 8)
        # HM-P1e cost-aware gate adapts from static to fast after regime shift.
        self.assertEqual(alice["memory_prediction"]["estimator"], "fast")
        self.assertGreater(alice["memory_prediction"]["probability"], 0.7)

    def test_deterministic_world_fingerprint_across_identical_runs(self):
        first = run_communication_session(scenario="recovery", rounds=10, seed=77)
        second = run_communication_session(scenario="recovery", rounds=10, seed=77)
        self.assertEqual(first["world_fingerprint"], second["world_fingerprint"])
        self.assertEqual(first["trace"], second["trace"])
        self.assertEqual(first["balances"], second["balances"])

    def test_sqlite_persistence_and_refusal_to_overwrite_existing_db(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "comm-agents.sqlite3"
            result = run_communication_session(
                scenario="cooperative", rounds=3, db_path=db_path
            )
            self.assertTrue(db_path.is_file())
            with closing(sqlite3.connect(db_path)) as db:
                exact_rows = db.execute(
                    "SELECT owner_id, agent_id, provenance FROM exact_events"
                ).fetchall()
                self.assertEqual(len(exact_rows), result["exact_memory_events"])
                self.assertTrue(all(r[2] == "simulated" for r in exact_rows))
                # Carol only received INFERRED INFORM notes, never exact observations.
                self.assertTrue(all(r[1] in {"alice", "bob"} for r in exact_rows))
            with self.assertRaises(FileExistsError):
                run_communication_session(
                    scenario="cooperative", rounds=3, db_path=db_path
                )

    def test_cli_json_output_matches_schema(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "examples/communicating_agent.py"),
                "--scenario",
                "hostile_liar",
                "--rounds",
                "4",
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["schema"], SCHEMA_VERSION)
        self.assertTrue(payload["replay_verified"])
        self.assertEqual(payload["scenario"], "hostile_liar")


class CommunicatingAgentSecurityNegativeTests(unittest.TestCase):
    def _build_hub(self, *, cross_owner: bool = False):
        bob_owner = "other-owner" if cross_owner else DEFAULT_OWNER
        world = create_world(
            (
                Agent("alice", DEFAULT_OWNER, "north", 5),
                Agent("bob", bob_owner, "north", 5),
                Agent("carol", DEFAULT_OWNER, "south", 5),
            ),
            (("alice", "bob"), ("alice", "carol")),
            seed=42,
        )
        return BoundedCommunicationHub(world)

    def test_cross_owner_communication_denied_with_zero_mutation(self):
        hub = self._build_hub(cross_owner=True)
        alice_write = hub.issue_capability("alice", action="write_agent")
        before_fp = hub.world.fingerprint()
        draft = MessageDraft(
            message_id="cross-owner-1",
            thread_id="t-1",
            sender_id="alice",
            receiver_id="bob",
            performative=Performative.PING,
            payload={"hello": "bob"},
            claim_provenance=Provenance.SIMULATED,
        )
        with self.assertRaises(PermissionError):
            hub.dispatch_tick(messages=((draft, alice_write),))
        self.assertEqual(hub.world.tick, 0)
        self.assertEqual(hub.world.fingerprint(), before_fp)
        self.assertEqual(len(hub.message_log), 0)

    def test_non_neighbor_message_denied_before_world_mutation(self):
        hub = self._build_hub()
        bob_write = hub.issue_capability("bob", action="write_agent")
        before_fp = hub.world.fingerprint()
        draft = MessageDraft(
            message_id="non-neighbor-1",
            thread_id="t-nn",
            sender_id="bob",
            receiver_id="carol",
            performative=Performative.PING,
            payload={"msg": "bypass graph"},
            claim_provenance=Provenance.SIMULATED,
        )
        with self.assertRaises(PermissionError):
            hub.dispatch_tick(messages=((draft, bob_write),))
        self.assertEqual(hub.world.tick, 0)
        self.assertEqual(hub.world.fingerprint(), before_fp)

    def test_revoked_write_and_read_capabilities_fail_closed(self):
        hub = self._build_hub()
        write_cap = hub.issue_capability(
            "alice", action="write_agent", nonce="write-nonce-1"
        )
        read_cap = hub.issue_capability(
            "bob", action="read_world", nonce="read-nonce-1"
        )
        hub.revoke_capability("write-nonce-1")
        draft = MessageDraft(
            message_id="revoked-1",
            thread_id="t-rev",
            sender_id="alice",
            receiver_id="bob",
            performative=Performative.PING,
            payload={"ping": 1},
            claim_provenance=Provenance.SIMULATED,
        )
        with self.assertRaises(PermissionError):
            hub.dispatch_tick(messages=((draft, write_cap),))

        hub.revoke_capability("read-nonce-1")
        with self.assertRaises(PermissionError):
            hub.read_inbox("bob", read_capability=read_cap)

    def test_cross_agent_capability_token_misuse_denied(self):
        hub = self._build_hub()
        bob_write = hub.issue_capability("bob", action="write_agent")
        bob_read = hub.issue_capability("bob", action="read_world")
        draft = MessageDraft(
            message_id="impersonate-1",
            thread_id="t-imp",
            sender_id="alice",
            receiver_id="bob",
            performative=Performative.PING,
            payload={"spoof": True},
            claim_provenance=Provenance.SIMULATED,
        )
        with self.assertRaises(PermissionError):
            hub.dispatch_tick(messages=((draft, bob_write),))
        with self.assertRaises(PermissionError):
            hub.read_inbox("alice", read_capability=bob_read)

    def test_provenance_promotion_to_verified_or_observed_rejected(self):
        hub = self._build_hub()
        alice_write = hub.issue_capability("alice", action="write_agent")
        for forbidden in (
            Provenance.VERIFIED,
            Provenance.OBSERVED_RECORDED,
            Provenance.UNAVAILABLE,
        ):
            with self.subTest(provenance=forbidden):
                draft = MessageDraft(
                    message_id=f"bad-prov-{forbidden.value}",
                    thread_id="t-prov",
                    sender_id="alice",
                    receiver_id="bob",
                    performative=Performative.INFORM,
                    payload={"claim": "fake verified fact"},
                    claim_provenance=forbidden,
                )
                with self.assertRaises(ValueError):
                    hub.dispatch_tick(messages=((draft, alice_write),))

    def test_duplicate_message_id_replay_rejected(self):
        hub = self._build_hub()
        alice_write = hub.issue_capability("alice", action="write_agent")
        draft = MessageDraft(
            message_id="dup-1",
            thread_id="t-dup",
            sender_id="alice",
            receiver_id="bob",
            performative=Performative.PING,
            payload={"seq": 1},
            claim_provenance=Provenance.SIMULATED,
        )
        hub.dispatch_tick(messages=((draft, alice_write),))
        with self.assertRaises(ValueError):
            hub.dispatch_tick(messages=((draft, alice_write),))

    def test_oversized_payload_nan_and_quota_exceeded_rejected(self):
        hub = BoundedCommunicationHub(
            create_world(
                (
                    Agent("alice", DEFAULT_OWNER, "north", 5),
                    Agent("bob", DEFAULT_OWNER, "north", 5),
                ),
                (("alice", "bob"),),
                seed=7,
            ),
            max_actions_per_tick=1,
        )
        alice_write = hub.issue_capability("alice", action="write_agent")
        oversized = MessageDraft(
            message_id="big-1",
            thread_id="t-big",
            sender_id="alice",
            receiver_id="bob",
            performative=Performative.INFORM,
            payload={"blob": "x" * (MAX_PAYLOAD_BYTES + 10)},
            claim_provenance=Provenance.INFERRED,
        )
        with self.assertRaises(ValueError):
            hub.dispatch_tick(messages=((oversized, alice_write),))

        nan_draft = MessageDraft(
            message_id="nan-1",
            thread_id="t-nan",
            sender_id="alice",
            receiver_id="bob",
            performative=Performative.INFORM,
            payload={"score": float("nan")},
            claim_provenance=Provenance.INFERRED,
        )
        with self.assertRaises(ValueError):
            hub.dispatch_tick(messages=((nan_draft, alice_write),))

        # Quota of 1 action/tick denies 2 simultaneous messages before W3 runs.
        m1 = MessageDraft(
            "q-1", "t-q", "alice", "bob", Performative.PING, {"i": 1}
        )
        m2 = MessageDraft(
            "q-2", "t-q", "alice", "bob", Performative.PING, {"i": 2}
        )
        with self.assertRaises(ValueError):
            hub.dispatch_tick(messages=((m1, alice_write), (m2, alice_write)))
        self.assertEqual(hub.world.tick, 0)

    def test_atomic_batch_precheck_rejects_all_when_second_item_fails(self):
        hub = self._build_hub()
        alice_write = hub.issue_capability("alice", action="write_agent")
        bob_write = hub.issue_capability("bob", action="write_agent")
        valid_msg = MessageDraft(
            "ok-1", "t-ok", "alice", "bob", Performative.PING, {"ok": True}
        )
        invalid_non_neighbor = MessageDraft(
            "bad-2", "t-bad", "bob", "carol", Performative.PING, {"ok": False}
        )
        with self.assertRaises(PermissionError):
            hub.dispatch_tick(
                messages=((valid_msg, alice_write), (invalid_non_neighbor, bob_write))
            )
        # First valid message did NOT leak into W3 or inbox.
        self.assertEqual(hub.world.tick, 0)
        self.assertEqual(len(hub.message_log), 0)

    def test_agent_memory_owner_isolation_and_transfer_validation(self):
        with HyperMemoryP1e(":memory:") as memory:
            alice = CommunicatingAgent(
                AgentIdentity("alice", DEFAULT_OWNER, "north"),
                AgentGenome(role="negotiator", strategy="adaptive"),
                memory,
            )
            alice.record_exact_outcome(
                event_id="evt-alice-1",
                event_type="simulated_exchange_settlement",
                outcome=1,
                evidence={"round": 0},
            )
            with self.assertRaises(PermissionError):
                memory.get_state(
                    owner_id=DEFAULT_OWNER,
                    agent_id="alice",
                    requester_owner_id="intruder-owner",
                )
        with self.assertRaises(ValueError):
            TransferDraft("tx-1", "alice", "alice", 1, "t-1").validate()
        with self.assertRaises(ValueError):
            TransferDraft("tx-2", "alice", "bob", 0, "t-1").validate()


if __name__ == "__main__":
    unittest.main()
