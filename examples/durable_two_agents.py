"""Durable, same-owner, SIMULATED gifts, receipts, risk budget and agent memory.

One complete two-phase round is the authoritative SQLite transaction. Memory
is a separately committed, verified projection. No external effects or LLMs.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from dataclasses import asdict
import json
import os
from pathlib import Path
import sqlite3
import time

from persistent_agents import canonical, digest, single_writer
from two_agents import DonorAgent, Outcome, RecipientAgent, SCENARIOS, OWNER, PRINCIPAL, find_return_receipt
from openworld_superkernel.hyper_memory_p1e import HyperMemoryP1e, Observation
from openworld_superkernel.memory_contracts import MemoryEvent, Provenance
from openworld_superkernel.risk_budget import BREAK_EVEN, CAP
from openworld_superkernel.trust_boundaries import CapabilityAuthority
from openworld_superkernel.world_fixture import Action, Agent, TickInput, advance, create_world, verify_replay
from openworld_superkernel.world_guard import AuthorizedWorldAction, GuardedWorldGateway

FORMAT = "openworld.durable-two-agents.v1"
MAX_ROUNDS = 20
DEFAULTS = {"mode": "reconcile", "scenario": "cooperative", "policy": "memory",
            "drop_every": 2, "delay": 1, "recover_at": 10, "seed": 2026}


def settings(**options):
    config = DEFAULTS | options
    if (set(config) != set(DEFAULTS)
            or config["mode"] not in ("notifications", "reconcile")
            or config["scenario"] not in SCENARIOS
            or config["policy"] not in ("memory", "always_offer")
            or type(config["drop_every"]) is not int or not 0 <= config["drop_every"] <= 20
            or type(config["delay"]) is not int or not 0 <= config["delay"] <= 2
            or type(config["recover_at"]) is not int or not 0 <= config["recover_at"] <= 20
            or type(config["seed"]) is not int or not 0 <= config["seed"] < 2**31):
        raise ValueError("invalid bounded durable simulation settings")
    return config


def observation(record):
    return Observation(MemoryEvent(record["event_id"], OWNER, record["event_type"],
                                  Provenance.SIMULATED, record["payload"].encode("utf-8"),
                                  protected=True), record["agent"], record["sequence"], record["outcome"])


class RoundEngine:
    """Example-local deterministic reducer; private memory contains only replayed evidence."""

    def __init__(self, config, memory):
        self.config, self.memory = config, memory
        self.a = DonorAgent(config["mode"])
        self.b = RecipientAgent(config["scenario"], config["recover_at"])
        self.genesis = self.world = create_world((Agent("A", OWNER, "local", 8),
                                                  Agent("B", OWNER, "local", 0)),
                                                 (("A", "B"),), seed=config["seed"])
        self.round = self.sent = self.returned = self.true_peak = 0
        self.channel, self.items, self.outcomes = [], [], {}

    def _emit(self, agent, event_id, event_type, outcome, evidence):
        state = self.memory.get_state(owner_id=OWNER, agent_id=agent, requester_owner_id=OWNER)
        record = {"agent": agent, "event_id": event_id, "event_type": event_type,
                  "sequence": state["seq"] + 1, "outcome": int(outcome),
                  "payload": canonical({"schema": FORMAT, "provenance": "SIMULATED", **evidence})}
        self.memory.apply_batch((observation(record),), requester_owner_id=OWNER)
        self.items.append(record)

    def _receive(self, outcome, *, source):
        # A nonempty digest alone is insufficient: bind to the completed phase
        # and recompute the exact positive receipt from the accepted W3 event.
        completed = self.outcomes.get(outcome.origin)
        if completed is None or outcome != completed["outcome"]:
            raise ValueError("feedback does not match its completed recipient phase")
        if outcome.returned and find_return_receipt(self.world, outcome.origin) != outcome:
            raise ValueError("return receipt origin or digest mismatch")
        if self.a.receive(outcome, self.round, reconciled=source == "reconciliation"):
            self._emit("A", f"durable-A-{outcome.origin}", "simulated_partner_return",
                       outcome.returned, {"origin": outcome.origin, "at_round": self.round,
                       "source": source, "returned": outcome.returned,
                       "receipt_digest": outcome.receipt_digest,
                       "completed_tick": completed["tick"], "phase_sha256": completed["hash"]})

    def _commit(self, actor, target, enabled, request_id, gateway, tokens):
        action = Action(request_id, self.world.tick, OWNER, actor, target, "transfer", 1)
        if gateway is None:
            result = advance(self.world, TickInput(self.world.tick, (action,) if enabled else (), (), 1),
                             max_actions=1)
        else:
            authorized = (AuthorizedWorldAction(action, tokens[actor]),) if enabled else ()
            result = gateway.advance(self.world, actions=authorized, max_actions=1)
        if result.rejected or result.accepted != ((request_id,) if enabled else ()):
            raise ValueError("unexpected W3 action result")
        self.world = result.world

    def snapshot(self):
        budget = self.a.budget
        return {"round": self.round, "world_sha256": self.world.fingerprint(),
                "balances": dict(self.world.balances), "sent": self.sent, "returned": self.returned,
                "actual_loss": self.sent-self.returned, "peak_actual_exposure": self.true_peak,
                "budget": {"known_loss": budget.known_bad, "pending": sorted(budget.pending),
                           "exposure": budget.exposure, "peak_exposure": budget.peak_exposure,
                           "observed": list(budget.observed), "recent": list(budget.recent),
                           "blocked": budget.blocked},
                "observations": self.a.observations, "reconciled": self.a.reconciled,
                "duplicates_ignored": self.a.duplicates,
                "channel": [{"due": due, **asdict(outcome)} for due, outcome in self.channel]}

    def step(self, previous_hash, *, live=False):
        rnd = self.round
        if rnd >= MAX_ROUNDS:
            raise ValueError("bounded example reached 20 rounds; choose a new database")
        start_items, start_events = len(self.items), len(self.world.events)
        for due, outcome in tuple(self.channel):
            if due == rnd:
                self._receive(outcome, source="notification")
                self.channel.remove((due, outcome))
        if self.config["mode"] == "reconcile" and rnd % 3 == 0:
            for origin in sorted(self.a.budget.pending):
                receipt = find_return_receipt(self.world, origin)
                if receipt is not None:
                    self._receive(receipt, source="reconciliation")
        predictions = {agent: self.memory.predict(owner_id=OWNER, agent_id=agent,
                                                 requester_owner_id=OWNER) for agent in ("A", "B")}
        permitted = self.a.choose(rnd, dict(self.world.balances)["A"])
        give = permitted and (self.config["policy"] == "always_offer" or predictions["A"][0] > BREAK_EVEN)
        gateway, tokens = None, {}
        if live:
            authority = CapabilityAuthority(os.urandom(32), issuer="durable-demo", audience="local")
            gateway = GuardedWorldGateway(authority, authenticated_principal=lambda: PRINCIPAL)
            now = int(time.time())
            tokens = {actor: authority.issue(principal=PRINCIPAL, owner=OWNER, resource=actor,
                      action="write_agent", valid_from=now-10, expires_at=now+120) for actor in ("A", "B")}
        self._commit("A", "B", give, f"gift-{rnd}", gateway, tokens)
        if give:
            self.a.budget.accepted(rnd)
            self.sent += 1
            self.true_peak = max(self.true_peak, self.sent-self.returned)
        # B's task is predicting incoming gifts, including completed empty gift
        # phases. It does not train on A's private return estimate or risk state.
        self._emit("B", f"durable-B-{rnd}", "simulated_incoming_gift", give,
                   {"origin": rnd, "gift_received": give, "completed_tick": self.world.tick,
                    "phase_sha256": self.world.fingerprint(),
                    "gift_digest": self.world.events[-1].digest if give else None})
        give_back = self.b.choose_return(gift_received=give, round_index=rnd)
        self._commit("B", "A", give_back, f"return-{rnd}", gateway, tokens)
        self.returned += int(give_back)
        notice = "none"
        if give:
            receipt = find_return_receipt(self.world, rnd)
            if give_back != (receipt is not None):
                raise ValueError("recipient decision and committed receipt disagree")
            outcome = receipt if receipt is not None else Outcome(rnd, False)
            self.outcomes[rnd] = {"outcome": outcome, "tick": self.world.tick, "hash": self.world.fingerprint()}
            if self.config["drop_every"] and (rnd+1) % self.config["drop_every"] == 0:
                notice = "dropped"
            elif self.config["delay"]:
                due = rnd+self.config["delay"]
                self.channel.append((due, outcome))
                notice = f"due-{due}"
            else:
                self._receive(outcome, source="notification")
                notice = "delivered"
        if self.a.budget.exposure > CAP or self.true_peak > CAP:
            raise ValueError("safe risk budget invariant failed")
        if sum(dict(self.world.balances).values()) != 8:
            raise ValueError("resource conservation failed")
        self.round += 1
        return json.loads(canonical({"schema": FORMAT, "round": rnd, "previous_record_hash": previous_hash,
                "gift": give, "return": give_back, "notification": notice,
                "predictions_before": {a: {"probability": p, "estimator": e, "provenance": "INFERRED"}
                                       for a, (p, e) in predictions.items()},
                "inputs": [asdict(t) for t in self.world.journal[-2:]],
                "events": [asdict(e) for e in self.world.events[start_events:]],
                "memory_events": self.items[start_items:], "state": self.snapshot(),
                "provenance": "SIMULATED"}))


class DurableTwoAgents:
    """Example-only, single-writer store. Existing examples and schemas are unchanged."""

    def __init__(self, path, *, config=None, create=True):
        self.path = Path(path).resolve()
        self.recovered = 0
        self._dirty = False
        self._stack = ExitStack()
        if not create and not self.path.is_file():
            raise FileNotFoundError("simulation does not exist; run with --rounds first")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._stack.enter_context(single_writer(self.path))
            self.db = sqlite3.connect(self.path, isolation_level=None, timeout=15)
            self._stack.callback(self.db.close)
            self._prepare(config)
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            self.memory = self._stack.enter_context(HyperMemoryP1e(self.path))
            self.reference = self._stack.enter_context(HyperMemoryP1e(":memory:"))
            self.engine = RoundEngine(self.config, self.reference)
            self._restore()
        except BaseException:
            self._stack.close()
            raise

    def _prepare(self, requested):
        tables = {r[0] for r in self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        required = {"durable_pair_meta", "durable_pair_journal"}
        if tables and (not required <= tables or tables-required-{"agent_state", "exact_events"}):
            raise ValueError("not this example's database; refusing to modify existing store")
        if tables:
            rows = self.db.execute("SELECT id,config,config_hash FROM durable_pair_meta").fetchall()
            if len(rows) != 1 or rows[0][0] != 1 or digest(rows[0][1]) != rows[0][2]:
                raise ValueError("invalid simulation metadata")
            saved = json.loads(rows[0][1])
            if set(saved) != {"schema", "settings"} or saved["schema"] != FORMAT:
                raise ValueError("simulation format mismatch")
            self.config = settings(**saved["settings"])
            if requested is not None and self.config != settings(**(self.config | requested)):
                raise ValueError("saved simulation settings differ; use the original settings or a new database")
            return
        self.config = settings(**(requested or {}))
        body = canonical({"schema": FORMAT, "settings": self.config})
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("CREATE TABLE durable_pair_meta (id INTEGER PRIMARY KEY CHECK(id=1), config TEXT NOT NULL, config_hash TEXT NOT NULL)")
            self.db.execute("CREATE TABLE durable_pair_journal (round INTEGER PRIMARY KEY, body TEXT NOT NULL, body_hash TEXT NOT NULL)")
            self.db.execute("INSERT INTO durable_pair_meta VALUES(1,?,?)", (body, digest(body)))
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _restore(self):
        if self.db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise ValueError("SQLite integrity check failed")
        rows = self.db.execute("SELECT round,body,body_hash FROM durable_pair_journal ORDER BY round LIMIT ?",
                               (MAX_ROUNDS+1,)).fetchall()
        if len(rows) > MAX_ROUNDS:
            raise ValueError("journal exceeds 20-round bound")
        self.records, self.previous = [], "GENESIS"
        for rnd, body, body_hash in rows:
            if rnd != self.engine.round or digest(body) != body_hash:
                raise ValueError("journal sequence or digest mismatch")
            expected = self.engine.step(self.previous)
            if canonical(expected) != body:
                raise ValueError("journal replay mismatch: action, budget, queue, receipt or memory")
            self.records.append(expected)
            self.previous = body_hash
        self._verify_and_project()

    def _verify_and_project(self):
        # Validate every existing row and the entire authoritative history BEFORE
        # appending missing projection rows. A damaged projection is not erased.
        states = {a: self.memory.get_state(owner_id=OWNER, agent_id=a, requester_owner_id=OWNER) for a in ("A", "B")}
        for state in states.values():
            if type(state.get("seq")) is not int or not 0 <= state["seq"] <= MAX_ROUNDS:
                raise ValueError("invalid persisted memory sequence")
        keys = set(self.memory.db.execute("SELECT owner_id,agent_id FROM agent_state"))
        if not keys <= {(OWNER, a) for a in ("A", "B")}:
            raise ValueError("unexpected owner or agent in memory")
        counts, boundaries = {"A": 0, "B": 0}, {(0, 0)}
        for record in self.records:
            for item in record["memory_events"]:
                counts[item["agent"]] += 1
            boundaries.add((counts["A"], counts["B"]))
        if (states["A"]["seq"], states["B"]["seq"]) not in boundaries:
            raise ValueError("memory projection is not at an atomic round boundary")
        matched = set()
        with HyperMemoryP1e(":memory:") as check:
            for a in ("A", "B"):
                if states[a]["seq"] == 0:
                    if states[a] != check.get_state(owner_id=OWNER, agent_id=a, requester_owner_id=OWNER):
                        raise ValueError("invalid initial memory state")
                    matched.add(a)
            for record in self.engine.items:
                item = observation(record)
                check.apply_batch((item,), requester_owner_id=OWNER)
                a, seq = item.agent_id, item.sequence_number
                if seq <= states[a]["seq"]:
                    row = self.memory.db.execute(
                        "SELECT owner_id,agent_id,seq,event_id,provenance,event_type,payload,payload_hash FROM exact_events WHERE owner_id=? AND agent_id=? AND seq=?",
                        (OWNER, a, seq)).fetchone()
                    payload = item.event.payload
                    expected = (OWNER, a, seq, item.event.event_id, "simulated", item.event.event_type, payload, digest(payload.decode("utf-8")))
                    if row != expected:
                        raise ValueError("exact memory event differs from authoritative journal")
                if seq == states[a]["seq"]:
                    if states[a] != check.get_state(owner_id=OWNER, agent_id=a, requester_owner_id=OWNER):
                        raise ValueError("predictive memory state differs from authoritative journal")
                    matched.add(a)
        if matched != {"A", "B"}:
            raise ValueError("memory is ahead of authoritative journal")
        count = self.memory.db.execute("SELECT COUNT(*) FROM exact_events").fetchone()[0]
        if count != sum(s["seq"] for s in states.values()):
            raise ValueError("unexpected or missing exact memory events")
        missing = [observation(r) for r in self.engine.items if r["sequence"] > states[r["agent"]]["seq"]]
        self.recovered += self.memory.apply_batch(missing, requester_owner_id=OWNER)

    def _before_journal_commit(self):
        """Fault-injection hook; no external effects are permitted."""

    def _after_journal_commit(self):
        """Fault-injection hook before the separate memory transaction."""

    def step(self):
        if self._dirty:
            raise RuntimeError("a step was interrupted; close and reopen to verify and recover")
        if self.engine.round >= MAX_ROUNDS:
            raise ValueError("bounded example reached 20 rounds; choose a new database")
        self._dirty = True
        record = self.engine.step(self.previous, live=True)
        body = canonical(record)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            count = self.db.execute("SELECT COUNT(*) FROM durable_pair_journal").fetchone()[0]
            if count != record["round"]:
                raise ValueError("journal changed since opening; close and reopen")
            self.db.execute("INSERT INTO durable_pair_journal VALUES(?,?,?)", (record["round"], body, digest(body)))
            self._before_journal_commit()
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        self._after_journal_commit()
        self.memory.apply_batch([observation(r) for r in record["memory_events"]], requester_owner_id=OWNER)
        self.records.append(record)
        self.previous, self._dirty = digest(body), False
        return record

    def status(self, *, history=False):
        if self._dirty:
            raise RuntimeError("a step was interrupted; close and reopen to verify and recover")
        if not verify_replay(self.engine.genesis, self.engine.world):
            raise ValueError("world replay failed")
        memories = {}
        for a in ("A", "B"):
            state = self.memory.get_state(owner_id=OWNER, agent_id=a, requester_owner_id=OWNER)
            p, estimator = self.memory.predict(owner_id=OWNER, agent_id=a, requester_owner_id=OWNER)
            memories[a] = {"sequence": state["seq"], "observations": state["n"], "successes": state["successes"],
                           "prediction": p, "estimator": estimator, "prediction_provenance": "INFERRED"}
        result = {"schema": FORMAT, "database": str(self.path), "settings": self.config,
                  **self.engine.snapshot(), "memory": memories,
                  "exact_events": self.memory.db.execute("SELECT COUNT(*) FROM exact_events").fetchone()[0],
                  "recovered_memory_events": self.recovered, "replay_verified": True, "provenance": "SIMULATED"}
        if history:
            result["history"] = self.records
        return result

    def close(self):
        self._stack.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/durable-two-agents.sqlite3"))
    parser.add_argument("--rounds", type=int, default=3, help="additional rounds; total bound is 20")
    parser.add_argument("--status", action="store_true", help="verify/recover without new rounds")
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--mode", choices=("notifications", "reconcile"))
    parser.add_argument("--scenario", choices=SCENARIOS)
    parser.add_argument("--policy", choices=("memory", "always_offer"))
    for option in ("drop_every", "delay", "recover_at", "seed"):
        parser.add_argument("--"+option.replace("_", "-"), type=int)
    args = parser.parse_args()
    if not 1 <= args.rounds <= MAX_ROUNDS:
        parser.error("--rounds must be between 1 and 20")
    specified = {k: getattr(args, k) for k in DEFAULTS if getattr(args, k) is not None}
    try:
        # Unspecified settings resume from metadata; explicit options are checked
        # against that metadata before any new round or memory recovery.
        with DurableTwoAgents(args.db, config=specified or None, create=not args.status) as simulation:
            start = simulation.engine.round
            if not args.status and start+args.rounds > MAX_ROUNDS:
                raise ValueError("requested rounds exceed the total bound of 20")
            if not args.status:
                for _ in range(args.rounds):
                    simulation.step()
            result = simulation.status(history=args.history)
            result["resumed_from_round"] = start
    except (ValueError, RuntimeError, OSError, sqlite3.Error, KeyError, TypeError) as exc:
        parser.exit(1, f"Simulation stopped: {exc}\n")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
