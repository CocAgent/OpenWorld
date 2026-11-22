"""Bounded, capability-checked multi-agent communication over OpenWorld W3 + HM-P1e.

Research example aligned with OpenWorld R2/R3 roadmap:
- Separates agent identity, immutable genome, shared policy reference,
  per-agent HyperMemoryP1e state, hard DonorBudget risk cap, and scoped
  CapabilityAuthority grants.
- Anchors every agent-to-agent message to an authorized W3 world `signal`
  event through GuardedWorldGateway, preserving deterministic replay and
  resource conservation.
- Enforces same-owner isolation and sparse W3 graph adjacency by default.
- Verifies partner return claims against the authoritative W3 event ledger
  rather than trusting peer messages.
- Keeps third-party reputation updates strictly labeled `INFERRED` hearsay
  and never promotes simulated or inferred claims to verified history.

CPU-only, dependency-free Python 3.11+. No LLM, network call, paid API,
cross-owner consent protocol, or production security certification.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time
from typing import Mapping

# Allow direct execution from repository root (`python examples/communicating_agent.py`).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

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
from openworld_superkernel.trust_boundaries import CapabilityAuthority
from openworld_superkernel.world_fixture import (
    Action,
    Agent,
    Event,
    Observation as WorldObservation,
    Weather,
    World,
    create_world,
    verify_replay,
)
from openworld_superkernel.world_guard import (
    AuthorizedWorldAction,
    GuardedWorldGateway,
)

# ---------------------------------------------------------------------------
# Protocol constants and canonical serialization helpers
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "openworld.communicating-agent.v1"
MESSAGE_SCHEMA = "openworld.agent-msg.v1"
MODEL_REF_DEFAULT = "shared-policy.comm-adaptive.v1"
DEFAULT_OWNER = "openworld-comm-owner"
DEFAULT_PRINCIPAL = "trusted-local-comm-host"

MAX_ROUNDS = 20
MAX_ID_LENGTH = 128
MAX_PAYLOAD_BYTES = 1024
MAX_ACTIONS_PER_TICK = 16
SCENARIOS = ("cooperative", "hostile_refuse", "hostile_liar", "recovery")

# Allowed claim provenance values inside this local simulated research fixture.
# VERIFIED and OBSERVED_RECORDED are deliberately disallowed so simulated or
# inferred agent claims can never masquerade as verified outside-world history.
ALLOWED_SIMULATED_PROVENANCE = frozenset({
    Provenance.SIMULATED,
    Provenance.INFERRED,
})


def canonical_json(value: object) -> str:
    """Deterministic compact JSON encoding that rejects NaN/Infinity."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def sha256_text(text: str) -> str:
    """Compute hex SHA-256 over UTF-8 text."""
    return sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Layer 1: Identity, Genome, Relationship State (Identity != Model != Grants)
# ---------------------------------------------------------------------------


class Performative(str, Enum):
    """Finite set of allowed agent-to-agent communicative acts."""

    PING = "ping"
    PROPOSE = "propose"
    ACCEPT = "accept"
    DECLINE = "decline"
    COMMIT_ACK = "commit_ack"
    INFORM = "inform"


@dataclass(frozen=True, slots=True)
class AgentIdentity:
    """Persistent agent identity decoupled from shared model/policy weights."""

    agent_id: str
    owner_id: str
    region: str
    model_ref: str = MODEL_REF_DEFAULT

    def __post_init__(self) -> None:
        for field_name, value in (
            ("agent_id", self.agent_id),
            ("owner_id", self.owner_id),
            ("region", self.region),
            ("model_ref", self.model_ref),
        ):
            if not isinstance(value, str) or not value or len(value) > MAX_ID_LENGTH:
                raise ValueError(f"invalid {field_name}")


@dataclass(frozen=True, slots=True)
class AgentGenome:
    """Immutable bounded configuration traits for an agent's policy behavior."""

    role: str  # "negotiator" | "responder" | "observer"
    strategy: str  # "adaptive" | "cooperative" | "hostile_refuse" | "hostile_liar" | "recovery"
    propose_threshold: float = BREAK_EVEN
    min_reserve_balance: int = 1
    probe_interval: int = 4
    recover_at_round: int = 4
    share_reputation: bool = False

    def __post_init__(self) -> None:
        if self.role not in {"negotiator", "responder", "observer"}:
            raise ValueError("unknown agent role")
        if self.strategy not in {"adaptive", *SCENARIOS}:
            raise ValueError("unknown agent strategy")
        if not (0.0 <= self.propose_threshold <= 1.0):
            raise ValueError("propose_threshold must be in [0, 1]")
        if type(self.min_reserve_balance) is not int or self.min_reserve_balance < 0:
            raise ValueError("min_reserve_balance must be a nonnegative integer")
        if type(self.probe_interval) is not int or not 0 <= self.probe_interval <= MAX_ROUNDS:
            raise ValueError("probe_interval out of bounds")
        if type(self.recover_at_round) is not int or not 0 <= self.recover_at_round <= MAX_ROUNDS:
            raise ValueError("recover_at_round out of bounds")
        if not isinstance(self.share_reputation, bool):
            raise TypeError("share_reputation must be a boolean")


@dataclass
class PeerRelationship:
    """Private per-peer interaction history maintained by one agent."""

    peer_id: str
    messages_sent: int = 0
    messages_received: int = 0
    proposals_sent: int = 0
    proposals_accepted: int = 0
    proposals_declined: int = 0
    transfers_sent: int = 0
    returns_confirmed: int = 0
    unreturned_losses: int = 0
    unverified_acks_rejected: int = 0
    # Third-party INFORM messages stay strictly isolated as INFERRED hearsay.
    inferred_notes: list[dict[str, object]] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "peer_id": self.peer_id,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "proposals_sent": self.proposals_sent,
            "proposals_accepted": self.proposals_accepted,
            "proposals_declined": self.proposals_declined,
            "transfers_sent": self.transfers_sent,
            "returns_confirmed": self.returns_confirmed,
            "unreturned_losses": self.unreturned_losses,
            "unverified_acks_rejected": self.unverified_acks_rejected,
            "inferred_notes_count": len(self.inferred_notes),
            "last_inferred_note": self.inferred_notes[-1] if self.inferred_notes else None,
        }


