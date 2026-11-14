"""Persistent same-owner W3 + HyperMemory example, using one local SQLite file.

The exact simulation journal is authoritative. HyperMemory is a recoverable
projection, written in a SECOND transaction. No cross-store atomicity, network
identity, real observations, model service or production crash-safety claim.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from openworld_superkernel.hyper_memory_p1e import HyperMemoryP1e, Observation
from openworld_superkernel.memory_contracts import MemoryEvent, Provenance
from openworld_superkernel.trust_boundaries import CapabilityAuthority
from openworld_superkernel.world_fixture import Action, Agent, TickInput, advance, create_world, observe, verify_replay
from openworld_superkernel.world_guard import AuthorizedWorldAction, GuardedWorldGateway

FORMAT = "openworld.persistent-agent-demo.v1"
OWNER, PRINCIPAL = "persistent-demo-owner", "trusted-local-host"
AGENTS = ("alice", "bob")
FEEDBACK = (0, 1, 1)  # Lab-supplied feedback, not a partner's observed response.
MAX_TICKS = 1000


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


@contextmanager
def single_writer(path: Path):
    """OS lock releases on process exit; the small lock file may remain."""
    lock_path = path.with_name(path.name + ".lock")
    with lock_path.open("a+b") as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if sys.platform == "win32":
            import msvcrt
            acquire = lambda: msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            release = lambda: msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            acquire = lambda: fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            release = lambda: fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        try:
            acquire()
        except OSError as exc:
            raise RuntimeError("another process is using this simulation") from exc
        try:
            yield
        finally:
            handle.seek(0)
            release()


def genesis_world():
    return create_world(tuple(Agent(a, OWNER, "lab", 3) for a in AGENTS),
                        (("alice", "bob"),), seed=2026)


def proposal(world, memory):
    actor = AGENTS[world.tick % 2]
    target = AGENTS[1-world.tick % 2]
    obs = observe(world, OWNER, actor)
    probability, estimator = memory.predict(owner_id=OWNER, agent_id=actor,
                                            requester_owner_id=OWNER)
    state = memory.get_state(owner_id=OWNER, agent_id=actor, requester_owner_id=OWNER)
    kind = "transfer" if probability >= 0.5 and obs.balance >= 1 else "signal"
    return (Action(f"persistent-{world.tick}-{actor}", world.tick, OWNER, actor,
                   target, kind, 1 if kind == "transfer" else 0),
            probability, estimator, state["seq"]+1)


def record_for(before, after, action, probability, estimator, sequence, previous):
    event_id = f"persistent-feedback-{before.tick}-{action.actor}"
    payload = canonical({"schema": FORMAT, "action": asdict(action),
                         "world_before": before.fingerprint(),
                         "world_after": after.fingerprint(),
                         "outcome": FEEDBACK[before.tick % len(FEEDBACK)],
                         "provenance": "SIMULATED"})
    return {"tick": before.tick, "actor": action.actor, "sequence": sequence,
            "event_id": event_id, "prediction": probability, "estimator": estimator,
            "payload": payload, "previous_record_hash": previous}


def memory_item(record):
    payload = json.loads(record["payload"])
    return Observation(MemoryEvent(record["event_id"], OWNER,
                                   "persistent_simulated_feedback", Provenance.SIMULATED,
                                   record["payload"].encode("utf-8"), protected=True),
                       record["actor"], record["sequence"], payload["outcome"])


class PersistentSimulation:
    """Bounded example, not a public runtime interface. One process per file."""

    def __init__(self, path, *, create=True):
        self.path = Path(path).resolve()
        if not create and not self.path.is_file():
            raise FileNotFoundError("simulation does not exist; run with --steps first")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._stack = ExitStack()
        try:
            self._stack.enter_context(single_writer(self.path))
            self.db = sqlite3.connect(self.path, isolation_level=None, timeout=15)
            self._stack.callback(self.db.close)
            self._prepare()
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            self.memory = self._stack.enter_context(HyperMemoryP1e(self.path))
            self.genesis = genesis_world()
            self.recovered = 0
            self._needs_recovery = False
            self._restore()
        except BaseException:
            self._stack.close()
            raise

    def _prepare(self):
        tables = {r[0] for r in self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        if tables and not {"persistent_demo_meta", "persistent_demo_journal"} <= tables:
            raise ValueError("not this demo's database; refusing to modify an existing store")
        if tables - {"persistent_demo_meta", "persistent_demo_journal", "agent_state", "exact_events"}:
            raise ValueError("unexpected tables in this demo's database")
        expected = canonical({"format": FORMAT, "owner": OWNER, "agents": AGENTS,
                              "feedback": FEEDBACK, "genesis": genesis_world().fingerprint()})
        if tables:
            row = self.db.execute("SELECT config,config_hash FROM persistent_demo_meta WHERE id=1").fetchone()
            if row != (expected, digest(expected)):
                raise ValueError("simulation format or configuration mismatch")
            return
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("CREATE TABLE persistent_demo_meta (id INTEGER PRIMARY KEY CHECK(id=1), config TEXT NOT NULL, config_hash TEXT NOT NULL)")
            self.db.execute("CREATE TABLE persistent_demo_journal (tick INTEGER PRIMARY KEY, body TEXT NOT NULL, body_hash TEXT NOT NULL)")
            self.db.execute("INSERT INTO persistent_demo_meta VALUES(1,?,?)", (expected, digest(expected)))
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _restore(self):
        if self.db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise ValueError("SQLite integrity check failed")
        rows = self.db.execute("SELECT tick,body,body_hash FROM persistent_demo_journal ORDER BY tick LIMIT ?",
                               (MAX_TICKS+1,)).fetchall()
        if len(rows) > MAX_TICKS:
            raise ValueError("bounded example journal exceeds 1000 ticks")
        stored = {a: self.memory.get_state(owner_id=OWNER, agent_id=a, requester_owner_id=OWNER)
                  for a in AGENTS}
        if any(type(s.get("seq")) is not int or not 0 <= s["seq"] <= MAX_TICKS for s in stored.values()):
            raise ValueError("invalid persisted agent sequence")
        matched = {a: stored[a]["seq"] == 0 for a in AGENTS}
        records = []
        world, previous = self.genesis, "GENESIS"
        # Verify the ENTIRE authoritative journal before changing a projection.
        with HyperMemoryP1e(":memory:") as reference:
            for a in AGENTS:
                initial = reference.get_state(owner_id=OWNER, agent_id=a, requester_owner_id=OWNER)
                if matched[a] and stored[a] != initial:
                    raise ValueError("invalid initial agent memory")
            for tick, body, body_hash in rows:
                if tick != world.tick or digest(body) != body_hash:
                    raise ValueError("journal sequence or digest mismatch")
                record = json.loads(body)
                action, probability, estimator, seq = proposal(world, reference)
                step = advance(world, TickInput(world.tick, (action,), (), 1), max_actions=1)
                expected = record_for(world, step.world, action, probability, estimator, seq, previous)
                if record != expected or step.accepted != (action.request_id,) or step.rejected:
                    raise ValueError("journal action, feedback or replay mismatch")
                item = memory_item(record)
                reference.apply_batch((item,), requester_owner_id=OWNER)
                actor = record["actor"]
                if seq <= stored[actor]["seq"]:
                    exact = self.memory.db.execute(
                        "SELECT owner_id,agent_id,seq,event_id,provenance,event_type,payload,payload_hash FROM exact_events WHERE owner_id=? AND agent_id=? AND seq=?",
                        (OWNER, actor, seq)).fetchone()
                    payload = item.event.payload
                    if exact != (OWNER, actor, seq, item.event.event_id, "simulated",
                                 item.event.event_type, payload, sha256(payload).hexdigest()):
                        raise ValueError("materialized exact event differs from journal")
                if seq == stored[actor]["seq"]:
                    state = reference.get_state(owner_id=OWNER, agent_id=actor, requester_owner_id=OWNER)
                    if stored[actor] != state:
                        raise ValueError("materialized predictive state differs from journal")
                    matched[actor] = True
                records.append(record)
                world, previous = step.world, body_hash
        if not all(matched.values()):
            raise ValueError("agent memory is ahead of authoritative history")
        state_keys = set(self.memory.db.execute("SELECT owner_id,agent_id FROM agent_state"))
        if not state_keys <= {(OWNER, a) for a in AGENTS}:
            raise ValueError("unexpected owner or agent in this demo's memory")
        exact_count = self.memory.db.execute("SELECT COUNT(*) FROM exact_events").fetchone()[0]
        if exact_count != sum(s["seq"] for s in stored.values()):
            raise ValueError("unexpected or missing exact-event rows")
        for record in records:
            if record["sequence"] > stored[record["actor"]]["seq"]:
                self.memory.apply_batch((memory_item(record),), requester_owner_id=OWNER)
                self.recovered += 1
        self.world, self.previous, self.records = world, previous, records
        self._needs_recovery = False

    def _before_journal_commit(self):
        """Empty fault-injection hook used only by local tests."""

    def _after_journal_commit(self):
        """Empty fault-injection hook used only by local tests."""

    def step(self):
        if self._needs_recovery:
            self._restore()
        if self.world.tick >= MAX_TICKS:
            raise ValueError("bounded example reached 1000 ticks; choose a new database")
        action, probability, estimator, sequence = proposal(self.world, self.memory)
        authority = CapabilityAuthority(os.urandom(32), issuer="persistent-demo", audience="world")
        gateway = GuardedWorldGateway(authority, authenticated_principal=lambda: PRINCIPAL)
        now = int(time.time())
        def token(kind):
            return authority.issue(principal=PRINCIPAL, owner=OWNER, resource=action.actor,
                                   action=kind, valid_from=now-10, expires_at=now+120)
        gateway.observe(self.world, agent_id=action.actor, signed_capability=token("read_world"))
        step = gateway.advance(self.world, actions=(AuthorizedWorldAction(action, token("write_agent")),),
                               external=(), max_actions=1)
        if step.accepted != (action.request_id,) or step.rejected:
            raise ValueError("guarded action rejected")
        record = record_for(self.world, step.world, action, probability, estimator, sequence, self.previous)
        body = canonical(record)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            count = self.db.execute("SELECT COUNT(*) FROM persistent_demo_journal").fetchone()[0]
            if count != self.world.tick:
                raise ValueError("history changed since opening; reopen the simulation")
            self.db.execute("INSERT INTO persistent_demo_journal VALUES(?,?,?)", (self.world.tick, body, digest(body)))
            self._before_journal_commit()
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        self._needs_recovery = True
        self._after_journal_commit()
        self.memory.apply_batch((memory_item(record),), requester_owner_id=OWNER)
        self.world, self.previous = step.world, digest(body)
        self.records.append(record)
        self._needs_recovery = False
        return {"tick": record["tick"], "actor": action.actor, "target": action.target,
                "action": action.kind, "amount": action.amount, "prediction_before": probability,
                "synthetic_feedback": FEEDBACK[record["tick"] % len(FEEDBACK)],
                "memory_event_id": record["event_id"], "provenance": "SIMULATED"}

    def status(self, *, history=False):
        if self._needs_recovery:
            self._restore()
        if not verify_replay(self.genesis, self.world):
            raise ValueError("world replay failed")
        memories = {}
        for agent in AGENTS:
            state = self.memory.get_state(owner_id=OWNER, agent_id=agent, requester_owner_id=OWNER)
            probability, estimator = self.memory.predict(owner_id=OWNER, agent_id=agent, requester_owner_id=OWNER)
            memories[agent] = {"observations": state["n"], "successes": state["successes"],
                               "sequence": state["seq"], "prediction": probability,
                               "prediction_provenance": "INFERRED", "estimator": estimator}
        result = {"schema": FORMAT, "database": str(self.path), "tick": self.world.tick,
                  "balances": dict(self.world.balances), "memory": memories,
                  "exact_events": self.memory.db.execute("SELECT COUNT(*) FROM exact_events").fetchone()[0],
                  "recovered_memory_events": self.recovered, "world_sha256": self.world.fingerprint(),
                  "world_replay": "PASS", "provenance": "SIMULATED",
                  "limits": "Scripted same-owner lab feedback; journal and memory projection use separate transactions. Recovery is from exact journal records, not inferred history. No outside actions, authenticated identity or production power-loss certification."}
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
    parser.add_argument("--db", type=Path, default=Path("data/openworld.sqlite3"))
    parser.add_argument("--steps", type=int, default=3, help="additional ticks on each invocation (1-100)")
    parser.add_argument("--status", action="store_true", help="recover and inspect without adding actions")
    parser.add_argument("--history", action="store_true", help="include exact saved simulation records")
    args = parser.parse_args()
    if not 1 <= args.steps <= 100:
        parser.error("--steps must be between 1 and 100")
    try:
        with PersistentSimulation(args.db, create=not args.status) as simulation:
            start = simulation.world.tick
            if not args.status and start+args.steps > MAX_TICKS:
                raise ValueError("requested steps exceed the 1000-tick example bound")
            cycles = [] if args.status else [simulation.step() for _ in range(args.steps)]
            result = simulation.status(history=args.history)
            result["resumed_from_tick"], result["new_cycles"] = start, cycles
    except (ValueError, RuntimeError, OSError, sqlite3.Error) as exc:
        parser.exit(1, f"Simulation stopped: {exc}\n")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
