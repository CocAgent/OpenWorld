"""HM-P1e experimental, cost-aware Bernoulli memory with an exact evidence lane.

Only synthetic/research workloads are supported. No API, LLM, or user data.
The SQLite transaction boundary is local to one database, not distributed.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .memory_contracts import MemoryEvent, MemoryRoute, Provenance, route_memory_event


class StaleRetryError(ValueError):
    """A retry predates the most recent retained idempotency receipt."""


class ConflictingRetryError(ValueError):
    """The same sequence number was supplied with different content."""


class EvidenceIntegrityError(ValueError):
    """An exact ledger record's payload digest does not match."""


@dataclass(frozen=True, slots=True)
class Observation:
    event: MemoryEvent
    sequence_number: int
    outcome: int

    def __post_init__(self) -> None:
        if type(self.sequence_number) is not int or self.sequence_number < 1:
            raise ValueError("sequence_number must be a positive integer")
        if type(self.outcome) is not int or self.outcome not in (0, 1):
            raise ValueError("outcome must be 0 or 1")
        if self.event.provenance == Provenance.UNAVAILABLE:
            raise ValueError("unavailable evidence cannot train a predictor")


def _initial_state() -> dict:
    return {
        "seq": 0, "receipt": "",
        "n": 0, "successes": 0,
        "fast_s": 0.0, "fast_w": 0.0,
        "slow_s": 0.0, "slow_w": 0.0,
        "loss_static": 0.25, "loss_fast": 0.25, "loss_slow": 0.25,
        "selected": "static",
    }


def _probabilities(s: dict) -> dict[str, float]:
    return {
        "static": (s["successes"] + 1.0) / (s["n"] + 2.0),
        "fast": (s["fast_s"] + 1.0) / (s["fast_w"] + 2.0),
        "slow": (s["slow_s"] + 1.0) / (s["slow_w"] + 2.0),
    }


def _choose(s: dict, penalty: float) -> str:
    if s["n"] < 8:
        return "static"
    best = min(("fast", "slow"), key=lambda n: (s["loss_" + n], n))
    if s["loss_static"] - s["loss_" + best] > penalty:
        return best
    return "static"