# ---------------------------------------------------------------------------
# Layer 2: Typed, Bounded, Provenance-Tagged Message Envelopes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MessageDraft:
    """An agent's proposed outgoing message prior to W3 authorization & commit."""

    message_id: str
    thread_id: str
    sender_id: str
    receiver_id: str
    performative: Performative
    payload: dict[str, object]
    claim_provenance: Provenance = Provenance.SIMULATED
    in_reply_to: str | None = None

    def validate(self) -> str:
        """Validate bounds, types, and provenance; return canonical payload JSON."""
        for label, value in (
            ("message_id", self.message_id),
            ("thread_id", self.thread_id),
            ("sender_id", self.sender_id),
            ("receiver_id", self.receiver_id),
        ):
            if not isinstance(value, str) or not value or len(value) > MAX_ID_LENGTH:
                raise ValueError(f"invalid {label}")
        if self.in_reply_to is not None:
            if (
                not isinstance(self.in_reply_to, str)
                or not self.in_reply_to
                or len(self.in_reply_to) > MAX_ID_LENGTH
            ):
                raise ValueError("invalid in_reply_to")
        if self.sender_id == self.receiver_id:
            raise ValueError("self-messaging is disallowed")
        if not isinstance(self.performative, Performative):
            raise TypeError("performative must be a Performative enum")
        if not isinstance(self.claim_provenance, Provenance):
            raise TypeError("claim_provenance must be an explicit Provenance value")
        if self.claim_provenance not in ALLOWED_SIMULATED_PROVENANCE:
            raise ValueError(
                "simulated fixture refuses VERIFIED/OBSERVED_RECORDED/UNAVAILABLE message claims"
            )
        if not isinstance(self.payload, dict):
            raise TypeError("payload must be a JSON-serializable dict")
        encoded = canonical_json(self.payload)
        if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            raise ValueError(f"message payload exceeds {MAX_PAYLOAD_BYTES} bytes")
        return encoded


@dataclass(frozen=True, slots=True)
class AgentMessage:
    """Committed, hash-chained message anchored to an accepted W3 signal event."""

    schema_version: str
    message_id: str
    thread_id: str
    in_reply_to: str | None
    tick: int
    sender_id: str
    receiver_id: str
    owner_id: str
    performative: Performative
    payload_json: str
    claim_provenance: Provenance
    world_event_digest: str
    prev_log_hash: str
    digest: str

    def payload(self) -> dict[str, object]:
        return json.loads(self.payload_json)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "in_reply_to": self.in_reply_to,
            "tick": self.tick,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "owner_id": self.owner_id,
            "performative": self.performative.value,
            "payload": self.payload(),
            "claim_provenance": self.claim_provenance.value,
            "world_event_digest": self.world_event_digest,
            "prev_log_hash": self.prev_log_hash,
            "digest": self.digest,
        }


@dataclass(frozen=True, slots=True)
class TransferDraft:
    """An agent's proposed W3 resource transfer prior to capability dispatch."""

    request_id: str
    sender_id: str
    receiver_id: str
    amount: int
    thread_id: str

    def validate(self) -> None:
        for label, value in (
            ("request_id", self.request_id),
            ("sender_id", self.sender_id),
            ("receiver_id", self.receiver_id),
            ("thread_id", self.thread_id),
        ):
            if not isinstance(value, str) or not value or len(value) > MAX_ID_LENGTH:
                raise ValueError(f"invalid {label}")
        if self.sender_id == self.receiver_id:
            raise ValueError("self-transfer is disallowed")
        if type(self.amount) is not int or self.amount <= 0:
            raise ValueError("transfer amount must be a positive integer")


@dataclass(frozen=True, slots=True)
class TickDispatchResult:
    """Outcome of one atomic W3 tick containing messages and/or transfers."""

    tick: int
    committed_messages: tuple[AgentMessage, ...]
    committed_transfers: tuple[Event, ...]
    world_fingerprint: str


# ---------------------------------------------------------------------------
# Layer 3: Capability-Gated Bounded Communication Hub (SuperKernel Mediator)
# ---------------------------------------------------------------------------


