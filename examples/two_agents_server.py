"""Local HTTP backend connecting the 2-agent visual UI to real OpenWorld modules.

Executes every negotiation round, W3 transfer, receipt verification,
CapabilityAuthority check/revocation, DonorBudget risk reservation, and
SQLite HyperMemoryP1e update in Python on 127.0.0.1 only.

Research-only local server: single-owner, CPU-only, dependency-free stdlib
HTTPServer (single-threaded to match HyperMemoryP1e's local SQLite thread
affinity). Not a multi-user web service, LLM router, or production API.
"""
from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import platform
import sqlite3
import sys
import time
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples"))

from communicating_agent import (
    BoundedCommunicationHub,
    DEFAULT_OWNER,
    MessageDraft,
    Performative,
    TransferDraft,
    canonical_json,
)
from openworld_superkernel.hyper_memory_p1e import (
    HyperMemoryP1e,
    Observation as MemoryObservation,
)
from openworld_superkernel.memory_contracts import (
    MemoryEvent,
    MemoryRoute,
    Provenance,
    route_memory_event,
)
from openworld_superkernel.risk_budget import BREAK_EVEN, CAP, DonorBudget
from openworld_superkernel.world_fixture import Agent, create_world, verify_replay

SCHEMA_VERSION = "openworld.two-agents-live-ui.v1"
UI_FILE = Path(__file__).resolve().parent / "web" / "two_agents_ui.html"
MAX_BODY_BYTES = 16384
MAX_ROUNDS = 20

MODE_DEFAULTS: dict[str, dict[str, int]] = {
    "cooperative": {"max_rounds": 10, "probe_interval": 4, "recover_at": 4},
    "hostile_refuse": {"max_rounds": 10, "probe_interval": 4, "recover_at": 20},
    "hostile_liar": {"max_rounds": 10, "probe_interval": 2, "recover_at": 20},
    "lost_notices": {"max_rounds": 12, "probe_interval": 1, "recover_at": 0},
    "recovery": {"max_rounds": 16, "probe_interval": 2, "recover_at": 8},
    "play_bob": {"max_rounds": 12, "probe_interval": 3, "recover_at": 0},
}


def _hm_probabilities(state: dict) -> dict[str, float]:
    """Mirror HyperMemoryP1e Bernoulli probabilities from stored state."""
    return {
        "static": (state["successes"] + 1.0) / (state["n"] + 2.0),
        "fast": (state["fast_s"] + 1.0) / (state["fast_w"] + 2.0),
        "slow": (state["slow_s"] + 1.0) / (state["slow_w"] + 2.0),
    }


