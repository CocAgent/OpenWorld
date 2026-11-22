"""OpenWorld Companion & Multi-Agent Runtime (R2/R3 local research implementation).

Combines OpenWorld's existing SuperKernel primitives (CapabilityAuthority,
HyperMemoryP1e, Provenance, MemoryEvent) with a multi-provider LLM router,
sandboxed real tools, explicit human approval gates for consequential writes,
persistent SQLite exact ledger + searchable memory, and peer-agent delegation.
"""
from __future__ import annotations

from .memory_store import CompanionMemoryStore
from .model_router import ModelConfig, ModelRouter
from .runtime import OpenWorldAgentRuntime
from .tool_gateway import PendingApproval, SandboxedToolGateway

__all__ = [
    "CompanionMemoryStore",
    "ModelConfig",
    "ModelRouter",
    "OpenWorldAgentRuntime",
    "PendingApproval",
    "SandboxedToolGateway",
]