class BoundedCommunicationHub:
    """Mediates all agent-to-agent messages and transfers over GuardedWorldGateway.

    Every send requires a valid `write_agent` capability; every inbox read
    requires a valid `read_world` capability. Cross-owner communication and
    non-neighbor messages fail closed before the W3 reducer executes.
    """

    def __init__(
        self,
        world: World,
        *,
        principal: str = DEFAULT_PRINCIPAL,
        issuer: str = "openworld-comm-hub",
        audience: str = "openworld-local-w3",
        max_actions_per_tick: int = MAX_ACTIONS_PER_TICK,
    ) -> None:
        if not isinstance(world, World):
            raise TypeError("expected W3 World fixture")
        if not isinstance(principal, str) or not principal:
            raise ValueError("trusted host principal required")
        if type(max_actions_per_tick) is not int or not 1 <= max_actions_per_tick <= 256:
            raise ValueError("max_actions_per_tick must be in 1..256")
        self.genesis: World = world
        self.world: World = world
        self.principal = principal
        self.max_actions_per_tick = max_actions_per_tick
        self.initial_total_resources = sum(dict(world.balances).values())
        # Ephemeral signing key owned strictly by the trusted host process.
        self.authority = CapabilityAuthority(
            os.urandom(32), issuer=issuer, audience=audience
        )
        self.gateway = GuardedWorldGateway(
            self.authority, authenticated_principal=lambda: self.principal
        )
        self._owners: dict[str, str] = {a.agent_id: a.owner_id for a in world.agents}
        self._graph: dict[str, tuple[str, ...]] = dict(world.graph)
        self._message_log: list[AgentMessage] = []
        self._seen_message_ids: set[str] = set()
        self._inboxes: dict[str, list[AgentMessage]] = {
            a.agent_id: [] for a in world.agents
        }

    @property
    def message_log(self) -> tuple[AgentMessage, ...]:
        return tuple(self._message_log)

    def issue_capability(
        self,
        agent_id: str,
        *,
        action: str,
        lifetime: int = 300,
        nonce: str | None = None,
    ) -> str:
        """Issue a scoped, short-lived HMAC capability for one registered agent."""
        owner = self._owners.get(agent_id)
        if owner is None:
            raise PermissionError(f"unknown agent_id: {agent_id}")
        now = int(time.time())
        return self.authority.issue(
            principal=self.principal,
            owner=owner,
            resource=agent_id,
            action=action,
            valid_from=now - 5,
            expires_at=now + lifetime,
            nonce=nonce,
        )

    def revoke_capability(self, nonce: str) -> None:
        """Immediately revoke a capability nonce in the host authority."""
        self.authority.revoke(nonce)

    def read_inbox(
        self,
        agent_id: str,
        *,
        read_capability: str,
        since_tick: int = 0,
    ) -> tuple[WorldObservation, tuple[AgentMessage, ...]]:
        """Authenticate read_world capability and return world observation + messages."""
        if type(since_tick) is not int or since_tick < 0:
            raise ValueError("since_tick must be a nonnegative integer")
        world_obs = self.gateway.observe(
            self.world, agent_id=agent_id, signed_capability=read_capability
        )
        # Cross-check that every returned message matches an authoritative W3 event digest.
        valid_digests = {e.digest for e in self.world.events if e.kind == "signal"}
        delivered: list[AgentMessage] = []
        for msg in self._inboxes[agent_id]:
            if msg.tick < since_tick:
                continue
            if msg.world_event_digest not in valid_digests:
                raise AssertionError("unanchored message detected in inbox")
            delivered.append(msg)
        return world_obs, tuple(delivered)

    def find_committed_transfer(
        self,
        *,
        sender_id: str,
        receiver_id: str,
        tick: int,
        amount: int,
    ) -> Event | None:
        """Verify an exact committed W3 transfer event directly in the world ledger.

        Agents call this instead of trusting a peer's `COMMIT_ACK` claim.
        """
        if type(tick) is not int or tick < 0 or type(amount) is not int or amount <= 0:
            raise ValueError("invalid transfer lookup parameters")
        matches = [
            event
            for event in self.world.events
            if event.tick == tick
            and event.kind == "transfer"
            and event.actor == sender_id
            and event.target == receiver_id
            and event.amount == amount
            and event.provenance == "SIMULATED"
        ]
        return matches[0] if len(matches) == 1 else None

    def dispatch_tick(
        self,
        *,
        messages: tuple[tuple[MessageDraft, str], ...] = (),
        transfers: tuple[tuple[TransferDraft, str], ...] = (),
        external: tuple[Weather, ...] = (),
    ) -> TickDispatchResult:
        """Atomically pre-check and commit one W3 tick of messages and transfers.

        All permission, quota, adjacency, ownership, provenance, and anti-replay
        checks execute BEFORE invoking GuardedWorldGateway.advance. If any item
        fails validation, the entire tick fails closed with zero state mutation.
        """
        if not isinstance(messages, tuple) or not isinstance(transfers, tuple):
            raise TypeError("messages and transfers must be immutable tuples")
        total_actions = len(messages) + len(transfers)
        if total_actions > self.max_actions_per_tick:
            raise ValueError("per-tick communication action budget exceeded")

        tick = self.world.tick
        seen_batch_ids: set[str] = set()
        authorized_actions: list[AuthorizedWorldAction] = []
        validated_messages: list[tuple[MessageDraft, str, str]] = []  # (draft, payload_json, owner)

        # 1. Pre-validate every outgoing message before mutating W3 world state.
        for draft, write_cap in messages:
            if not isinstance(draft, MessageDraft):
                raise TypeError("expected MessageDraft")
            payload_json = draft.validate()
            if (
                draft.message_id in self._seen_message_ids
                or draft.message_id in seen_batch_ids
                or draft.message_id in self.world.processed_ids
            ):
                raise ValueError(f"duplicate or replayed message_id: {draft.message_id}")
            seen_batch_ids.add(draft.message_id)
            sender_owner = self._owners.get(draft.sender_id)
            receiver_owner = self._owners.get(draft.receiver_id)
            if sender_owner is None or receiver_owner is None:
                raise PermissionError("unknown message sender or receiver")
            if sender_owner != receiver_owner:
                raise PermissionError(
                    "cross-owner agent communication is denied without bilateral consent"
                )
            if draft.receiver_id not in self._graph[draft.sender_id]:
                raise PermissionError("target is not a W3 graph neighbor")
            action = Action(
                request_id=draft.message_id,
                tick=tick,
                principal=sender_owner,
                actor=draft.sender_id,
                target=draft.receiver_id,
                kind="signal",
                amount=0,
            )
            authorized_actions.append(AuthorizedWorldAction(action, write_cap))
            validated_messages.append((draft, payload_json, sender_owner))

        # 2. Pre-validate every outgoing transfer before mutating W3 world state.
        for xfer, write_cap in transfers:
            if not isinstance(xfer, TransferDraft):
                raise TypeError("expected TransferDraft")
            xfer.validate()
            if (
                xfer.request_id in seen_batch_ids
                or xfer.request_id in self.world.processed_ids
            ):
                raise ValueError(f"duplicate transfer request_id: {xfer.request_id}")
            seen_batch_ids.add(xfer.request_id)
            sender_owner = self._owners.get(xfer.sender_id)
            receiver_owner = self._owners.get(xfer.receiver_id)
            if sender_owner is None or receiver_owner is None:
                raise PermissionError("unknown transfer sender or receiver")
            if sender_owner != receiver_owner:
                raise PermissionError(
                    "cross-owner transfer is denied without bilateral consent"
                )
            if xfer.receiver_id not in self._graph[xfer.sender_id]:
                raise PermissionError("transfer target is not a W3 graph neighbor")
            action = Action(
                request_id=xfer.request_id,
                tick=tick,
                principal=sender_owner,
                actor=xfer.sender_id,
                target=xfer.receiver_id,
                kind="transfer",
                amount=xfer.amount,
            )
            authorized_actions.append(AuthorizedWorldAction(action, write_cap))

        # 3. Commit the entire batch atomically through GuardedWorldGateway.
        prev_event_count = len(self.world.events)
        step = self.gateway.advance(
            self.world,
            actions=tuple(authorized_actions),
            external=external,
            max_actions=self.max_actions_per_tick,
        )
        if step.rejected:
            raise ValueError(f"W3 rejected authorized actions: {step.rejected}")
        if sum(dict(step.world.balances).values()) != self.initial_total_resources:
            raise AssertionError("W3 resource conservation invariant violated")

        self.world = step.world
        new_events = self.world.events[prev_event_count:]

        # 4. Anchor each accepted message to its exact W3 signal event digest.
        # W3 executes actions in canonical sorted order by request_id; align
        # signal events deterministically with validated_messages sorted by message_id.
        signal_events = [e for e in new_events if e.kind == "signal"]
        transfer_events = tuple(e for e in new_events if e.kind == "transfer")
        sorted_msgs = sorted(validated_messages, key=lambda item: item[0].message_id)
        if len(signal_events) != len(sorted_msgs):
            raise AssertionError("signal event count diverged from committed messages")

        committed_msgs: list[AgentMessage] = []
        for (draft, payload_json, owner_id), event in zip(sorted_msgs, signal_events):
            if event.actor != draft.sender_id or event.target != draft.receiver_id:
                raise AssertionError("signal event actor/target alignment mismatch")
            prev_hash = self._message_log[-1].digest if self._message_log else "GENESIS"
            envelope_body = [
                MESSAGE_SCHEMA,
                draft.message_id,
                draft.thread_id,
                draft.in_reply_to,
                tick,
                draft.sender_id,
                draft.receiver_id,
                owner_id,
                draft.performative.value,
                payload_json,
                draft.claim_provenance.value,
                event.digest,
                prev_hash,
            ]
            msg_digest = sha256_text(canonical_json(envelope_body))
            committed = AgentMessage(
                schema_version=MESSAGE_SCHEMA,
                message_id=draft.message_id,
                thread_id=draft.thread_id,
                in_reply_to=draft.in_reply_to,
                tick=tick,
                sender_id=draft.sender_id,
                receiver_id=draft.receiver_id,
                owner_id=owner_id,
                performative=draft.performative,
                payload_json=payload_json,
                claim_provenance=draft.claim_provenance,
                world_event_digest=event.digest,
                prev_log_hash=prev_hash,
                digest=msg_digest,
            )
            self._message_log.append(committed)
            self._seen_message_ids.add(committed.message_id)
            self._inboxes[committed.receiver_id].append(committed)
            committed_msgs.append(committed)

        return TickDispatchResult(
            tick=tick,
            committed_messages=tuple(committed_msgs),
            committed_transfers=transfer_events,
            world_fingerprint=self.world.fingerprint(),
        )

    def verify_integrity(self) -> bool:
        """Verify full W3 deterministic replay, provenance, and message hash chain."""
        verify_replay(self.genesis, self.world)
        if any(e.provenance != "SIMULATED" for e in self.world.events):
            raise AssertionError("unexpected non-simulated W3 event")
        if sum(dict(self.world.balances).values()) != self.initial_total_resources:
            raise AssertionError("resource conservation check failed")
        valid_signal_digests = {e.digest for e in self.world.events if e.kind == "signal"}
        expected_prev = "GENESIS"
        for msg in self._message_log:
            if msg.prev_log_hash != expected_prev:
                raise AssertionError("message log hash chain broken")
            if msg.world_event_digest not in valid_signal_digests:
                raise AssertionError("message lacks authoritative W3 signal anchor")
            recomputed = sha256_text(
                canonical_json([
                    msg.schema_version,
                    msg.message_id,
                    msg.thread_id,
                    msg.in_reply_to,
                    msg.tick,
                    msg.sender_id,
                    msg.receiver_id,
                    msg.owner_id,
                    msg.performative.value,
                    msg.payload_json,
                    msg.claim_provenance.value,
                    msg.world_event_digest,
                    msg.prev_log_hash,
                ])
            )
            if recomputed != msg.digest:
                raise AssertionError("message digest tampering detected")
            expected_prev = msg.digest
        return True