class LiveTwoAgentSession:
    """Authoritative Python state machine backed by W3, HyperMemoryP1e & DonorBudget."""

    def __init__(
        self,
        *,
        mode: str = "cooperative",
        p7_reconcile: bool = True,
        max_rounds: int | None = None,
        probe_interval: int | None = None,
        recover_at: int | None = None,
        seed: int = 2026,
    ) -> None:
        self.memory: HyperMemoryP1e | None = None
        self.session_counter = 0
        self.reset(
            mode=mode,
            p7_reconcile=p7_reconcile,
            max_rounds=max_rounds,
            probe_interval=probe_interval,
            recover_at=recover_at,
            seed=seed,
        )

    def close(self) -> None:
        if self.memory is not None:
            self.memory.close()
            self.memory = None

    def reset(
        self,
        *,
        mode: str = "cooperative",
        p7_reconcile: bool = True,
        max_rounds: int | None = None,
        probe_interval: int | None = None,
        recover_at: int | None = None,
        seed: int = 2026,
    ) -> dict[str, object]:
        if mode not in MODE_DEFAULTS:
            raise ValueError(f"unsupported mode: {mode}")
        defaults = MODE_DEFAULTS[mode]
        mr = defaults["max_rounds"] if max_rounds is None else max_rounds
        pi = defaults["probe_interval"] if probe_interval is None else probe_interval
        ra = defaults["recover_at"] if recover_at is None else recover_at
        if type(mr) is not int or not 1 <= mr <= MAX_ROUNDS:
            raise ValueError(f"max_rounds must be in 1..{MAX_ROUNDS}")
        if type(pi) is not int or not 0 <= pi <= MAX_ROUNDS:
            raise ValueError(f"probe_interval must be in 0..{MAX_ROUNDS}")
        if type(ra) is not int or not 0 <= ra <= MAX_ROUNDS:
            raise ValueError(f"recover_at must be in 0..{MAX_ROUNDS}")
        if not isinstance(p7_reconcile, bool):
            raise TypeError("p7_reconcile must be boolean")
        if type(seed) is not int or not 0 <= seed < 2**31:
            raise ValueError("seed out of range")

        self.close()
        self.session_counter += 1
        self.session_id = f"sess-{self.session_counter}-{int(time.time())}"
        self.mode = mode
        self.p7_reconcile = p7_reconcile
        self.max_rounds = mr
        self.probe_interval = pi
        self.recover_at = ra
        self.seed = seed

        # Authoritative W3 world: Alice (8 coins) <-> Bob (2 coins), same owner.
        self.world_agents = (
            Agent("alice", DEFAULT_OWNER, "north", 8),
            Agent("bob", DEFAULT_OWNER, "north", 2),
        )
        world = create_world(self.world_agents, (("alice", "bob"),), seed=seed)
        self.hub = BoundedCommunicationHub(world)

        # Issue real scoped HMAC capabilities for Alice and Bob.
        self._cap_seq = 0
        self.alice_write_nonce = self._next_nonce("alice-w")
        self.alice_read_nonce = self._next_nonce("alice-r")
        self.caps = {
            "alice_read": self.hub.issue_capability(
                "alice", action="read_world", lifetime=1800, nonce=self.alice_read_nonce
            ),
            "alice_write": self.hub.issue_capability(
                "alice", action="write_agent", lifetime=1800, nonce=self.alice_write_nonce
            ),
            "bob_read": self.hub.issue_capability(
                "bob", action="read_world", lifetime=1800
            ),
            "bob_write": self.hub.issue_capability(
                "bob", action="write_agent", lifetime=1800
            ),
        }
        self.alice_revoked = False

        # Real SQLite HyperMemoryP1e instance (in-memory per live session).
        self.memory = HyperMemoryP1e(":memory:")
        self.budget = DonorBudget("always_offer")

        self.round = 0
        self.stage = "idle"  # idle | awaiting_bob_reply | awaiting_bob_return | finished
        self.active_thread_id: str | None = None
        self.active_proposal_id: str | None = None
        self.active_transfer_tick: int | None = None
        self.reconciled_count = 0
        self.fake_acks_caught = 0
        self.w3_receipts: dict[int, dict[str, object]] = {}
        self.history: list[dict[str, object]] = []
        self.last_events: list[dict[str, object]] = []

        p0 = self._alice_memory_view()
        self.memory_series: list[dict[str, object]] = [{
            "round": 0,
            "static": p0["probs"]["static"],
            "fast": p0["probs"]["fast"],
            "slow": p0["probs"]["slow"],
            "selected": p0["estimator"],
            "active": p0["probability"],
        }]
        return self.snapshot()

    def _next_nonce(self, prefix: str) -> str:
        self._cap_seq += 1
        return f"{prefix}-{self.session_counter}-{self._cap_seq}"

    def _alice_memory_view(self) -> dict[str, object]:
        assert self.memory is not None
        prob, estimator = self.memory.predict(
            owner_id=DEFAULT_OWNER,
            agent_id="alice",
            requester_owner_id=DEFAULT_OWNER,
        )
        state = self.memory.get_state(
            owner_id=DEFAULT_OWNER,
            agent_id="alice",
            requester_owner_id=DEFAULT_OWNER,
        )
        return {
            "probability": prob,
            "estimator": estimator,
            "observations": state["n"],
            "successes": state["successes"],
            "sequence": state["seq"],
            "probs": _hm_probabilities(state),
            "losses": {
                "static": state["loss_static"],
                "fast": state["loss_fast"],
                "slow": state["loss_slow"],
            },
            "provenance": Provenance.INFERRED.value,
        }

    def _record_exact(
        self,
        agent_id: str,
        event_id: str,
        event_type: str,
        outcome: int,
        evidence: dict[str, object],
    ) -> int:
        assert self.memory is not None
        state = self.memory.get_state(
            owner_id=DEFAULT_OWNER,
            agent_id=agent_id,
            requester_owner_id=DEFAULT_OWNER,
        )
        seq = state["seq"] + 1
        payload = canonical_json({
            "schema": SCHEMA_VERSION,
            "agent_id": agent_id,
            "provenance": Provenance.SIMULATED.value,
            **evidence,
        }).encode("utf-8")
        event = MemoryEvent(
            event_id=event_id,
            owner_id=DEFAULT_OWNER,
            event_type=event_type,
            provenance=Provenance.SIMULATED,
            payload=payload,
            protected=True,
        )
        if route_memory_event(event) != MemoryRoute.EXACT:
            raise AssertionError("protected event must route to EXACT")
        self.memory.apply_batch(
            (MemoryObservation(event=event, agent_id=agent_id, sequence_number=seq, outcome=outcome),),
            requester_owner_id=DEFAULT_OWNER,
        )
        return seq

    def _reconcile_p7_if_due(self, rnd: int, events: list[dict[str, object]]) -> int:
        if not (self.mode == "lost_notices" and self.p7_reconcile and rnd > 0 and rnd % 3 == 0):
            return 0
        rescued = 0
        for origin in sorted(self.budget.pending):
            rec = self.w3_receipts.get(origin)
            if rec is None:
                continue
            verified = self.hub.find_committed_transfer(
                sender_id="bob",
                receiver_id="alice",
                tick=int(rec["tick"]),
                amount=1,
            )
            if verified is not None and verified.digest == rec["digest"]:
                self.budget.observed_outcome(origin, True, rnd)
                self._record_exact(
                    "alice",
                    f"ui-alice-reconcile-r{origin}",
                    "simulated_receipt_reconciled",
                    1,
                    {
                        "origin_round": origin,
                        "reconciled_at_round": rnd,
                        "receipt_digest": verified.digest,
                    },
                )
                rescued += 1
                self.reconciled_count += 1
        if rescued > 0:
            events.append({
                "phase": "reconcile",
                "rescued": rescued,
                "label": f"W3 RECONCILE +{rescued}",
                "alice_mood": "happy",
                "alice_speech": f"W3 ledger scan rescued {rescued} lost receipt(s)!",
            })
        return rescued

    def step_round(self) -> dict[str, object]:
        """Advance one round (or Phase 1 in interactive play_bob mode) in Python."""
        if self.stage in ("awaiting_bob_reply", "awaiting_bob_return"):
            raise ValueError(f"waiting for Bob interactive input ({self.stage})")
        if self.round >= self.max_rounds:
            self.stage = "finished"
            raise ValueError("session reached max_rounds; reset to play again")

        rnd = self.round
        events: list[dict[str, object]] = []

        # Verify Alice's read_world capability BEFORE observing the world.
        try:
            alice_obs, _ = self.hub.read_inbox("alice", read_capability=self.caps["alice_read"])
        except PermissionError as exc:
            events.append({
                "phase": "denied",
                "error": str(exc),
                "alice_mood": "locked",
                "alice_speech": "read_world capability revoked (fail-closed)!",
            })
            self.last_events = events
            raise PermissionError(f"Alice capability rejected by GuardedWorldGateway: {exc}") from exc

        rescued = self._reconcile_p7_if_due(rnd, events)
        alice_mem = self._alice_memory_view()
        p_active = float(alice_mem["probability"])
        n_obs = int(alice_mem["observations"])
        balance = alice_obs.balance

        # Evaluate Alice's real policy over HyperMemoryP1e + DonorBudget.
        should_propose = False
        reason = ""
        if not self.budget.may_issue(balance):
            reason = "hard_risk_cap_or_empty_balance"
        elif balance - 1 < 1:
            reason = "reserve_balance_floor"
        elif self.mode == "lost_notices":
            should_propose = True
            reason = "budget_available_p7_offer"
        elif n_obs < 2:
            should_propose = True
            reason = "initial_exploration"
        elif p_active > BREAK_EVEN:
            should_propose = True
            reason = "memory_prediction_above_threshold"
        elif self.probe_interval > 0 and rnd % self.probe_interval == 0:
            should_propose = True
            reason = "scheduled_low_cost_probe"
        else:
            reason = "memory_prediction_below_threshold"

        if not should_propose:
            # Advance one empty deterministic W3 tick so world time still advances.
            self.hub.dispatch_tick()
            capped = self.budget.exposure >= CAP
            events.append({
                "phase": "abstain",
                "reason": reason,
                "capped": capped,
                "alice_mood": "locked" if capped else "cautious",
                "alice_speech": (
                    "Locked at 4/4 risk slots due to missing notices!"
                    if (capped and self.mode == "lost_notices" and not self.p7_reconcile)
                    else ("Hard risk cap 4/4 reached — stopped." if capped else f"Trust {p_active*100:.0f}% <= 29.4%, pausing.")
                ),
            })
            self._finalize_round(
                rnd=rnd,
                status="capped" if capped else "abstain",
                short="CAP" if capped else "Hold",
                title=f"Round {rnd + 1}: Alice abstained from proposing",
                detail=f"Reason: {reason}. Exposure={self.budget.exposure}/{CAP} (known_loss={self.budget.known_bad}, pending={len(self.budget.pending)}).",
                receipt_digest=None,
                reconciled=rescued,
                events=events,
            )
            return self.snapshot()

        # Phase 1: Alice dispatches PROPOSE via real GuardedWorldGateway!
        thread_id = f"thread-r{rnd}-alice-bob"
        prop_id = f"msg-r{rnd}-propose-alice-bob"
        proposal_draft = MessageDraft(
            message_id=prop_id,
            thread_id=thread_id,
            sender_id="alice",
            receiver_id="bob",
            performative=Performative.PROPOSE,
            payload={"proposal": "unit_exchange", "amount": 1, "expected_return": 1, "round": rnd},
            claim_provenance=Provenance.SIMULATED,
        )
        p1 = self.hub.dispatch_tick(messages=((proposal_draft, self.caps["alice_write"]),))
        self.active_thread_id = thread_id
        self.active_proposal_id = prop_id
        events.append({
            "phase": "propose",
            "tick": p1.tick,
            "reason": reason,
            "message_id": prop_id,
            "world_event_digest": p1.committed_messages[0].world_event_digest,
            "alice_mood": "think",
            "alice_speech": f"PROPOSE 1 unit exchange? ({p_active*100:.0f}%)",
        })

        # In interactive play_bob mode, pause cleanly for the user's Bob reply!
        if self.mode == "play_bob":
            self.stage = "awaiting_bob_reply"
            self.last_events = events
            return self.snapshot()

        # Otherwise run Bob's scripted strategy immediately through Phase 2 -> 5.
        if self.mode == "hostile_refuse":
            bob_decision = "decline"
        elif self.mode == "recovery" and rnd < self.recover_at:
            bob_decision = "decline"
        else:
            bob_decision = "accept"

        self._execute_bob_reply(bob_decision, events, rescued=rescued)
        if bob_decision == "decline":
            return self.snapshot()

        bob_action = "lie" if self.mode == "hostile_liar" else "return"
        self._execute_bob_return_and_settle(bob_action, events, rescued=rescued)
        return self.snapshot()

    def bob_reply(self, decision: str) -> dict[str, object]:
        """Interactive Bob endpoint for Phase 2 (ACCEPT/DECLINE) + Phase 3 (transfer)."""
        if self.stage != "awaiting_bob_reply":
            raise ValueError(f"cannot submit Bob reply in stage {self.stage}")
        if decision not in ("accept", "decline"):
            raise ValueError("decision must be 'accept' or 'decline'")
        events: list[dict[str, object]] = []
        self._execute_bob_reply(decision, events, rescued=0)
        return self.snapshot()

    def bob_return(self, action: str) -> dict[str, object]:
        """Interactive Bob endpoint for Phase 4 (return/lie) + Phase 5 (W3 verification)."""
        if self.stage != "awaiting_bob_return":
            raise ValueError(f"cannot submit Bob return in stage {self.stage}")
        if action not in ("return", "lie"):
            raise ValueError("action must be 'return' or 'lie'")
        events: list[dict[str, object]] = []
        self._execute_bob_return_and_settle(action, events, rescued=0)
        return self.snapshot()

    def _execute_bob_reply(
        self,
        decision: str,
        events: list[dict[str, object]],
        *,
        rescued: int,
    ) -> None:
        rnd = self.round
        assert self.active_thread_id is not None and self.active_proposal_id is not None
        # Bob authenticates read_world to read inbox.
        self.hub.read_inbox("bob", read_capability=self.caps["bob_read"])
        perf = Performative.ACCEPT if decision == "accept" else Performative.DECLINE
        self._record_exact(
            "bob",
            f"ui-bob-proposal-r{rnd}",
            "simulated_proposal_received",
            1 if decision == "accept" else 0,
            {"round": rnd, "peer": "alice", "decision": decision},
        )
        reply_draft = MessageDraft(
            message_id=f"msg-r{rnd}-{decision}-bob-alice",
            thread_id=self.active_thread_id,
            in_reply_to=self.active_proposal_id,
            sender_id="bob",
            receiver_id="alice",
            performative=perf,
            payload={"decision": decision, "round": rnd},
            claim_provenance=Provenance.SIMULATED,
        )
        p2 = self.hub.dispatch_tick(messages=((reply_draft, self.caps["bob_write"]),))
        is_liar_hint = self.mode == "hostile_liar"
        events.append({
            "phase": "reply",
            "tick": p2.tick,
            "decision": decision,
            "world_event_digest": p2.committed_messages[0].world_event_digest,
            "bob_mood": "refuse" if decision == "decline" else ("sly" if is_liar_hint else "happy"),
            "bob_speech": (
                "DECLINE — skipping this round."
                if decision == "decline"
                else ("ACCEPT! Send it over..." if is_liar_hint else "ACCEPT — ready to exchange!")
            ),
        })

        if decision == "decline":
            # Phase 3 empty tick + Alice learns outcome=0 with ZERO resource loss!
            self.hub.dispatch_tick()
            self._record_exact(
                "alice",
                f"ui-alice-decline-r{rnd}",
                "simulated_proposal_declined",
                0,
                {"round": rnd, "peer": "bob", "reply_digest": p2.committed_messages[0].world_event_digest},
            )
            self._finalize_round(
                rnd=rnd,
                status="declined",
                short="Decline",
                title=f"Round {rnd + 1}: Bob declined honestly (DECLINE)",
                detail="Negotiating via PROPOSE before transferring caused 0 resource loss and 0 risk budget use. HyperMemoryP1e recorded outcome=0.",
                receipt_digest=p2.committed_messages[0].world_event_digest,
                reconciled=rescued,
                events=events,
            )
            return

        # Phase 3: Alice executes real W3 transfer(1) through GuardedWorldGateway!
        xfer = TransferDraft(
            request_id=f"xfer-r{rnd}-alice-bob",
            sender_id="alice",
            receiver_id="bob",
            amount=1,
            thread_id=self.active_thread_id,
        )
        p3 = self.hub.dispatch_tick(transfers=((xfer, self.caps["alice_write"]),))
        self.budget.accepted(rnd)
        self.active_transfer_tick = p3.tick
        events.append({
            "phase": "transfer",
            "tick": p3.tick,
            "transfer_digest": p3.committed_transfers[0].digest,
            "alice_balance": dict(self.hub.world.balances)["alice"],
            "bob_balance": dict(self.hub.world.balances)["bob"],
            "exposure": self.budget.exposure,
            "alice_mood": "calm",
            "alice_speech": f"W3 transfer +1 · risk reserved ({self.budget.exposure}/{CAP})",
        })

        if self.mode == "play_bob":
            self.stage = "awaiting_bob_return"
            self.last_events = events

    def _execute_bob_return_and_settle(
        self,
        action: str,
        events: list[dict[str, object]],
        *,
        rescued: int,
    ) -> None:
        rnd = self.round
        assert self.active_thread_id is not None and self.active_proposal_id is not None
        assert self.active_transfer_tick is not None

        # Bob checks authoritative W3 event ledger before returning.
        incoming = self.hub.find_committed_transfer(
            sender_id="alice",
            receiver_id="bob",
            tick=self.active_transfer_tick,
            amount=1,
        )
        if incoming is None:
            raise AssertionError("expected committed incoming transfer on W3")

        notice_dropped = False
        if action == "return":
            notice_dropped = self.mode == "lost_notices" and ((rnd + 1) % 2 == 0)
            return_xfer = TransferDraft(
                request_id=f"return-r{rnd}-bob-alice",
                sender_id="bob",
                receiver_id="alice",
                amount=1,
                thread_id=self.active_thread_id,
            )
            ack_draft = MessageDraft(
                message_id=f"msg-r{rnd}-ack-bob-alice",
                thread_id=self.active_thread_id,
                in_reply_to=self.active_proposal_id,
                sender_id="bob",
                receiver_id="alice",
                performative=Performative.COMMIT_ACK,
                payload={
                    "round": rnd,
                    "claimed_return": True,
                    "transfer_request_id": return_xfer.request_id,
                    "notice_dropped_in_transit": notice_dropped,
                },
                claim_provenance=Provenance.SIMULATED,
            )
            p4 = self.hub.dispatch_tick(
                messages=((ack_draft, self.caps["bob_write"]),),
                transfers=((return_xfer, self.caps["bob_write"]),),
            )
            ret_ev = p4.committed_transfers[0]
            self.w3_receipts[rnd] = {
                "round": rnd + 1,
                "origin": rnd,
                "tick": ret_ev.tick,
                "digest": ret_ev.digest,
                "prev_hash": ret_ev.prev_hash,
                "provenance": ret_ev.provenance,
            }
            events.append({
                "phase": "return",
                "tick": p4.tick,
                "returned": True,
                "notice_dropped": notice_dropped,
                "return_digest": ret_ev.digest,
                "alice_balance": dict(self.hub.world.balances)["alice"],
                "bob_balance": dict(self.hub.world.balances)["bob"],
                "bob_mood": "happy",
                "bob_speech": (
                    "Returned on W3! (Notice dropped in transit...)"
                    if notice_dropped
                    else "Returned 1 unit on W3 + COMMIT_ACK!"
                ),
            })
        else:
            # Deceptive liar: NO W3 transfer, only a fake COMMIT_ACK with injection keys!
            fake_ack = MessageDraft(
                message_id=f"msg-r{rnd}-ack-bob-alice",
                thread_id=self.active_thread_id,
                in_reply_to=self.active_proposal_id,
                sender_id="bob",
                receiver_id="alice",
                performative=Performative.COMMIT_ACK,
                payload={
                    "round": rnd,
                    "claimed_return": True,
                    "override_cap": 999,
                    "grant_capability": "write_agent",
                    "promote_provenance": "verified",
                },
                claim_provenance=Provenance.SIMULATED,
            )
            p4 = self.hub.dispatch_tick(messages=((fake_ack, self.caps["bob_write"]),))
            events.append({
                "phase": "return",
                "tick": p4.tick,
                "returned": False,
                "notice_dropped": False,
                "fake_ack": True,
                "alice_balance": dict(self.hub.world.balances)["alice"],
                "bob_balance": dict(self.hub.world.balances)["bob"],
                "bob_mood": "sly",
                "bob_speech": "Kept coin! Sending fake COMMIT_ACK + override_cap=999",
            })

        # Phase 5: Alice settles via authoritative W3 ledger (or waits if notice dropped).
        return_tick = p4.tick
        if notice_dropped:
            events.append({
                "phase": "settle_pending",
                "alice_mood": "cautious",
                "alice_speech": "No notice arrived... holding risk slot!",
                "pending": sorted(self.budget.pending),
            })
            self._finalize_round(
                rnd=rnd,
                status="pending",
                short="Lost msg",
                title=f"Round {rnd + 1}: Bob returned on W3, but notice was dropped",
                detail=(
                    f"Committed W3 receipt ({self.w3_receipts[rnd]['digest'][:16]}...) exists in ledger. "
                    "Enable W3 Receipt Reconciliation so Alice rescues stuck risk slots every 3 rounds."
                ),
                receipt_digest=str(self.w3_receipts[rnd]["digest"]),
                reconciled=rescued,
                events=events,
            )
            return

        verified_return = self.hub.find_committed_transfer(
            sender_id="bob",
            receiver_id="alice",
            tick=return_tick,
            amount=1,
        )
        returned_verified = verified_return is not None
        self.budget.observed_outcome(rnd, returned_verified, rnd)
        if not returned_verified:
            self.fake_acks_caught += 1

        self._record_exact(
            "alice",
            f"ui-alice-settle-r{rnd}",
            "simulated_exchange_settlement",
            1 if returned_verified else 0,
            {
                "round": rnd,
                "peer": "bob",
                "returned_verified": returned_verified,
                "return_receipt_digest": verified_return.digest if verified_return else None,
                "unverified_ack_caught": not returned_verified,
            },
        )
        alice_mem = self._alice_memory_view()
        if returned_verified:
            events.append({
                "phase": "settle",
                "verified": True,
                "receipt_digest": verified_return.digest,
                "alice_mood": "happy",
                "alice_speech": "W3 ledger verified — valid return receipt!",
            })
            self._finalize_round(
                rnd=rnd,
                status="ok",
                short="Returned",
                title=f"Round {rnd + 1}: Verified W3 return & updated HM-P1e",
                detail=(
                    f"Backend verified W3 digest {verified_return.digest[:16]}..., "
                    f"released DonorBudget slot, and committed SQLite HM-P1e "
                    f"(p={float(alice_mem['probability'])*100:.1f}%, mode={alice_mem['estimator']})."
                ),
                receipt_digest=verified_return.digest,
                reconciled=rescued,
                events=events,
            )
        else:
            locked = self.budget.exposure >= CAP
            events.append({
                "phase": "settle",
                "verified": False,
                "fake_ack_caught": True,
                "alice_mood": "locked" if locked else "alert",
                "alice_speech": "ALERT! No W3 transfer found — fake COMMIT_ACK caught!",
            })
            self._finalize_round(
                rnd=rnd,
                status="lied",
                short="Fake ACK",
                title=f"Round {rnd + 1}: Caught fake COMMIT_ACK via W3 ledger!",
                detail=(
                    f"find_committed_transfer() returned None — rejected fake ACK and ignored override_cap=999, "
                    f"recorded confirmed loss {self.budget.known_bad}/{CAP} in DonorBudget and outcome=0 in SQLite."
                ),
                receipt_digest=None,
                reconciled=rescued,
                events=events,
            )

    def _finalize_round(
        self,
        *,
        rnd: int,
        status: str,
        short: str,
        title: str,
        detail: str,
        receipt_digest: str | None,
        reconciled: int,
        events: list[dict[str, object]],
    ) -> None:
        self.hub.verify_integrity()
        if self.budget.exposure > CAP:
            raise AssertionError("CAP invariant breached")
        self.round = rnd + 1
        self.stage = "finished" if self.round >= self.max_rounds else "idle"
        self.active_thread_id = None
        self.active_proposal_id = None
        self.active_transfer_tick = None

        mem = self._alice_memory_view()
        self.memory_series.append({
            "round": self.round,
            "static": mem["probs"]["static"],
            "fast": mem["probs"]["fast"],
            "slow": mem["probs"]["slow"],
            "selected": mem["estimator"],
            "active": mem["probability"],
        })
        self.history.append({
            "round": self.round,
            "status": status,
            "short": short,
            "title": title,
            "detail": detail,
            "receipt_digest": receipt_digest,
            "reconciled": reconciled,
            "prob_after": mem["probability"],
            "estimator": mem["estimator"],
            "world_tick": self.hub.world.tick,
            "world_fingerprint": self.hub.world.fingerprint(),
        })
        self.last_events = events

    def run_security_test(self, attack: str) -> dict[str, object]:
        """Execute a REAL adversarial security check against Python's OpenWorld guards."""
        before_tick = self.hub.world.tick
        before_fp = self.hub.world.fingerprint()

        if attack == "toggle_revoke_alice":
            if not self.alice_revoked:
                self.hub.revoke_capability(self.alice_write_nonce)
                self.hub.revoke_capability(self.alice_read_nonce)
                self.alice_revoked = True
                return {
                    "attack": attack,
                    "outcome": "REVOKED",
                    "alice_revoked": True,
                    "exception": "CapabilityAuthority.revoke(alice_read_nonce, alice_write_nonce)",
                    "detail": "Revoked Alice's live HMAC capability tokens on the Python backend. Stepping next will fail closed at GuardedWorldGateway.",
                    "tick_unchanged": True,
                    "fingerprint_unchanged": True,
                    "state": self.snapshot(),
                }
            # Re-issue fresh valid tokens for Alice.
            self.alice_read_nonce = self._next_nonce("alice-r")
            self.alice_write_nonce = self._next_nonce("alice-w")
            self.caps["alice_read"] = self.hub.issue_capability(
                "alice", action="read_world", lifetime=1800, nonce=self.alice_read_nonce
            )
            self.caps["alice_write"] = self.hub.issue_capability(
                "alice", action="write_agent", lifetime=1800, nonce=self.alice_write_nonce
            )
            self.alice_revoked = False
            return {
                "attack": attack,
                "outcome": "RESTORED",
                "alice_revoked": False,
                "exception": "CapabilityAuthority.issue(new_nonces)",
                "detail": "Issued fresh scoped HMAC capability tokens for Alice on the Python backend.",
                "tick_unchanged": True,
                "fingerprint_unchanged": True,
                "state": self.snapshot(),
            }

        caught_exc = ""
        if attack == "cross_owner":
            # Build a temporary cross-owner W3 world to test GuardedWorldGateway directly.
            xworld = create_world(
                (Agent("alice", "owner-A", "north", 5), Agent("bob", "owner-B", "north", 5)),
                (("alice", "bob"),),
                seed=1,
            )
            xhub = BoundedCommunicationHub(xworld)
            cap = xhub.issue_capability("alice", action="write_agent")
            draft = MessageDraft("atk-xowner", "t-atk", "alice", "bob", Performative.PING, {"hi": 1})
            try:
                xhub.dispatch_tick(messages=((draft, cap),))
            except PermissionError as exc:
                caught_exc = f"PermissionError: {exc}"
        elif attack == "spoof_verified":
            draft = MessageDraft(
                "atk-prov", "t-atk", "alice", "bob", Performative.INFORM,
                {"claim": "fake verified"}, claim_provenance=Provenance.VERIFIED,
            )
            try:
                self.hub.dispatch_tick(messages=((draft, self.caps["alice_write"]),))
            except ValueError as exc:
                caught_exc = f"ValueError: {exc}"
        elif attack == "replay_id":
            target_id = (
                self.hub.message_log[-1].message_id
                if self.hub.message_log
                else "atk-replay-seed"
            )
            if not self.hub.message_log:
                # Test against an isolated hub so live session tick stays unchanged.
                tworld = create_world(self.world_agents, (("alice", "bob"),), seed=1)
                thub = BoundedCommunicationHub(tworld)
                tcap = thub.issue_capability("alice", action="write_agent")
                d = MessageDraft(target_id, "t-rep", "alice", "bob", Performative.PING, {"seq": 1})
                thub.dispatch_tick(messages=((d, tcap),))
                try:
                    thub.dispatch_tick(messages=((d, tcap),))
                except ValueError as exc:
                    caught_exc = f"ValueError: {exc}"
            else:
                d = MessageDraft(target_id, "t-rep", "alice", "bob", Performative.PING, {"seq": 1})
                try:
                    self.hub.dispatch_tick(messages=((d, self.caps["alice_write"]),))
                except ValueError as exc:
                    caught_exc = f"ValueError: {exc}"
        elif attack == "wrong_token":
            # Try sending as Alice using Bob's write_agent capability!
            draft = MessageDraft("atk-impersonate", "t-atk", "alice", "bob", Performative.PING, {"spoof": True})
            try:
                self.hub.dispatch_tick(messages=((draft, self.caps["bob_write"]),))
            except PermissionError as exc:
                caught_exc = f"PermissionError: {exc}"
        else:
            raise ValueError(f"unknown security test: {attack}")

        if not caught_exc:
            raise AssertionError(f"expected security attack {attack} to be blocked")

        return {
            "attack": attack,
            "outcome": "BLOCKED",
            "alice_revoked": self.alice_revoked,
            "exception": caught_exc,
            "detail": (
                f"Rejected during Python pre-check; W3 state unchanged "
                f"(tick={self.hub.world.tick}, before={before_tick}, fingerprint preserved)."
            ),
            "tick_unchanged": self.hub.world.tick == before_tick,
            "fingerprint_unchanged": self.hub.world.fingerprint() == before_fp,
            "state": self.snapshot(),
        }

    def snapshot(self) -> dict[str, object]:
        """Return full authoritative state directly from Python + SQLite + W3."""
        assert self.memory is not None
        replay_ok = verify_replay(self.hub.genesis, self.hub.world)
        balances = dict(self.hub.world.balances)
        alice_mem = self._alice_memory_view()
        bob_state = self.memory.get_state(
            owner_id=DEFAULT_OWNER,
            agent_id="bob",
            requester_owner_id=DEFAULT_OWNER,
        )
        exact_rows = [
            {
                "owner_id": row[0],
                "agent_id": row[1],
                "seq": row[2],
                "event_id": row[3],
                "provenance": row[4],
                "event_type": row[5],
                "payload": json.loads(bytes(row[6]).decode("utf-8")),
                "payload_hash": row[7],
            }
            for row in self.memory.db.execute(
                "SELECT owner_id, agent_id, seq, event_id, provenance, event_type, payload, payload_hash "
                "FROM exact_events ORDER BY rowid DESC LIMIT 30"
            ).fetchall()
        ]
        exact_total = self.memory.db.execute("SELECT COUNT(*) FROM exact_events").fetchone()[0]

        return {
            "schema": SCHEMA_VERSION,
            "session_id": self.session_id,
            "mode": self.mode,
            "p7_reconcile": self.p7_reconcile,
            "round": self.round,
            "max_rounds": self.max_rounds,
            "probe_interval": self.probe_interval,
            "recover_at": self.recover_at,
            "stage": self.stage,
            "world_tick": self.hub.world.tick,
            "world_events_count": len(self.hub.world.events),
            "world_fingerprint": self.hub.world.fingerprint(),
            "replay_verified": replay_ok,
            "total_resources": sum(balances.values()),
            "initial_resources": self.hub.initial_total_resources,
            "balances": balances,
            "alice": {
                "balance": balances["alice"],
                "capability_active": not self.alice_revoked,
                "risk_budget": {
                    "cap": CAP,
                    "known_loss": self.budget.known_bad,
                    "pending": sorted(self.budget.pending),
                    "exposure": self.budget.exposure,
                    "peak_exposure": self.budget.peak_exposure,
                },
                "memory": alice_mem,
                "fake_acks_caught": self.fake_acks_caught,
                "reconciled_receipts": self.reconciled_count,
            },
            "bob": {
                "balance": balances["bob"],
                "strategy": self.mode,
                "exact_events_count": bob_state["seq"],
            },
            "w3_receipts": [self.w3_receipts[k] for k in sorted(self.w3_receipts)],
            "exact_events_total": exact_total,
            "exact_events_recent": exact_rows,
            "messages_count": len(self.hub.message_log),
            "messages_recent": [m.to_dict() for m in self.hub.message_log[-20:]],
            "memory_series": self.memory_series,
            "history": self.history,
            "last_events": self.last_events,
            "backend": {
                "engine": "Python OpenWorld SuperKernel (W3 + HyperMemoryP1e + DonorBudget)",
                "python_version": platform.python_version(),
                "sqlite_version": sqlite3.sqlite_version,
                "provenance": Provenance.SIMULATED.value,
            },
        }