def _receipt(item: Observation) -> str:
    e = item.event
    body = (
        e.event_id, e.owner_id, e.event_type, e.provenance.value,
        e.payload.hex(), e.reconstructable, e.protected,
        item.sequence_number, item.outcome,
    )
    return hashlib.sha256(
        json.dumps(body, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    ).hexdigest()


class HyperMemoryP1e:
    """Experimental SQLite memory: bounded adaptive state and exact events.

    Only the latest receipt is retained per agent. Older retries are rejected;
    they are never reported as successful. SQLite supplies local atomicity.
    """

    def __init__(self, path: str | Path, *, gate_penalty: float = 0.007):
        if not (0.0 <= gate_penalty <= 1.0):
            raise ValueError("gate_penalty out of range")
        self.gate_penalty = gate_penalty
        self.db = sqlite3.connect(str(path), isolation_level=None, timeout=15)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS agent_state (
                owner_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                state_json TEXT NOT NULL,
                PRIMARY KEY (owner_id, agent_id)
            );
            CREATE TABLE IF NOT EXISTS exact_events (
                owner_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                seq INTEGER NOT NULL,
                event_id TEXT NOT NULL UNIQUE,
                provenance TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload BLOB NOT NULL,
                payload_hash TEXT NOT NULL,
                PRIMARY KEY (owner_id, agent_id, seq)
            );
            """
        )

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "HyperMemoryP1e":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def get_state(self, *, owner_id: str, agent_id: str,
                  requester_owner_id: str) -> dict:
        if owner_id != requester_owner_id:
            raise PermissionError("cross-owner state access denied")
        row = self.db.execute(
            "SELECT state_json FROM agent_state WHERE owner_id=? AND agent_id=?",
            (owner_id, agent_id),
        ).fetchone()
        return json.loads(row[0]) if row else _initial_state()

    def predict(self, *, owner_id: str, agent_id: str,
                requester_owner_id: str) -> tuple[float, str]:
        s = self.get_state(owner_id=owner_id, agent_id=agent_id,
                           requester_owner_id=requester_owner_id)
        selected = _choose(s, self.gate_penalty)
        return _probabilities(s)[selected], selected

    def exact_event(self, event_id: str, *, requester_owner_id: str) -> bytes | None:
        row = self.db.execute(
            "SELECT owner_id,payload,payload_hash FROM exact_events WHERE event_id=?",
            (event_id,),
        ).fetchone()
        if row is None:
            return None
        if row[0] != requester_owner_id:
            raise PermissionError("cross-owner event access denied")
        data = bytes(row[1])
        if hashlib.sha256(data).hexdigest() != row[2]:
            raise EvidenceIntegrityError("exact event payload corrupted")
        return data

    def apply_batch(self, items: Iterable[Observation], *,
                    requester_owner_id: str,
                    inject_failure: bool = False) -> int:
        """Apply all updates atomically. No partial state or ledger commit."""
        events = list(items)
        if not requester_owner_id:
            raise ValueError("requester identity required")
        for item in events:
            if item.event.owner_id != requester_owner_id:
                raise PermissionError("cross-owner mutation denied")

        applied = 0
        self.db.execute("BEGIN IMMEDIATE")
        try:
            for item in events:
                e = item.event
                row = self.db.execute(
                    "SELECT state_json FROM agent_state WHERE owner_id=? AND agent_id=?",
                    (e.owner_id, e.event_id.split(":", 1)[0] if False else e.owner_id + "::" + self._agent_id(item)),
                ).fetchone()
                # Agent identity is distinct from event identity; see _agent_id.
                # The event data type does not have an agent_id in bootstrap v0.
                # A stable explicit agent ID is derived from the Observation wrapper.
                s = json.loads(row[0]) if row else _initial_state()
                digest = _receipt(item)
                if item.sequence_number == s["seq"]:
                    if digest != s["receipt"]:
                        raise ConflictingRetryError("latest sequence has different content")
                    continue
                if item.sequence_number <= s["seq"]:
                    raise StaleRetryError("older receipt not retained")
                if item.sequence_number != s["seq"] + 1:
                    raise ValueError("out-of-order update")
                prior = _probabilities(s)
                value = item.outcome
                for name, p in prior.items():
                    key = "loss_" + name
                    s[key] = 0.92 * s[key] + 0.08 * (p - value) ** 2
                s["n"] += 1
                s["successes"] += value
                s["fast_s"] = 0.65 * s["fast_s"] + value
                s["fast_w"] = 0.65 * s["fast_w"] + 1.0
                s["slow_s"] = 0.96 * s["slow_s"] + value
                s["slow_w"] = 0.96 * s["slow_w"] + 1.0
                s["seq"] = item.sequence_number
                s["receipt"] = digest
                s["selected"] = _choose(s, self.gate_penalty)
                aid = self._agent_id(item)
                self.db.execute(
                    "INSERT INTO agent_state(owner_id,agent_id,state_json) VALUES(?,?,?) "
                    "ON CONFLICT(owner_id,agent_id) DO UPDATE SET state_json=excluded.state_json",
                    (e.owner_id, aid, json.dumps(s, separators=(",", ":"))),
                )
                if route_memory_event(e) == MemoryRoute.EXACT:
                    self.db.execute(
                        "INSERT INTO exact_events(owner_id,agent_id,seq,event_id,provenance,"
                        "event_type,payload,payload_hash) VALUES(?,?,?,?,?,?,?,?)",
                        (e.owner_id, aid, item.sequence_number, e.event_id,
                         e.provenance.value, e.event_type, e.payload,
                         hashlib.sha256(e.payload).hexdigest()),
                    )
                applied += 1
                if inject_failure:
                    raise RuntimeError("injected failure before commit")
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        return applied

    @staticmethod
    def _agent_id(item: Observation) -> str:
        """Temporary contract: the caller encodes agent_id as event_id prefix.

        Example: agent-7:day-20. W0 RFC-006 will add agent_id to the envelope;
        until then event_id without a colon is invalid.
        """
        pieces = item.event.event_id.split(":", 1)
        if len(pieces) != 2 or not pieces[0] or not pieces[1]:
            raise ValueError("event_id must be '<agent_id>:<event_sequence_id>'")
        return pieces[0]

    def checkpoint(self) -> tuple[int, int, int]:
        """WAL checkpoint; busy readers can prevent truncation."""
        return tuple(self.db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone())