# ---------------------------------------------------------------------------
# Layer 4: Shared Policy Engine + CommunicatingAgent Model
# ---------------------------------------------------------------------------


def shared_policy_should_propose(
    *,
    genome: AgentGenome,
    predicted_cooperation: float,
    observations_count: int,
    budget: DonorBudget,
    balance: int,
    round_index: int,
) -> tuple[bool, str]:
    """Pure shared policy router referenced by AgentIdentity.model_ref.

    Multiple agents can share this decision function without sharing private
    memory, identity, or risk budget state.
    """
    if not budget.may_issue(balance):
        return False, "hard_risk_cap_or_empty_balance"
    if balance - 1 < genome.min_reserve_balance:
        return False, "reserve_balance_floor"
    if genome.strategy == "cooperative":
        return True, "always_propose_strategy"
    if observations_count < 2:
        return True, "initial_exploration"
    if predicted_cooperation > genome.propose_threshold:
        return True, "memory_prediction_above_threshold"
    if genome.probe_interval > 0 and round_index % genome.probe_interval == 0:
        return True, "scheduled_low_cost_probe"
    return False, "memory_prediction_below_threshold"


def shared_policy_evaluate_proposal(
    *,
    genome: AgentGenome,
    round_index: int,
    balance: int,
) -> tuple[Performative, str]:
    """Shared responder policy deciding whether to ACCEPT or DECLINE a proposal."""
    if genome.strategy == "cooperative":
        return Performative.ACCEPT, "cooperative_accept"
    if genome.strategy == "hostile_refuse":
        return Performative.DECLINE, "policy_refusal"
    if genome.strategy == "hostile_liar":
        # Adversary control: accepts verbally while intending to withhold return.
        return Performative.ACCEPT, "deceptive_accept"
    if genome.strategy == "recovery":
        if round_index >= genome.recover_at_round:
            return Performative.ACCEPT, "recovered_accept"
        return Performative.DECLINE, "pre_recovery_refusal"
    # Adaptive responder accepts when above reserve floor.
    if balance >= genome.min_reserve_balance:
        return Performative.ACCEPT, "adaptive_accept"
    return Performative.DECLINE, "insufficient_reserve"


def shared_policy_should_return_gift(
    *,
    genome: AgentGenome,
    round_index: int,
    balance: int,
) -> bool:
    """Shared responder policy deciding whether to execute the W3 return transfer."""
    if balance < 1:
        return False
    if genome.strategy == "cooperative":
        return True
    if genome.strategy == "hostile_liar":
        return False
    if genome.strategy == "hostile_refuse":
        return False
    if genome.strategy == "recovery":
        return round_index >= genome.recover_at_round
    return True


