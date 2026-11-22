"""Persistent SQLite exact ledger, searchable agent memory, and HM-P1e integration.

Implements RFC-006 provenance discipline for real local agent execution:
- Real user inputs, real tool outputs, and human consent decisions are recorded
  as OBSERVED_RECORDED inside an append-only SHA-256 hash-chained exact ledger.
- Model/LLM syntheses and predictions are strictly tagged INFERRED and cannot
  promote themselves to OBSERVED_RECORDED or VERIFIED.
- Each agent identity (e.g., `nova`, `atlas`) owns an isolated partition keyed
  by `(owner_id, agent_id)`, independent from any shared `model_ref`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

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

LEDGER_SCHEMA_VERSION = "openworld.companion-memory.v1"
MAX_FACT_BYTES = 4096

# Provenance labels that an autonomous agent may assign to stored facts.
# VERIFIED requires an external verification policy and cannot be self-minted.
ALLOWED_FACT_PROVENANCE = frozenset({
    Provenance.OBSERVED_RECORDED,
    Provenance.INFERRED,
})


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def sha256_hex(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


class CompanionMemoryStore:
    """Single-owner persistent SQLite store backing real OpenWorld agents."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path_str = str(path)
        if self.path_str != ":memory:":
            Path(self.path_str).resolve().parent.mkdir(parents=True, exist_ok=True)
        # HyperMemoryP1e owns the SQLite connection (WAL + synchronous=FULL)
        # and creates `agent_state` + `exact_events`.
        self.hm = HyperMemoryP1e(self.path_str)
        self.db: sqlite3.Connection = self.hm.db
        self._init_tables()

    def _init_tables(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS companion_agents (
                owner_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                role TEXT NOT NULL,
                model_ref TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (owner_id, agent_id)
            );
            CREATE TABLE IF NOT EXISTS exact_ledger (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                owner_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                provenance TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                digest TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS knowledge_facts (
                fact_id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                fact_key TEXT NOT NULL,
                content TEXT NOT NULL,
                provenance TEXT NOT NULL,
                source_event_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conversation_turns (
                turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                provenance TEXT NOT NULL,
                ledger_event_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tool_audit_log (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                args_sha256 TEXT NOT NULL,
                decision TEXT NOT NULL,
                reason TEXT NOT NULL,
                capability_nonce TEXT NOT NULL,
                latency_ms INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

    def close(self) -> None:
        self.hm.close()

    def __enter__(self) -> "CompanionMemoryStore":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def register_agent(
        self, *, owner_id: str, agent_id: str, role: str, model_ref: str
    ) -> None:
        self.db.execute(
            "INSERT INTO companion_agents(owner_id, agent_id, role, model_ref, created_at) "
            "VALUES(?, ?, ?, ?, ?) "
            "ON CONFLICT(owner_id, agent_id) DO UPDATE SET role=excluded.role, model_ref=excluded.model_ref",
            (owner_id, agent_id, role, model_ref, utc_now_iso()),
        )

    def list_agents(self, *, owner_id: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT agent_id, role, model_ref, created_at FROM companion_agents "
            "WHERE owner_id=? ORDER BY agent_id",
            (owner_id,),
        ).fetchall()
        result: list[dict[str, Any]] = []
        for aid, role, model_ref, created_at in rows:
            prob, estimator = self.hm.predict(
                owner_id=owner_id, agent_id=aid, requester_owner_id=owner_id
            )
            st = self.hm.get_state(
                owner_id=owner_id, agent_id=aid, requester_owner_id=owner_id
            )
            fact_cnt = self.db.execute(
                "SELECT COUNT(*) FROM knowledge_facts WHERE owner_id=? AND agent_id=?",
                (owner_id, aid),
            ).fetchone()[0]
            result.append({
                "agent_id": aid,
                "owner_id": owner_id,
                "role": role,
                "model_ref": model_ref,
                "created_at": created_at,
                "facts_count": fact_cnt,
                "hm_p1e": {
                    "reliability_estimate": round(prob, 4),
                    "estimator": estimator,
                    "observations": st["n"],
                    "successes": st["successes"],
                    "provenance": Provenance.INFERRED.value,
                },
            })
        return result

    def append_ledger(
        self,
        *,
        event_id: str,
        owner_id: str,
        agent_id: str,
        event_type: str,
        provenance: Provenance,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Atomically append one SHA-256 hash-chained exact ledger record."""
        if not isinstance(provenance, Provenance):
            raise TypeError("provenance must be an explicit Provenance enum")
        if provenance == Provenance.VERIFIED:
            raise ValueError("runtime cannot self-mint VERIFIED provenance")
        payload_json = canonical_json({
            "schema": LEDGER_SCHEMA_VERSION,
            "provenance": provenance.value,
            **payload,
        })
        payload_hash = sha256_hex(payload_json)
        # Validate via OpenWorld's core MemoryEvent contract.
        mem_event = MemoryEvent(
            event_id=event_id,
            owner_id=owner_id,
            event_type=event_type,
            provenance=provenance,
            payload=payload_json.encode("utf-8"),
            protected=True,
        )
        if route_memory_event(mem_event) != MemoryRoute.EXACT:
            raise AssertionError("exact ledger event failed EXACT routing")

        now = utc_now_iso()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            last = self.db.execute(
                "SELECT digest FROM exact_ledger ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            prev_hash = last[0] if last else "GENESIS"
            digest = sha256_hex(
                canonical_json([
                    event_id,
                    owner_id,
                    agent_id,
                    event_type,
                    provenance.value,
                    payload_hash,
                    prev_hash,
                    now,
                ])
            )
            cur = self.db.execute(
                "INSERT INTO exact_ledger("
                "event_id, owner_id, agent_id, event_type, provenance, "
                "payload_json, payload_sha256, prev_hash, digest, created_at"
                ") VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event_id,
                    owner_id,
                    agent_id,
                    event_type,
                    provenance.value,
                    payload_json,
                    payload_hash,
                    prev_hash,
                    digest,
                    now,
                ),
            )
            seq = int(cur.lastrowid)
            self.db.execute("COMMIT")
            return {
                "seq": seq,
                "event_id": event_id,
                "owner_id": owner_id,
                "agent_id": agent_id,
                "event_type": event_type,
                "provenance": provenance.value,
                "payload_sha256": payload_hash,
                "prev_hash": prev_hash,
                "digest": digest,
                "created_at": now,
            }
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def verify_ledger_chain(self) -> tuple[bool, int]:
        """Recompute and verify every SHA-256 link in `exact_ledger`."""
        rows = self.db.execute(
            "SELECT event_id, owner_id, agent_id, event_type, provenance, "
            "payload_json, payload_sha256, prev_hash, digest, created_at "
            "FROM exact_ledger ORDER BY seq ASC"
        ).fetchall()
        expected_prev = "GENESIS"
        for row in rows:
            (
                event_id,
                owner_id,
                agent_id,
                event_type,
                provenance,
                payload_json,
                payload_hash,
                prev_hash,
                digest,
                created_at,
            ) = row
            if prev_hash != expected_prev:
                return False, len(rows)
            if sha256_hex(payload_json) != payload_hash:
                return False, len(rows)
            recomputed = sha256_hex(
                canonical_json([
                    event_id,
                    owner_id,
                    agent_id,
                    event_type,
                    provenance,
                    payload_hash,
                    prev_hash,
                    created_at,
                ])
            )
            if recomputed != digest:
                return False, len(rows)
            expected_prev = digest
        return True, len(rows)

    def record_reliability_outcome(
        self,
        *,
        owner_id: str,
        agent_id: str,
        event_id: str,
        event_type: str,
        outcome: int,
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        """Train HyperMemoryP1e on real observed tool/delegation execution outcomes."""
        st = self.hm.get_state(
            owner_id=owner_id, agent_id=agent_id, requester_owner_id=owner_id
        )
        next_seq = st["seq"] + 1
        payload_bytes = canonical_json({
            "schema": LEDGER_SCHEMA_VERSION,
            "agent_id": agent_id,
            **evidence,
        }).encode("utf-8")
        ev = MemoryEvent(
            event_id=event_id,
            owner_id=owner_id,
            event_type=event_type,
            provenance=Provenance.OBSERVED_RECORDED,
            payload=payload_bytes,
            protected=True,
        )
        self.hm.apply_batch(
            (MemoryObservation(event=ev, agent_id=agent_id, sequence_number=next_seq, outcome=int(outcome)),),
            requester_owner_id=owner_id,
        )
        prob, est = self.hm.predict(
            owner_id=owner_id, agent_id=agent_id, requester_owner_id=owner_id
        )
        return {
            "probability": round(prob, 4),
            "estimator": est,
            "sequence": next_seq,
            "provenance": Provenance.INFERRED.value,
        }

    def save_fact(
        self,
        *,
        owner_id: str,
        agent_id: str,
        fact_key: str,
        content: str,
        provenance: Provenance,
        source_event_id: str,
        requester_owner_id: str,
    ) -> dict[str, Any]:
        if owner_id != requester_owner_id:
            raise PermissionError("cross-owner memory write denied")
        if provenance not in ALLOWED_FACT_PROVENANCE:
            raise ValueError("facts may only be stored as OBSERVED_RECORDED or INFERRED")
        key_clean = fact_key.strip()[:120]
        content_clean = content.strip()
        if not key_clean or not content_clean:
            raise ValueError("fact_key and content are required")
        if len(content_clean.encode("utf-8")) > MAX_FACT_BYTES:
            raise ValueError(f"fact content exceeds {MAX_FACT_BYTES} bytes")

        now = utc_now_iso()
        fact_id = "fact-" + sha256_hex(f"{owner_id}:{agent_id}:{key_clean}:{now}:{source_event_id}")[:16]
        self.db.execute(
            "INSERT INTO knowledge_facts("
            "fact_id, owner_id, agent_id, fact_key, content, provenance, source_event_id, created_at"
            ") VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (fact_id, owner_id, agent_id, key_clean, content_clean, provenance.value, source_event_id, now),
        )
        return {
            "fact_id": fact_id,
            "agent_id": agent_id,
            "fact_key": key_clean,
            "content": content_clean,
            "provenance": provenance.value,
            "source_event_id": source_event_id,
            "created_at": now,
        }

    def recall_facts(
        self,
        *,
        owner_id: str,
        agent_id: str,
        requester_owner_id: str,
        query: str = "",
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        """Retrieve scoped per-agent facts along with provenance and source event ID."""
        if owner_id != requester_owner_id:
            raise PermissionError("cross-owner memory read denied")
        tokens = [t.lower() for t in query.split() if len(t) >= 2]
        rows = self.db.execute(
            "SELECT fact_id, fact_key, content, provenance, source_event_id, created_at "
            "FROM knowledge_facts WHERE owner_id=? AND agent_id=? ORDER BY rowid DESC LIMIT 200",
            (owner_id, agent_id),
        ).fetchall()
        scored: list[tuple[int, dict[str, Any]]] = []
        for fid, fkey, content, prov, src_id, created in rows:
            haystack = f"{fkey} {content}".lower()
            score = sum(1 for t in tokens if t in haystack) if tokens else 1
            if not tokens or score > 0:
                scored.append((
                    score,
                    {
                        "fact_id": fid,
                        "agent_id": agent_id,
                        "fact_key": fkey,
                        "content": content,
                        "provenance": prov,
                        "source_event_id": src_id,
                        "created_at": created,
                    },
                ))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored[:limit]]

    def append_turn(
        self,
        *,
        owner_id: str,
        agent_id: str,
        role: str,
        content: str,
        provenance: Provenance,
        ledger_event_id: str,
    ) -> None:
        self.db.execute(
            "INSERT INTO conversation_turns("
            "owner_id, agent_id, role, content, provenance, ledger_event_id, created_at"
            ") VALUES(?, ?, ?, ?, ?, ?, ?)",
            (owner_id, agent_id, role, content, provenance.value, ledger_event_id, utc_now_iso()),
        )

    def recent_turns(
        self, *, owner_id: str, agent_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT turn_id, role, content, provenance, ledger_event_id, created_at "
            "FROM conversation_turns WHERE owner_id=? AND agent_id=? "
            "ORDER BY turn_id DESC LIMIT ?",
            (owner_id, agent_id, limit),
        ).fetchall()
        rows.reverse()
        return [
            {
                "turn_id": r[0],
                "role": r[1],
                "content": r[2],
                "provenance": r[3],
                "ledger_event_id": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]

    def record_tool_audit(
        self,
        *,
        owner_id: str,
        agent_id: str,
        tool_name: str,
        args: dict[str, Any],
        decision: str,
        reason: str,
        capability_nonce: str,
        latency_ms: int,
    ) -> None:
        self.db.execute(
            "INSERT INTO tool_audit_log("
            "owner_id, agent_id, tool_name, args_sha256, decision, reason, "
            "capability_nonce, latency_ms, created_at"
            ") VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                owner_id,
                agent_id,
                tool_name,
                sha256_hex(canonical_json(args)),
                decision,
                reason,
                capability_nonce,
                int(latency_ms),
                utc_now_iso(),
            ),
        )

    def recent_ledger(self, *, owner_id: str, limit: int = 25) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT seq, event_id, agent_id, event_type, provenance, payload_sha256, prev_hash, digest, created_at "
            "FROM exact_ledger WHERE owner_id=? ORDER BY seq DESC LIMIT ?",
            (owner_id, limit),
        ).fetchall()
        return [
            {
                "seq": r[0],
                "event_id": r[1],
                "agent_id": r[2],
                "event_type": r[3],
                "provenance": r[4],
                "payload_sha256": r[5],
                "prev_hash": r[6],
                "digest": r[7],
                "created_at": r[8],
            }
            for r in rows
        ]

    def recent_tool_audits(self, *, owner_id: str, limit: int = 25) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT audit_id, agent_id, tool_name, args_sha256, decision, reason, capability_nonce, latency_ms, created_at "
            "FROM tool_audit_log WHERE owner_id=? ORDER BY audit_id DESC LIMIT ?",
            (owner_id, limit),
        ).fetchall()
        return [
            {
                "audit_id": r[0],
                "agent_id": r[1],
                "tool_name": r[2],
                "args_sha256": r[3],
                "decision": r[4],
                "reason": r[5],
                "capability_nonce": r[6],
                "latency_ms": r[7],
                "created_at": r[8],
            }
            for r in rows
        ]