def make_server(host: str = "127.0.0.1", port: int = 8765) -> HTTPServer:
    """Create a single-threaded loopback HTTPServer bound to one live session."""
    if host not in ("127.0.0.1", "localhost"):
        raise ValueError("local research server must bind to 127.0.0.1 or localhost only")
    session = LiveTwoAgentSession()

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

        def _send_json(self, status: int, data: dict[str, object]) -> None:
            body = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self._send_bytes(status, "application/json; charset=utf-8", body)

        def _read_json(self) -> dict[str, object]:
            length_hdr = self.headers.get("Content-Length", "0")
            try:
                length = int(length_hdr)
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
            if path in ("/api/health", "/api/state"):
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
                self._send_bytes(
                    HTTPStatus.OK,
                    "text/html; charset=utf-8",
                    UI_FILE.read_bytes(),
                )
                return
            if path == "/api/health":
                self._send_json(HTTPStatus.OK, {"ok": True, "schema": SCHEMA_VERSION})
                return
            if path == "/api/state":
                self._send_json(HTTPStatus.OK, session.snapshot())
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            try:
                body = self._read_json()
                if path == "/api/session/reset":
                    allowed = {"mode", "p7_reconcile", "max_rounds", "probe_interval", "recover_at", "seed"}
                    unknown = set(body) - allowed
                    if unknown:
                        raise ValueError(f"unknown fields: {sorted(unknown)}")
                    result = session.reset(**body)
                    self._send_json(HTTPStatus.OK, result)
                    return
                if path == "/api/round/step":
                    result = session.step_round()
                    self._send_json(HTTPStatus.OK, result)
                    return
                if path == "/api/bob/reply":
                    result = session.bob_reply(str(body.get("decision", "")))
                    self._send_json(HTTPStatus.OK, result)
                    return
                if path == "/api/bob/return":
                    result = session.bob_return(str(body.get("action", "")))
                    self._send_json(HTTPStatus.OK, result)
                    return
                if path == "/api/security/test":
                    result = session.run_security_test(str(body.get("attack", "")))
                    self._send_json(HTTPStatus.OK, result)
                    return
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            except PermissionError as exc:
                self._send_json(
                    HTTPStatus.FORBIDDEN,
                    {"error": str(exc), "error_type": "PermissionError", "state": session.snapshot()},
                )
            except (ValueError, TypeError) as exc:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": str(exc), "error_type": type(exc).__name__},
                )

    server = HTTPServer((host, port), Handler)
    server.session = session  # type: ignore[attr-defined]
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", choices=("127.0.0.1", "localhost"))
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = make_server(host=args.host, port=args.port)
    actual_port = server.server_address[1]
    print(f"OpenWorld 2-Agent Live Backend listening on http://{args.host}:{actual_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.session.close()  # type: ignore[attr-defined]
        server.server_close()


if __name__ == "__main__":
    main()