class CommunicatingAgent:
    """OpenWorld agent with isolated identity, HyperMemoryP1e, risk budget, and dialogue.

    Maps directly to OpenWorld's formal agent state:
      Agent_i(t) = (Identity_i, Genome_i, PredictiveState_i(t),
                    ExactLedger_i, Relationships_i(t), PolicyRef_i)
    """

    def __init__(
        self,
        identity: AgentIdentity,
        genome: AgentGenome,
        memory: HyperMemoryP1e,
    ) -> None:
        self.identity = identity
        self.genome = genome
        self.memory = memory
        # Hard risk-budget guard (CAP = 4) for outgoing resource transfers.
        self.budget = DonorBudget("always_offer")
        self.relationships: dict[str, PeerRelationship] = {}
        self.active_threads: dict[str, dict[str, object]] = {}
        self._last_read_tick: int = 0

    @property
    def agent_id(self) -> str:
        return self.identity.agent_id

    @property
    def owner_id(self) -> str:
        return self.identity.owner_id

    def relationship(self, peer_id: str) -> PeerRelationship:
        if peer_id not in self.relationships:
            self.relationships[peer_id] = PeerRelationship(peer_id=peer_id)
        return self.relationships[peer_id]

    def predict_cooperation(self) -> dict[str, object]:
        """Query HyperMemoryP1e and explicitly label the estimate INFERRED."""
        probability, estimator = self.memory.predict(
            owner_id=self.owner_id,
            agent_id=self.agent_id,
            requester_owner_id=self.owner_id,
        )
        state = self.memory.get_state(
            owner_id=self.owner_id,
            agent_id=self.agent_id,
            requester_owner_id=self.owner_id,
        )
        return {
            "probability": probability,
            "estimator": estimator,
            "observations": state["n"],
            "successes": state["successes"],
            "sequence": state["seq"],
            "provenance": Provenance.INFERRED.value,
        }

    def record_exact_outcome(
        self,
        *,
        event_id: str,
        event_type: str,
        outcome: int,
        evidence: Mapping[str, object],
    ) -> int:
        """Persist one exact SIMULATED observation into HyperMemoryP1e.

        Uses protected=True so route_memory_event strictly selects MemoryRoute.EXACT.
        """
        state = self.memory.get_state(
            owner_id=self.owner_id,
            agent_id=self.agent_id,
            requester_owner_id=self.owner_id,
        )
        next_seq = state["seq"] + 1
        payload_bytes = canonical_json({
            "schema": SCHEMA_VERSION,
            "agent_id": self.agent_id,
            "provenance": Provenance.SIMULATED.value,
            **dict(evidence),
        }).encode("utf-8")
        event = MemoryEvent(
            event_id=event_id,
            owner_id=self.owner_id,
            event_type=event_type,
            provenance=Provenance.SIMULATED,
            payload=payload_bytes,
            protected=True,
        )
        if route_memory_event(event) != MemoryRoute.EXACT:
            raise AssertionError("protected communication evidence must route to EXACT")
        observation = MemoryObservation(
            event=event,
            agent_id=self.agent_id,
            sequence_number=next_seq,
            outcome=int(outcome),
        )
        self.memory.apply_batch((observation,), requester_owner_id=self.owner_id)
        return next_seq

    def perceive(
        self,
        hub: BoundedCommunicationHub,
        *,
        read_capability: str,
    ) -> tuple[WorldObservation, tuple[AgentMessage, ...]]:
        """Step 1 (Observe): authenticate and pull unread verified messages."""
        world_obs, messages = hub.read_inbox(
            self.agent_id,
            read_capability=read_capability,
            since_tick=self._last_read_tick,
        )
        if messages:
            self._last_read_tick = max(m.tick for m in messages) + 1
        for msg in messages:
            rel = self.relationship(msg.sender_id)
            rel.messages_received += 1
            if msg.performative == Performative.INFORM:
                # Third-party INFORM messages are strictly isolated as INFERRED
                # hearsay; they never mutate exact_events or DonorBudget.
                body = msg.payload()
                subject = str(body.get("subject", msg.sender_id))
                subject_rel = self.relationship(subject)
                subject_rel.inferred_notes.append({
                    "from_peer": msg.sender_id,
                    "tick": msg.tick,
                    "message_id": msg.message_id,
                    "claim_provenance": msg.claim_provenance.value,
                    "payload": body,
                })
        return world_obs, messages

    def draft_proposal(
        self,
        *,
        target_id: str,
        world_obs: WorldObservation,
        round_index: int,
    ) -> tuple[MessageDraft | None, str]:
        """Phase 1 (Negotiator): decide whether to propose an exchange to target_id."""
        if target_id not in world_obs.neighbors:
            return None, "target_not_neighbor"
        pred = self.predict_cooperation()
        should_send, reason = shared_policy_should_propose(
            genome=self.genome,
            predicted_cooperation=float(pred["probability"]),
            observations_count=int(pred["observations"]),
            budget=self.budget,
            balance=world_obs.balance,
            round_index=round_index,
        )
        if not should_send:
            return None, reason

        thread_id = f"thread-r{round_index}-{self.agent_id}-{target_id}"
        msg_id = f"msg-r{round_index}-propose-{self.agent_id}-{target_id}"
        draft = MessageDraft(
            message_id=msg_id,
            thread_id=thread_id,
            sender_id=self.agent_id,
            receiver_id=target_id,
            performative=Performative.PROPOSE,
            payload={
                "proposal": "unit_exchange",
                "amount": 1,
                "expected_return": 1,
                "round": round_index,
            },
            claim_provenance=Provenance.SIMULATED,
        )
        rel = self.relationship(target_id)
        rel.messages_sent += 1
        rel.proposals_sent += 1
        self.active_threads[thread_id] = {
            "round": round_index,
            "peer": target_id,
            "state": "PROPOSED",
            "proposal_msg_id": msg_id,
        }
        return draft, reason

    def draft_reply_to_proposal(
        self,
        *,
        proposal: AgentMessage,
        world_obs: WorldObservation,
        round_index: int,
    ) -> MessageDraft:
        """Phase 2 (Responder): evaluate an incoming PROPOSE and draft ACCEPT/DECLINE."""
        performative, reason = shared_policy_evaluate_proposal(
            genome=self.genome,
            round_index=round_index,
            balance=world_obs.balance,
        )
        # Responder records the exact incoming proposal in its own HyperMemoryP1e.
        self.record_exact_outcome(
            event_id=f"mem-{self.agent_id}-proposal-r{round_index}",
            event_type="simulated_proposal_received",
            outcome=1 if performative == Performative.ACCEPT else 0,
            evidence={
                "round": round_index,
                "peer": proposal.sender_id,
                "proposal_msg_id": proposal.message_id,
                "world_event_digest": proposal.world_event_digest,
                "decision": performative.value,
                "reason": reason,
            },
        )
        draft = MessageDraft(
            message_id=f"msg-r{round_index}-{performative.value}-{self.agent_id}-{proposal.sender_id}",
            thread_id=proposal.thread_id,
            in_reply_to=proposal.message_id,
            sender_id=self.agent_id,
            receiver_id=proposal.sender_id,
            performative=performative,
            payload={
                "decision": performative.value,
                "reason": reason,
                "round": round_index,
            },
            claim_provenance=Provenance.SIMULATED,
        )
        self.relationship(proposal.sender_id).messages_sent += 1
        self.active_threads[proposal.thread_id] = {
            "round": round_index,
            "peer": proposal.sender_id,
            "state": performative.value.upper(),
            "proposal_msg_id": proposal.message_id,
        }
        return draft

    def handle_reply_and_draft_transfer(
        self,
        *,
        reply: AgentMessage,
        world_obs: WorldObservation,
        round_index: int,
    ) -> TransferDraft | None:
        """Phase 3 (Negotiator): process ACCEPT/DECLINE and optionally draft W3 transfer."""
        thread = self.active_threads.get(reply.thread_id)
        if thread is None or thread["peer"] != reply.sender_id:
            return None
        rel = self.relationship(reply.sender_id)
        if reply.performative == Performative.DECLINE:
            rel.proposals_declined += 1
            thread["state"] = "DECLINED"
            # Explicit refusal costs 0 resources and 0 risk budget, while updating memory.
            self.record_exact_outcome(
                event_id=f"mem-{self.agent_id}-decline-r{round_index}",
                event_type="simulated_proposal_declined",
                outcome=0,
                evidence={
                    "round": round_index,
                    "peer": reply.sender_id,
                    "reply_msg_id": reply.message_id,
                    "world_event_digest": reply.world_event_digest,
                },
            )
            return None
        if reply.performative == Performative.ACCEPT:
            rel.proposals_accepted += 1
            if not self.budget.may_issue(world_obs.balance):
                thread["state"] = "BLOCKED_BY_CAP"
                return None
            if world_obs.balance - 1 < self.genome.min_reserve_balance:
                thread["state"] = "BLOCKED_BY_RESERVE"
                return None
            thread["state"] = "TRANSFER_DRAFTED"
            return TransferDraft(
                request_id=f"xfer-r{round_index}-{self.agent_id}-{reply.sender_id}",
                sender_id=self.agent_id,
                receiver_id=reply.sender_id,
                amount=1,
                thread_id=reply.thread_id,
            )
        return None

    def mark_transfer_committed(
        self,
        *,
        thread_id: str,
        round_index: int,
        transfer_event: Event,
    ) -> None:
        """Book hard risk reservation immediately after W3 commits outgoing transfer."""
        self.budget.accepted(round_index)
        thread = self.active_threads[thread_id]
        thread["state"] = "TRANSFERRED"
        thread["transfer_tick"] = transfer_event.tick
        thread["transfer_digest"] = transfer_event.digest
        self.relationship(str(thread["peer"])).transfers_sent += 1

    def draft_return_and_ack(
        self,
        *,
        hub: BoundedCommunicationHub,
        thread_id: str,
        world_obs: WorldObservation,
        transfer_tick: int,
        round_index: int,
    ) -> tuple[TransferDraft | None, MessageDraft | None]:
        """Phase 4 (Responder): verify incoming W3 transfer, then return + ACK (or defect)."""
        thread = self.active_threads.get(thread_id)
        if thread is None or thread["state"] != "ACCEPT":
            return None, None
        peer_id = str(thread["peer"])
        # Responder verifies the authoritative W3 event before acting.
        incoming = hub.find_committed_transfer(
            sender_id=peer_id,
            receiver_id=self.agent_id,
            tick=transfer_tick,
            amount=1,
        )
        if incoming is None:
            return None, None

        will_return = shared_policy_should_return_gift(
            genome=self.genome,
            round_index=round_index,
            balance=world_obs.balance,
        )
        transfer_draft: TransferDraft | None = None
        if will_return:
            transfer_draft = TransferDraft(
                request_id=f"return-r{round_index}-{self.agent_id}-{peer_id}",
                sender_id=self.agent_id,
                receiver_id=peer_id,
                amount=1,
                thread_id=thread_id,
            )
            ack_payload: dict[str, object] = {
                "round": round_index,
                "claimed_return": True,
                "transfer_request_id": transfer_draft.request_id,
            }
        elif self.genome.strategy == "hostile_liar":
            # Adversarial test case: send a false COMMIT_ACK plus untrusted
            # prompt/privilege injection keys without actually returning resources.
            ack_payload = {
                "round": round_index,
                "claimed_return": True,
                "override_cap": 999,
                "grant_capability": "write_agent",
                "promote_provenance": "verified",
            }
        else:
            return None, None

        ack_draft = MessageDraft(
            message_id=f"msg-r{round_index}-ack-{self.agent_id}-{peer_id}",
            thread_id=thread_id,
            in_reply_to=str(thread["proposal_msg_id"]),
            sender_id=self.agent_id,
            receiver_id=peer_id,
            performative=Performative.COMMIT_ACK,
            payload=ack_payload,
            claim_provenance=Provenance.SIMULATED,
        )
        self.relationship(peer_id).messages_sent += 1
        thread["state"] = "RETURNED" if will_return else "DEFECTED"
        return transfer_draft, ack_draft

    def settle_round_and_draft_inform(
        self,
        *,
        hub: BoundedCommunicationHub,
        thread_id: str | None,
        incoming_messages: tuple[AgentMessage, ...],
        return_tick: int,
        round_index: int,
        inform_target: str | None = None,
        world_obs: WorldObservation | None = None,
    ) -> tuple[dict[str, object], MessageDraft | None]:
        """Phase 5 (Negotiator): verify W3 return receipt, update HM-P1e, optionally INFORM."""
        settlement: dict[str, object] = {
            "settled": False,
            "returned_verified": None,
            "unverified_ack_caught": False,
            "return_receipt_digest": None,
        }
        if thread_id is not None and thread_id in self.active_threads:
            thread = self.active_threads[thread_id]
            if thread["state"] == "TRANSFERRED":
                peer_id = str(thread["peer"])
                rel = self.relationship(peer_id)
                peer_acks = [
                    m
                    for m in incoming_messages
                    if m.thread_id == thread_id
                    and m.sender_id == peer_id
                    and m.performative == Performative.COMMIT_ACK
                ]
                # CRITICAL INVARIANT: Never trust a peer's COMMIT_ACK text claim!
                # Verify directly against the authoritative W3 transfer event ledger.
                verified_return = hub.find_committed_transfer(
                    sender_id=peer_id,
                    receiver_id=self.agent_id,
                    tick=return_tick,
                    amount=1,
                )
                returned = verified_return is not None
                if not returned and peer_acks:
                    rel.unverified_acks_rejected += 1
                    settlement["unverified_ack_caught"] = True
                self.budget.observed_outcome(round_index, returned, round_index)
                if returned:
                    rel.returns_confirmed += 1
                else:
                    rel.unreturned_losses += 1
                self.record_exact_outcome(
                    event_id=f"mem-{self.agent_id}-settle-r{round_index}",
                    event_type="simulated_exchange_settlement",
                    outcome=1 if returned else 0,
                    evidence={
                        "round": round_index,
                        "peer": peer_id,
                        "thread_id": thread_id,
                        "returned_verified": returned,
                        "return_receipt_digest": (
                            verified_return.digest if verified_return else None
                        ),
                        "unverified_ack_caught": settlement["unverified_ack_caught"],
                    },
                )
                thread["state"] = "SETTLED_RETURNED" if returned else "SETTLED_LOSS"
                settlement.update({
                    "settled": True,
                    "returned_verified": returned,
                    "return_receipt_digest": (
                        verified_return.digest if verified_return else None
                    ),
                })

        # Optional bounded knowledge sharing: send an explicitly INFERRED estimate
        # about `bob` to connected neighbor `carol`.
        inform_draft: MessageDraft | None = None
        if (
            self.genome.share_reputation
            and inform_target is not None
            and world_obs is not None
            and inform_target in world_obs.neighbors
        ):
            pred = self.predict_cooperation()
            inform_draft = MessageDraft(
                message_id=f"msg-r{round_index}-inform-{self.agent_id}-{inform_target}",
                thread_id=f"reputation-r{round_index}-{self.agent_id}-{inform_target}",
                sender_id=self.agent_id,
                receiver_id=inform_target,
                performative=Performative.INFORM,
                payload={
                    "subject": "bob",
                    "round": round_index,
                    "estimated_cooperation": round(float(pred["probability"]), 6),
                    "estimator": pred["estimator"],
                    "observations": pred["observations"],
                    "basis": "hm_p1e_inferred_not_verified",
                },
                # Reputation beliefs are explicitly tagged INFERRED, never SIMULATED/VERIFIED.
                claim_provenance=Provenance.INFERRED,
            )
            self.relationship(inform_target).messages_sent += 1

        return settlement, inform_draft

    def snapshot(self, world: World) -> dict[str, object]:
        """Auditable per-agent snapshot separating exact ledger counts from INFERRED state."""
        pred = self.predict_cooperation()
        return {
            "identity": {
                "agent_id": self.identity.agent_id,
                "owner_id": self.identity.owner_id,
                "region": self.identity.region,
                "model_ref": self.identity.model_ref,
            },
            "genome": {
                "role": self.genome.role,
                "strategy": self.genome.strategy,
                "propose_threshold": self.genome.propose_threshold,
                "min_reserve_balance": self.genome.min_reserve_balance,
                "probe_interval": self.genome.probe_interval,
                "recover_at_round": self.genome.recover_at_round,
                "share_reputation": self.genome.share_reputation,
            },
            "world_balance": dict(world.balances)[self.agent_id],
            "risk_budget": {
                "cap": CAP,
                "known_loss": self.budget.known_bad,
                "pending": sorted(self.budget.pending),
                "exposure": self.budget.exposure,
                "peak_exposure": self.budget.peak_exposure,
            },
            "memory_prediction": pred,
            "relationships": {
                peer: rel.to_dict() for peer, rel in sorted(self.relationships.items())
            },
        }


