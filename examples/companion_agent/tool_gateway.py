"""Capability-gated, sandboxed real tool gateway backed by CapabilityAuthority.

Security boundaries enforced on every call:
1. Every read/compute/write tool call requires a valid, non-revoked HMAC token
   verified by OpenWorld's `CapabilityAuthority`.
2. File paths are canonicalized and confined strictly inside `workspace_root`;
   path traversal (`..`), symlink escapes, and sensitive secret patterns
   (`.env`, `*token*`, `*secret*`, `.git/config`) fail closed.
3. Consequential filesystem writes (`write_note`) are restricted to
   `<workspace>/data/agent_notes/` AND pause for explicit human approval bound
   to a canonical SHA-256 `intent_digest` before touching disk.
4. Arithmetic evaluation uses Python's `ast` parser over a tiny numeric allowlist
   (never `eval()`).
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import math
from pathlib import Path
import secrets
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from openworld_superkernel.memory_contracts import Provenance
from openworld_superkernel.trust_boundaries import CapabilityAuthority

from .memory_store import CompanionMemoryStore, canonical_json, sha256_hex

MAX_READ_BYTES = 16384
MAX_WRITE_BYTES = 16384
MAX_SEARCH_RESULTS = 20
MAX_LIST_ENTRIES = 80

SENSITIVE_NAME_FRAGMENTS = (
    ".env",
    "secret",
    "token",
    "credential",
    "id_rsa",
    "private_key",
    ".pem",
    ".key",
)

# Tool schemas exposed to LLMs (OpenAI / Ollama / Gemini compatible JSON Schema).
TOOL_SPECS: dict[str, dict[str, Any]] = {
    "list_files": {
        "name": "list_files",
        "description": "List files inside a relative directory of the OpenWorld workspace (read-only).",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Relative directory path, e.g. '.' or 'src/openworld_superkernel'."},
                "pattern": {"type": "string", "description": "Optional glob pattern, e.g. '*.py' or '*.md'."},
            },
        },
    },
    "read_file": {
        "name": "read_file",
        "description": "Read bounded line-numbered text from a workspace file (read-only, blocks secret files).",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path inside workspace, e.g. 'README.md'."},
                "start_line": {"type": "integer", "description": "1-based starting line number."},
                "max_lines": {"type": "integer", "description": "Maximum lines to read (1..120)."},
            },
            "required": ["path"],
        },
    },
    "search_text": {
        "name": "search_text",
        "description": "Case-insensitive text search across workspace source and documentation files (read-only).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Substring to search for."},
                "directory": {"type": "string", "description": "Relative subdirectory to search (default '.')."},
                "max_results": {"type": "integer", "description": "Maximum matches to return (1..20)."},
            },
            "required": ["query"],
        },
    },
    "calculate": {
        "name": "calculate",
        "description": "Evaluate an arithmetic expression safely using AST parsing (no eval).",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Numeric expression, e.g. '(1 - 0.25/0.85) * 960'."},
            },
            "required": ["expression"],
        },
    },
    "recall_memory": {
        "name": "recall_memory",
        "description": "Search this agent's persistent SQLite knowledge facts (returns value + provenance).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keywords to filter stored facts (empty returns latest facts)."},
            },
        },
    },
    "save_memory": {
        "name": "save_memory",
        "description": "Save a persistent fact into this agent's SQLite memory with explicit provenance (observed_recorded or inferred).",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Short topic label."},
                "content": {"type": "string", "description": "Fact content to persist."},
                "provenance": {"type": "string", "enum": ["observed_recorded", "inferred"]},
            },
            "required": ["key", "content"],
        },
    },
    "write_note": {
        "name": "write_note",
        "description": "Write a markdown/text note into data/agent_notes/. CONSEQUENTIAL: requires explicit human approval before writing.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Simple filename ending in .md or .txt (no subdirectories)."},
                "content": {"type": "string", "description": "Text content to write."},
            },
            "required": ["filename", "content"],
        },
    },
    "delegate_to_agent": {
        "name": "delegate_to_agent",
        "description": "Delegate an independent verification or research subtask to peer agent `atlas` via CapabilityAuthority.",
        "parameters": {
            "type": "object",
            "properties": {
                "target_agent": {"type": "string", "enum": ["atlas"]},
                "task": {"type": "string", "description": "Specific question or claim for Atlas to verify."},
                "context": {"type": "string", "description": "Supporting context or file references."},
            },
            "required": ["target_agent", "task"],
        },
    },
}


@dataclass
class PendingApproval:
    """Explicit human consent ticket bound to a canonical SHA-256 intent digest."""

    approval_id: str
    agent_id: str
    owner_id: str
    tool_name: str
    arguments: dict[str, Any]
    intent_digest: str
    created_at: float
    expires_at: float
    status: str = "pending"  # pending | approved | denied | expired

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "agent_id": self.agent_id,
            "owner_id": self.owner_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "intent_digest": self.intent_digest,
            "status": self.status,
            "expires_at": int(self.expires_at),
        }


def _safe_eval_math(expression: str) -> float:
    """Safe numeric AST evaluator supporting basic arithmetic and selected math functions."""
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 256:
        raise ValueError("invalid arithmetic expression")
    tree = ast.parse(expression, mode="eval")
    funcs = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sqrt": math.sqrt,
        "log": math.log,
        "exp": math.exp,
    }
    constants = {"pi": math.pi, "e": math.e}

    def _visit(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            val = float(node.value)
            if not math.isfinite(val):
                raise ValueError("nonfinite constant")
            return val
        if isinstance(node, ast.Name) and node.id in constants:
            return constants[node.id]
        if isinstance(node, ast.UnaryOp):
            operand = _visit(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            raise ValueError("unsupported unary operator")
        if isinstance(node, ast.BinOp):
            left = _visit(node.left)
            right = _visit(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    raise ValueError("division by zero")
                return left / right
            if isinstance(node.op, ast.FloorDiv):
                if right == 0:
                    raise ValueError("division by zero")
                return left // right
            if isinstance(node.op, ast.Mod):
                if right == 0:
                    raise ValueError("modulo by zero")
                return left % right
            if isinstance(node.op, ast.Pow):
                if abs(right) > 1000:
                    raise ValueError("exponent out of safe bounds")
                return left ** right
            raise ValueError("unsupported binary operator")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in funcs:
            if node.keywords:
                raise ValueError("keyword arguments disallowed in math expression")
            args = [_visit(arg) for arg in node.args]
            return float(funcs[node.func.id](*args))
        raise ValueError("disallowed syntax in arithmetic expression")

    result = _visit(tree)
    if not math.isfinite(result):
        raise ValueError("arithmetic result is nonfinite")
    return result


class SandboxedToolGateway:
    """Executes real local tools strictly inside workspace + capability + consent bounds."""

    def __init__(
        self,
        *,
        workspace_root: str | Path,
        owner_id: str,
        principal: str,
        authority: CapabilityAuthority,
        memory: CompanionMemoryStore,
        notes_subdir: str = "data/agent_notes",
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.notes_dir = (self.workspace_root / notes_subdir).resolve()
        if not self.notes_dir.is_relative_to(self.workspace_root):
            raise ValueError("notes directory must stay inside workspace_root")
        self.owner_id = owner_id
        self.principal = principal
        self.authority = authority
        self.memory = memory
        self.pending_approvals: dict[str, PendingApproval] = {}

    def _is_sensitive_path(self, resolved: Path) -> bool:
        rel = str(resolved.relative_to(self.workspace_root)).lower()
        parts = set(resolved.parts)
        if ".git" in parts:
            return True
        name = resolved.name.lower()
        return any(frag in name or frag in rel for frag in SENSITIVE_NAME_FRAGMENTS)

    def _safe_resolve(self, relative_path: str) -> Path:
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("path must be a nonempty string")
        candidate = Path(relative_path)
        if candidate.is_absolute():
            raise PermissionError("absolute paths are denied outside workspace sandbox")
        resolved = (self.workspace_root / candidate).resolve()
        if not resolved.is_relative_to(self.workspace_root):
            raise PermissionError("path traversal outside workspace sandbox denied")
        if self._is_sensitive_path(resolved):
            raise PermissionError("access to sensitive or secret-bearing path denied")
        return resolved

    def _authorize(self, *, agent_id: str, capability_token: str, action: str) -> str:
        grant = self.authority.verify(
            capability_token,
            authenticated_principal=self.principal,
            owner=self.owner_id,
            resource=agent_id,
            action=action,
        )
        return grant.nonce

    def execute_tool(
        self,
        *,
        agent_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        read_capability: str,
        write_capability: str | None = None,
    ) -> dict[str, Any]:
        """Authorize and execute one tool call, returning provenance-tagged output."""
        t0 = time.perf_counter()
        args = dict(arguments or {})
        nonce = "none"
        try:
            if tool_name in ("list_files", "read_file", "search_text", "calculate", "recall_memory"):
                nonce = self._authorize(agent_id=agent_id, capability_token=read_capability, action="read_world")
                if tool_name == "list_files":
                    output = self._tool_list_files(args)
                elif tool_name == "read_file":
                    output = self._tool_read_file(args)
                elif tool_name == "search_text":
                    output = self._tool_search_text(args)
                elif tool_name == "calculate":
                    output = self._tool_calculate(args)
                else:
                    output = self._tool_recall_memory(agent_id, args)
                decision = "ALLOW"
                reason = "scoped_read_capability_verified"
            elif tool_name == "save_memory":
                if not write_capability:
                    raise PermissionError("write_agent capability required for save_memory")
                nonce = self._authorize(agent_id=agent_id, capability_token=write_capability, action="write_agent")
                output = self._tool_save_memory(agent_id, args)
                decision = "ALLOW"
                reason = "scoped_write_memory_verified"
            elif tool_name == "write_note":
                if not write_capability:
                    raise PermissionError("write_agent capability required for write_note")
                nonce = self._authorize(agent_id=agent_id, capability_token=write_capability, action="write_agent")
                approval = self._stage_write_note_approval(agent_id, args)
                decision = "PENDING_HUMAN_APPROVAL"
                reason = "consequential_write_requires_explicit_consent"
                output = {
                    "status": "approval_required",
                    "approval": approval.to_dict(),
                    "message": (
                        f"Consequential action `write_note` for `{approval.arguments['filename']}` "
                        f"paused pending explicit human consent (intent_digest={approval.intent_digest[:16]}...)."
                    ),
                }
            else:
                raise ValueError(f"unknown tool: {tool_name}")

            elapsed = int((time.perf_counter() - t0) * 1000)
            self.memory.record_tool_audit(
                owner_id=self.owner_id,
                agent_id=agent_id,
                tool_name=tool_name,
                args=args,
                decision=decision,
                reason=reason,
                capability_nonce=nonce,
                latency_ms=elapsed,
            )
            return {
                "ok": True,
                "decision": decision,
                "tool": tool_name,
                "provenance": Provenance.OBSERVED_RECORDED.value,
                "untrusted_tool_output": True,
                "latency_ms": elapsed,
                "output": output,
            }
        except (PermissionError, ValueError, OSError) as exc:
            elapsed = int((time.perf_counter() - t0) * 1000)
            self.memory.record_tool_audit(
                owner_id=self.owner_id,
                agent_id=agent_id,
                tool_name=tool_name,
                args=args,
                decision="DENY",
                reason=f"{type(exc).__name__}: {exc}",
                capability_nonce=nonce,
                latency_ms=elapsed,
            )
            raise

    def _stage_write_note_approval(self, agent_id: str, args: dict[str, Any]) -> PendingApproval:
        filename = str(args.get("filename") or "").strip()
        content = str(args.get("content") or "")
        if (
            not filename
            or "/" in filename
            or "\\" in filename
            or ".." in filename
            or not filename.endswith((".md", ".txt"))
            or len(filename) > 80
        ):
            raise ValueError("filename must be a simple .md or .txt name without directories")
        if len(content.encode("utf-8")) > MAX_WRITE_BYTES:
            raise ValueError(f"note content exceeds {MAX_WRITE_BYTES} bytes")
        if self._is_sensitive_path(self.notes_dir / filename):
            raise PermissionError("refusing to write sensitive filename")

        now = time.time()
        clean_args = {"filename": filename, "content": content}
        approval_id = "apr-" + secrets.token_hex(6)
        intent_digest = sha256_hex(
            canonical_json({
                "approval_id": approval_id,
                "owner_id": self.owner_id,
                "agent_id": agent_id,
                "tool": "write_note",
                "arguments": clean_args,
            })
        )
        ticket = PendingApproval(
            approval_id=approval_id,
            agent_id=agent_id,
            owner_id=self.owner_id,
            tool_name="write_note",
            arguments=clean_args,
            intent_digest=intent_digest,
            created_at=now,
            expires_at=now + 600,
        )
        self.pending_approvals[approval_id] = ticket
        self.memory.append_ledger(
            event_id=f"ledger-consent-req-{approval_id}",
            owner_id=self.owner_id,
            agent_id=agent_id,
            event_type="consent",
            provenance=Provenance.OBSERVED_RECORDED,
            payload={"stage": "requested", **ticket.to_dict()},
        )
        return ticket

    def resolve_approval(
        self,
        *,
        approval_id: str,
        approved: bool,
        write_capability: str | None = None,
    ) -> dict[str, Any]:
        """Explicitly approve or deny a staged consequential action."""
        ticket = self.pending_approvals.get(approval_id)
        if ticket is None:
            raise ValueError(f"unknown approval_id: {approval_id}")
        if ticket.status != "pending":
            raise ValueError(f"approval {approval_id} already resolved ({ticket.status})")
        if time.time() > ticket.expires_at:
            ticket.status = "expired"
            raise ValueError(f"approval {approval_id} expired")

        if not approved:
            ticket.status = "denied"
            ledger = self.memory.append_ledger(
                event_id=f"ledger-consent-deny-{approval_id}",
                owner_id=self.owner_id,
                agent_id=ticket.agent_id,
                event_type="consent",
                provenance=Provenance.OBSERVED_RECORDED,
                payload={"stage": "denied", "approval_id": approval_id, "intent_digest": ticket.intent_digest},
            )
            return {
                "approval": ticket.to_dict(),
                "executed": False,
                "ledger_digest": ledger["digest"],
            }

        if not write_capability:
            raise PermissionError("valid write_agent capability required to execute approved write")
        nonce = self._authorize(
            agent_id=ticket.agent_id,
            capability_token=write_capability,
            action="write_agent",
        )
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        target = (self.notes_dir / ticket.arguments["filename"]).resolve()
        if not target.is_relative_to(self.notes_dir):
            raise PermissionError("resolved note path escaped notes sandbox")
        content = ticket.arguments["content"]
        target.write_text(content, encoding="utf-8")
        ticket.status = "approved"
        rel_written = str(target.relative_to(self.workspace_root))
        ledger = self.memory.append_ledger(
            event_id=f"ledger-consent-exec-{approval_id}",
            owner_id=self.owner_id,
            agent_id=ticket.agent_id,
            event_type="external_action",
            provenance=Provenance.OBSERVED_RECORDED,
            payload={
                "stage": "approved_and_executed",
                "approval_id": approval_id,
                "intent_digest": ticket.intent_digest,
                "written_path": rel_written,
                "bytes_written": len(content.encode("utf-8")),
                "content_sha256": sha256_hex(content),
            },
        )
        self.memory.record_tool_audit(
            owner_id=self.owner_id,
            agent_id=ticket.agent_id,
            tool_name="write_note",
            args={"filename": ticket.arguments["filename"]},
            decision="APPROVED_EXECUTED",
            reason="explicit_human_consent_granted",
            capability_nonce=nonce,
            latency_ms=1,
        )
        return {
            "approval": ticket.to_dict(),
            "executed": True,
            "written_path": rel_written,
            "bytes_written": len(content.encode("utf-8")),
            "ledger_digest": ledger["digest"],
        }

    # --- Read & Compute Tool Implementations ---

    def _tool_list_files(self, args: dict[str, Any]) -> dict[str, Any]:
        directory = str(args.get("directory") or ".")
        pattern = str(args.get("pattern") or "*")
        base = self._safe_resolve(directory)
        if not base.is_dir():
            raise ValueError(f"not a directory: {directory}")
        entries: list[str] = []
        for entry in sorted(base.glob(pattern)):
            if not entry.resolve().is_relative_to(self.workspace_root):
                continue
            if self._is_sensitive_path(entry.resolve()):
                continue
            if any(skip in entry.parts for skip in (".git", "__pycache__", ".venv", "node_modules")):
                continue
            rel = str(entry.relative_to(self.workspace_root))
            entries.append(rel + ("/" if entry.is_dir() else ""))
            if len(entries) >= MAX_LIST_ENTRIES:
                break
        return {"directory": directory, "count": len(entries), "entries": entries}

    def _tool_read_file(self, args: dict[str, Any]) -> dict[str, Any]:
        rel_path = str(args.get("path") or "")
        start_line = max(1, int(args.get("start_line") or 1))
        max_lines = max(1, min(120, int(args.get("max_lines") or 60)))
        target = self._safe_resolve(rel_path)
        if not target.is_file():
            raise ValueError(f"file not found: {rel_path}")
        raw = target.read_bytes()
        if len(raw) > 512_000:
            raw = raw[:512_000]
        lines = raw.decode("utf-8", errors="replace").splitlines()
        sliced = lines[start_line - 1 : start_line - 1 + max_lines]
        numbered = "\n".join(f"{start_line + idx}: {line}" for idx, line in enumerate(sliced))
        if len(numbered.encode("utf-8")) > MAX_READ_BYTES:
            numbered = numbered[:MAX_READ_BYTES] + "\n... (truncated)"
        return {
            "path": str(target.relative_to(self.workspace_root)),
            "total_lines": len(lines),
            "start_line": start_line,
            "lines_returned": len(sliced),
            "content": numbered,
        }

    def _tool_search_text(self, args: dict[str, Any]) -> dict[str, Any]:
        query = str(args.get("query") or "").strip()
        if not query or len(query) > 120:
            raise ValueError("query must be 1..120 characters")
        directory = str(args.get("directory") or ".")
        max_results = max(1, min(MAX_SEARCH_RESULTS, int(args.get("max_results") or 12)))
        base = self._safe_resolve(directory)
        if not base.is_dir():
            raise ValueError(f"not a directory: {directory}")
        needle = query.lower()
        matches: list[dict[str, Any]] = []
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if any(skip in path.parts for skip in (".git", "__pycache__", ".venv", "node_modules", "research")):
                continue
            if path.suffix.lower() not in {".py", ".md", ".json", ".toml", ".txt", ".html"}:
                continue
            resolved = path.resolve()
            if not resolved.is_relative_to(self.workspace_root) or self._is_sensitive_path(resolved):
                continue
            if resolved.stat().st_size > 256_000:
                continue
            try:
                text = resolved.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                if needle in line.lower():
                    matches.append({
                        "file": str(resolved.relative_to(self.workspace_root)),
                        "line": lineno,
                        "snippet": line.strip()[:160],
                    })
                    if len(matches) >= max_results:
                        return {"query": query, "count": len(matches), "matches": matches}
        return {"query": query, "count": len(matches), "matches": matches}

    def _tool_calculate(self, args: dict[str, Any]) -> dict[str, Any]:
        expr = str(args.get("expression") or "").strip()
        val = _safe_eval_math(expr)
        return {"expression": expr, "result": val}

    def _tool_recall_memory(self, agent_id: str, args: dict[str, Any]) -> dict[str, Any]:
        query = str(args.get("query") or "")
        facts = self.memory.recall_facts(
            owner_id=self.owner_id,
            agent_id=agent_id,
            requester_owner_id=self.owner_id,
            query=query,
        )
        return {"agent_id": agent_id, "query": query, "count": len(facts), "facts": facts}

    def _tool_save_memory(self, agent_id: str, args: dict[str, Any]) -> dict[str, Any]:
        key = str(args.get("key") or "note")
        content = str(args.get("content") or "")
        raw_prov = str(args.get("provenance") or "inferred").lower()
        prov = Provenance.OBSERVED_RECORDED if raw_prov == "observed_recorded" else Provenance.INFERRED
        ev = self.memory.append_ledger(
            event_id=f"ledger-mem-{agent_id}-{secrets.token_hex(6)}",
            owner_id=self.owner_id,
            agent_id=agent_id,
            event_type="memory_save",
            provenance=prov,
            payload={"key": key, "content": content},
        )
        saved = self.memory.save_fact(
            owner_id=self.owner_id,
            agent_id=agent_id,
            fact_key=key,
            content=content,
            provenance=prov,
            source_event_id=ev["event_id"],
            requester_owner_id=self.owner_id,
        )
        return {"saved": saved, "ledger_digest": ev["digest"]}