# ---------------------------------------------------------------------------
# Layer 5: Multi-Agent Simulation Orchestrator & CLI
# ---------------------------------------------------------------------------


def run_communication_session(
    *,
    scenario: str = "cooperative",
    rounds: int = 8,
    recover_at: int = 4,
    probe_interval: int = 4,
    seed: int = 2026,
    db_path: str | Path | None = None,
) -> dict[str, object]:
    """Run a bounded 3-agent (alice <-> bob, alice <-> carol) communication session.

    All three agents belong to the same synthetic owner and share one policy
    module while maintaining isolated identities, HyperMemoryP1e partitions,
    relationships, and capability tokens.
    """
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario}")
    if type(rounds) is not int or not 1 <= rounds <= MAX_ROUNDS:
        raise ValueError(f"rounds must be an integer in 1..{MAX_ROUNDS}")
    if type(recover_at) is not int or not 0 <= recover_at <= MAX_ROUNDS:
        raise ValueError(f"recover_at must be an integer in 0..{MAX_ROUNDS}")
    if type(probe_interval) is not int or not 0 <= probe_interval <= MAX_ROUNDS:
        raise ValueError(f"probe_interval must be an integer in 0..{MAX_ROUNDS}")
    if type(seed) is not int or not 0 <= seed < 2**31:
        raise ValueError("seed must be an integer in 0..2^31-1")

    memory_target: str | Path = ":memory:"
    if db_path is not None:
        resolved = Path(db_path).resolve()
        if resolved.exists():
            raise FileExistsError(
                "database already exists; choose a fresh path to avoid mixing experiments"
            )
        resolved.parent.mkdir(parents=True, exist_ok=True)
        memory_target = resolved

    # 1. Construct authoritative W3 sparse graph world.
    # Notice `bob` and `carol` share NO edge: only `alice` connects to both.
    w3_agents = (
        Agent("alice", DEFAULT_OWNER, "north", 8),
        Agent("bob", DEFAULT_OWNER, "north", 2),
        Agent("carol", DEFAULT_OWNER, "south", 4),
    )
    w3_edges = (("alice", "bob"), ("alice", "carol"))
    world = create_world(w3_agents, w3_edges, seed=seed)
    hub = BoundedCommunicationHub(world)

    # 2. Issue per-agent scoped capabilities (read_world + write_agent).
    read_caps = {
        a.agent_id: hub.issue_capability(a.agent_id, action="read_world")
        for a in w3_agents
    }
    write_caps = {
        a.agent_id: hub.issue_capability(a.agent_id, action="write_agent")
        for a in w3_agents
    }

    # 3. Initialize isolated HyperMemoryP1e store and three CommunicatingAgents.
    with HyperMemoryP1e(memory_target) as memory:
        alice = CommunicatingAgent(
            identity=AgentIdentity("alice", DEFAULT_OWNER, "north", MODEL_REF_DEFAULT),
            genome=AgentGenome(
                role="negotiator",
                strategy="adaptive",
                propose_threshold=BREAK_EVEN,
                min_reserve_balance=1,
                probe_interval=probe_interval,
                share_reputation=True,
            ),
            memory=memory,
        )
        bob = CommunicatingAgent(
            identity=AgentIdentity("bob", DEFAULT_OWNER, "north", MODEL_REF_DEFAULT),
            genome=AgentGenome(
                role="responder",
                strategy=scenario,
                min_reserve_balance=0,
                recover_at_round=recover_at,
            ),
            memory=memory,
        )
        carol = CommunicatingAgent(
            identity=AgentIdentity("carol", DEFAULT_OWNER, "south", MODEL_REF_DEFAULT),
            genome=AgentGenome(
                role="observer",
                strategy="cooperative",
                min_reserve_balance=1,
            ),
            memory=memory,
        )

        trace: list[dict[str, object]] = []
        for rnd in range(rounds):
            # --- Phase 1 (Tick 5*r + 0): Alice decides whether to PROPOSE to Bob ---
            alice_obs, _ = alice.perceive(hub, read_capability=read_caps["alice"])
            proposal_draft, propose_reason = alice.draft_proposal(
                target_id="bob", world_obs=alice_obs, round_index=rnd
            )
            p1 = hub.dispatch_tick(
                messages=((proposal_draft, write_caps["alice"]),)
                if proposal_draft is not None
                else ()
            )
            active_thread_id = proposal_draft.thread_id if proposal_draft else None

            # --- Phase 2 (Tick 5*r + 1): Bob perceives PROPOSE and sends ACCEPT/DECLINE ---
            bob_obs, bob_inbox = bob.perceive(hub, read_capability=read_caps["bob"])
            incoming_proposals = [
                m for m in bob_inbox if m.performative == Performative.PROPOSE
            ]
            reply_draft: MessageDraft | None = None
            if incoming_proposals:
                reply_draft = bob.draft_reply_to_proposal(
                    proposal=incoming_proposals[-1],
                    world_obs=bob_obs,
                    round_index=rnd,
                )
            p2 = hub.dispatch_tick(
                messages=((reply_draft, write_caps["bob"]),)
                if reply_draft is not None
                else ()
            )

            # --- Phase 3 (Tick 5*r + 2): Alice perceives reply and commits W3 transfer ---
            alice_obs, alice_inbox = alice.perceive(
                hub, read_capability=read_caps["alice"]
            )
            transfer_draft: TransferDraft | None = None
            for msg in alice_inbox:
                if msg.thread_id == active_thread_id and msg.performative in (
                    Performative.ACCEPT,
                    Performative.DECLINE,
                ):
                    transfer_draft = alice.handle_reply_and_draft_transfer(
                        reply=msg, world_obs=alice_obs, round_index=rnd
                    )
            p3 = hub.dispatch_tick(
                transfers=((transfer_draft, write_caps["alice"]),)
                if transfer_draft is not None
                else ()
            )
            transfer_tick = p3.tick
            if p3.committed_transfers and active_thread_id is not None:
                alice.mark_transfer_committed(
                    thread_id=active_thread_id,
                    round_index=rnd,
                    transfer_event=p3.committed_transfers[0],
                )

            # --- Phase 4 (Tick 5*r + 3): Bob verifies incoming W3 transfer, returns + ACKs ---
            bob_obs, _ = bob.perceive(hub, read_capability=read_caps["bob"])
            return_draft: TransferDraft | None = None
            ack_draft: MessageDraft | None = None
            if active_thread_id is not None and p3.committed_transfers:
                return_draft, ack_draft = bob.draft_return_and_ack(
                    hub=hub,
                    thread_id=active_thread_id,
                    world_obs=bob_obs,
                    transfer_tick=transfer_tick,
                    round_index=rnd,
                )
            p4 = hub.dispatch_tick(
                messages=((ack_draft, write_caps["bob"]),) if ack_draft else (),
                transfers=((return_draft, write_caps["bob"]),) if return_draft else (),
            )
            return_tick = p4.tick

            # --- Phase 5 (Tick 5*r + 4): Alice verifies W3 receipt, updates HM-P1e, INFORMs Carol ---
            alice_obs, alice_ack_inbox = alice.perceive(
                hub, read_capability=read_caps["alice"]
            )
            settlement, inform_draft = alice.settle_round_and_draft_inform(
                hub=hub,
                thread_id=active_thread_id,
                incoming_messages=alice_ack_inbox,
                return_tick=return_tick,
                round_index=rnd,
                inform_target="carol",
                world_obs=alice_obs,
            )
            p5 = hub.dispatch_tick(
                messages=((inform_draft, write_caps["alice"]),) if inform_draft else ()
            )
            # Carol observes the world and ingests Alice's INFORM strictly as INFERRED hearsay.
            carol.perceive(hub, read_capability=read_caps["carol"])

            # Hard safety invariants enforced on every single round.
            if alice.budget.exposure > CAP:
                raise AssertionError("donor hard exposure cap breached")
            alice_pred = alice.predict_cooperation()
            trace.append({
                "round": rnd + 1,
                "ticks": [p1.tick, p2.tick, p3.tick, p4.tick, p5.tick],
                "alice_proposed": proposal_draft is not None,
                "propose_reason": propose_reason,
                "bob_reply": reply_draft.performative.value if reply_draft else "none",
                "alice_transferred": bool(p3.committed_transfers),
                "bob_returned": bool(p4.committed_transfers),
                "bob_sent_ack": ack_draft is not None,
                "unverified_ack_caught": settlement["unverified_ack_caught"],
                "alice_prediction_after": {
                    "probability": round(float(alice_pred["probability"]), 4),
                    "estimator": alice_pred["estimator"],
                    "provenance": alice_pred["provenance"],
                },
                "alice_exposure": alice.budget.exposure,
                "alice_known_loss": alice.budget.known_bad,
                "inform_to_carol": inform_draft is not None,
                "balances": dict(hub.world.balances),
            })

        # Verify full W3 replay, resource conservation, and hash-chained message log.
        hub.verify_integrity()
        exact_events_count = memory.db.execute(
            "SELECT COUNT(*) FROM exact_events"
        ).fetchone()[0]

        return {
            "schema": SCHEMA_VERSION,
            "scenario": scenario,
            "rounds": rounds,
            "seed": seed,
            "owner_id": DEFAULT_OWNER,
            "database": str(memory_target),
            "total_ticks": hub.world.tick,
            "total_world_events": len(hub.world.events),
            "total_messages": len(hub.message_log),
            "exact_memory_events": exact_events_count,
            "initial_total_resources": hub.initial_total_resources,
            "final_total_resources": sum(dict(hub.world.balances).values()),
            "balances": dict(hub.world.balances),
            "world_fingerprint": hub.world.fingerprint(),
            "replay_verified": True,
            "provenance": Provenance.SIMULATED.value,
            "agents": {
                "alice": alice.snapshot(hub.world),
                "bob": bob.snapshot(hub.world),
                "carol": carol.snapshot(hub.world),
            },
            "messages": [m.to_dict() for m in hub.message_log],
            "trace": trace,
            "limits": (
                "Same-owner, CPU-only, SIMULATED multi-agent communication lab. "
                "No LLM, network transport, cross-owner bilateral consent, or "
                "production security certification."
            ),
        }


def _print_summary(result: dict[str, object]) -> None:
    print(
        f"OpenWorld Communicating Agents | scenario={result['scenario']} "
        f"rounds={result['rounds']} seed={result['seed']} | SIMULATED, same owner"
    )
    print("Graph: alice <-> bob, alice <-> carol (bob and carol are not neighbors)")
    print("-" * 92)
    for row in result["trace"]:
        pred = row["alice_prediction_after"]
        ack_tag = "FAKE_ACK_CAUGHT" if row["unverified_ack_caught"] else (
            "ack" if row["bob_sent_ack"] else "no-ack"
        )
        print(
            f"round {row['round']:02d} | propose={int(row['alice_proposed'])} "
            f"({row['propose_reason']:32s}) | bob={row['bob_reply']:7s} "
            f"| xfer={int(row['alice_transferred'])} ret={int(row['bob_returned'])} "
            f"{ack_tag:15s} | p_inferred={pred['probability']:.4f} ({pred['estimator']:6s}) "
            f"| loss={row['alice_known_loss']}/{CAP} | bal={row['balances']}"
        )
    print("-" * 92)
    carol_rel = result["agents"]["carol"]["relationships"].get("bob", {})
    print(
        f"messages={result['total_messages']} world_events={result['total_world_events']} "
        f"exact_memory_events={result['exact_memory_events']} "
        f"carol_inferred_notes_about_bob={carol_rel.get('inferred_notes_count', 0)} "
        f"conservation={result['final_total_resources']}/{result['initial_total_resources']} "
        f"replay={'PASS' if result['replay_verified'] else 'FAIL'}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, default="cooperative")
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--recover-at", type=int, default=4)
    parser.add_argument("--probe-interval", type=int, default=4)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument(
        "--db",
        type=Path,
        help="optional new SQLite file path to persist HyperMemoryP1e tables",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print complete structured JSON trace and message log",
    )
    args = parser.parse_args()
    try:
        result = run_communication_session(
            scenario=args.scenario,
            rounds=args.rounds,
            recover_at=args.recover_at,
            probe_interval=args.probe_interval,
            seed=args.seed,
            db_path=args.db,
        )
    except (ValueError, PermissionError, FileExistsError, OSError) as exc:
        parser.exit(1, f"Session stopped: {exc}\n")

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    else:
        _print_summary(result)


if __name__ == "__main__":
    main()
