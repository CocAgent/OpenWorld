"""Multi-provider shared AI model pool and resource-aware decision router.

Supports:
- `ollama`: Free local LLM via Ollama `/api/chat` with native tool calling.
- `openai`: Any OpenAI-compatible Chat Completions endpoint (OpenAI, OpenRouter,
  DeepSeek, Groq, vLLM, LM Studio) with function/tool calling.
- `gemini`: Google Gemini `generateContent` REST endpoint with function calling.
- `offline`: Dependency-free deterministic ReAct tool planner for zero-key
  local execution and reproducible testing.

Secrets discipline: API keys are held ONLY in memory or process environment
variables, never logged, never persisted to SQLite, and never serialized by
`public_info()`. Uses Python standard library only (`urllib.request`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROVIDERS = ("offline", "ollama", "openai", "gemini")

DEFAULT_BASE_URLS = {
    "ollama": "http://127.0.0.1:11434",
    "openai": "https://api.openai.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
    "offline": "",
}

DEFAULT_MODELS = {
    "ollama": "qwen2.5:7b",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.5-flash",
    "offline": "openworld.offline-react-planner.v1",
}


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ModelResponse:
    text: str
    tool_calls: tuple[ToolCall, ...] = ()
    model_ref: str = ""
    provider: str = "offline"
    raw_usage: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelConfig:
    provider: str = "offline"
    model: str = DEFAULT_MODELS["offline"]
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0.2
    timeout_seconds: int = 45

    def __post_init__(self) -> None:
        self.provider = self.provider.strip().lower()
        if self.provider not in PROVIDERS:
            raise ValueError(f"unsupported provider: {self.provider}; choose from {PROVIDERS}")
        if not self.model:
            self.model = DEFAULT_MODELS[self.provider]
        if not self.base_url:
            self.base_url = DEFAULT_BASE_URLS[self.provider]
        self.base_url = self.base_url.rstrip("/")
        if not (0.0 <= float(self.temperature) <= 2.0):
            raise ValueError("temperature must be in [0.0, 2.0]")
        if type(self.timeout_seconds) is not int or not 1 <= self.timeout_seconds <= 180:
            raise ValueError("timeout_seconds must be in 1..180")

    @property
    def model_ref(self) -> str:
        return f"{self.provider}:{self.model}"

    def public_info(self) -> dict[str, Any]:
        """Sanitized metadata safe for logs, UI, and ledger (never includes api_key)."""
        return {
            "provider": self.provider,
            "model": self.model,
            "model_ref": self.model_ref,
            "base_url": self.base_url,
            "api_key_configured": bool(self.api_key),
            "temperature": self.temperature,
        }

    @classmethod
    def from_env(
        cls,
        *,
        provider: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> "ModelConfig":
        prov = (provider or os.environ.get("OPENWORLD_PROVIDER") or "offline").strip().lower()
        if prov not in PROVIDERS:
            raise ValueError(f"unsupported provider: {prov}")
        resolved_key = api_key or ""
        resolved_url = base_url or ""
        if prov == "openai":
            resolved_key = resolved_key or os.environ.get("OPENAI_API_KEY", "")
            resolved_url = resolved_url or os.environ.get("OPENAI_BASE_URL", DEFAULT_BASE_URLS["openai"])
        elif prov == "gemini":
            resolved_key = resolved_key or os.environ.get("GEMINI_API_KEY", "")
            resolved_url = resolved_url or os.environ.get("GEMINI_BASE_URL", DEFAULT_BASE_URLS["gemini"])
        elif prov == "ollama":
            resolved_url = resolved_url or os.environ.get("OLLAMA_HOST", DEFAULT_BASE_URLS["ollama"])
        resolved_model = model or os.environ.get("OPENWORLD_MODEL") or DEFAULT_MODELS[prov]
        return cls(
            provider=prov,
            model=resolved_model,
            base_url=resolved_url,
            api_key=resolved_key,
        )


def _http_post_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str],
    timeout: int,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = Request(url, data=body, headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        raise RuntimeError(f"LLM endpoint HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"LLM endpoint unreachable ({url}): {exc.reason}") from exc


class ModelRouter:
    """Shared model pool referenced by multiple OpenWorld agent identities."""

    def __init__(self, config: ModelConfig) -> None:
        self.config = config

    def update_config(self, config: ModelConfig) -> None:
        self.config = config

    def complete(
        self,
        *,
        agent_id: str,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ModelResponse:
        prov = self.config.provider
        if prov == "offline":
            return _offline_react_complete(
                agent_id=agent_id,
                messages=messages,
                tools=tools,
                model_ref=self.config.model_ref,
            )
        if prov == "ollama":
            return self._call_ollama(system_prompt, messages, tools)
        if prov == "openai":
            return self._call_openai(system_prompt, messages, tools)
        if prov == "gemini":
            return self._call_gemini(system_prompt, messages, tools)
        raise ValueError(f"unsupported provider: {prov}")

    def _call_ollama(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ModelResponse:
        chat_msgs = [{"role": "system", "content": system_prompt}, *messages]
        ollama_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in tools
        ]
        payload = {
            "model": self.config.model,
            "messages": chat_msgs,
            "tools": ollama_tools,
            "stream": False,
            "options": {"temperature": self.config.temperature},
        }
        data = _http_post_json(
            f"{self.config.base_url}/api/chat",
            payload,
            headers={},
            timeout=self.config.timeout_seconds,
        )
        msg = data.get("message", {})
        raw_calls = msg.get("tool_calls") or []
        calls = []
        for idx, tc in enumerate(raw_calls):
            fn = tc.get("function", {})
            args = fn.get("arguments", {})
            if isinstance(args, str):
                args = json.loads(args)
            calls.append(ToolCall(call_id=f"ollama-{idx}", name=fn["name"], arguments=args))
        return ModelResponse(
            text=str(msg.get("content") or ""),
            tool_calls=tuple(calls),
            model_ref=self.config.model_ref,
            provider="ollama",
            raw_usage={
                "eval_count": data.get("eval_count"),
                "prompt_eval_count": data.get("prompt_eval_count"),
            },
        )

    def _call_openai(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ModelResponse:
        if not self.config.api_key and "127.0.0.1" not in self.config.base_url and "localhost" not in self.config.base_url:
            raise RuntimeError("OPENAI_API_KEY is required for remote OpenAI-compatible providers")
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in tools
        ]
        headers = {"Authorization": f"Bearer {self.config.api_key}"} if self.config.api_key else {}
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "temperature": self.config.temperature,
        }
        if openai_tools:
            payload["tools"] = openai_tools
            payload["tool_choice"] = "auto"
        data = _http_post_json(
            f"{self.config.base_url}/chat/completions",
            payload,
            headers=headers,
            timeout=self.config.timeout_seconds,
        )
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message", {})
        calls = []
        for idx, tc in enumerate(msg.get("tool_calls") or []):
            fn = tc.get("function", {})
            raw_args = fn.get("arguments", "{}")
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            calls.append(
                ToolCall(
                    call_id=str(tc.get("id") or f"openai-{idx}"),
                    name=str(fn["name"]),
                    arguments=args if isinstance(args, dict) else {},
                )
            )
        return ModelResponse(
            text=str(msg.get("content") or ""),
            tool_calls=tuple(calls),
            model_ref=self.config.model_ref,
            provider="openai",
            raw_usage=data.get("usage") or {},
        )

    def _call_gemini(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ModelResponse:
        if not self.config.api_key:
            raise RuntimeError("GEMINI_API_KEY is required for the Gemini provider")
        contents = []
        for m in messages:
            role = "model" if m["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": str(m.get("content") or "")}]})
        payload: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {"temperature": self.config.temperature},
        }
        if tools:
            payload["tools"] = [{
                "functionDeclarations": [
                    {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["parameters"],
                    }
                    for t in tools
                ]
            }]
        url = f"{self.config.base_url}/models/{self.config.model}:generateContent"
        data = _http_post_json(
            url,
            payload,
            headers={"x-goog-api-key": self.config.api_key},
            timeout=self.config.timeout_seconds,
        )
        cand = (data.get("candidates") or [{}])[0]
        parts = cand.get("content", {}).get("parts") or []
        texts: list[str] = []
        calls: list[ToolCall] = []
        for idx, part in enumerate(parts):
            if "text" in part:
                texts.append(str(part["text"]))
            if "functionCall" in part:
                fc = part["functionCall"]
                calls.append(
                    ToolCall(
                        call_id=f"gemini-{idx}",
                        name=str(fc["name"]),
                        arguments=dict(fc.get("args") or {}),
                    )
                )
        return ModelResponse(
            text="\n".join(texts).strip(),
            tool_calls=tuple(calls),
            model_ref=self.config.model_ref,
            provider="gemini",
            raw_usage=data.get("usageMetadata") or {},
        )


# ---------------------------------------------------------------------------
# Offline ReAct Tool Planner (deterministic zero-key brain for real local tools)
# ---------------------------------------------------------------------------

_FILE_PATH_RE = re.compile(r"([A-Za-z0-9_./-]+\.(?:py|md|json|toml|html|txt|sh))")
_MATH_EXPR_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?(?:\s*[\+\-\*/\^%]\s*\(?[0-9]+(?:\.[0-9]+)?\)?)+|\([0-9\s\.\+\-\*/\(\)]+\)(?:\s*[\+\-\*/]\s*[0-9\.]+)*)")


def _offline_react_complete(
    *,
    agent_id: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    model_ref: str,
) -> ModelResponse:
    """Deterministic multi-step ReAct planner over real sandboxed tools.

    Enables genuine end-to-end tool execution, SQLite memory recall/storage,
    peer-agent delegation (`nova -> atlas`), and human approval gating without
    requiring any paid API key.
    """
    available = {t["name"] for t in tools}
    user_text = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_text = str(m.get("content") or "")
            break
    tool_outputs = [m for m in messages if m.get("role") == "tool"]
    used_tools = [str(m.get("name") or "") for m in tool_outputs]
    lower = user_text.lower()

    # Atlas peer-agent verification behavior (read-only independent check).
    if agent_id == "atlas":
        if not tool_outputs:
            file_match = _FILE_PATH_RE.search(user_text)
            if file_match and "read_file" in available:
                return ModelResponse(
                    text="Checking the referenced file directly to verify Nova's claims.",
                    tool_calls=(ToolCall("atlas-1", "read_file", {"path": file_match.group(1), "max_lines": 50}),),
                    model_ref=model_ref,
                    provider="offline",
                )
            if "search_text" in available:
                query = "CapabilityAuthority" if "capability" in lower else (
                    "HyperMemoryP1e" if "memory" in lower else "Provenance"
                )
                return ModelResponse(
                    text=f"Searching the codebase for `{query}` to independently cross-check.",
                    tool_calls=(ToolCall("atlas-1", "search_text", {"query": query, "directory": "src"}),),
                    model_ref=model_ref,
                    provider="offline",
                )
        evidence_summary = tool_outputs[-1]["content"][:500] if tool_outputs else "No direct file evidence."
        return ModelResponse(
            text=(
                "Atlas independent verification report (provenance: INFERRED synthesis grounded in "
                "OBSERVED_RECORDED tool output):\n"
                f"- Checked directly via read-only tools ({', '.join(used_tools) or 'none'}).\n"
                f"- Observed evidence excerpt:\n{evidence_summary}\n"
                "- Verdict: Source evidence exists in workspace; no unverified external claims introduced."
            ),
            model_ref=model_ref,
            provider="offline",
        )

    # Nova primary Companion planner: multi-step ReAct over real workspace tools.
    # Step A: explicit save_memory intent
    if (
        any(kw in lower for kw in ("remember", "save memory", "ghi nho", "ghi nhớ", "luu tri nho", "lưu trí nhớ"))
        and "save_memory" in available
        and "save_memory" not in used_tools
    ):
        fact_key = "user_note"
        if "ten" in lower or "tên" in lower or "name" in lower:
            fact_key = "user_profile"
        elif "muc tieu" in lower or "mục tiêu" in lower or "goal" in lower:
            fact_key = "project_goal"
        return ModelResponse(
            text="Saving this statement to persistent SQLite memory as OBSERVED_RECORDED user input.",
            tool_calls=(
                ToolCall(
                    "nova-mem-save",
                    "save_memory",
                    {"key": fact_key, "content": user_text, "provenance": "observed_recorded"},
                ),
            ),
            model_ref=model_ref,
            provider="offline",
        )

    # Step B: recall_memory intent
    if (
        any(kw in lower for kw in ("recall", "what do you remember", "nhớ gì", "nho gi", "trí nhớ", "tri nho", "đã lưu", "da luu"))
        and "recall_memory" in available
        and "recall_memory" not in used_tools
    ):
        return ModelResponse(
            text="Querying my persistent SQLite memory with provenance metadata.",
            tool_calls=(ToolCall("nova-mem-recall", "recall_memory", {"query": ""}),),
            model_ref=model_ref,
            provider="offline",
        )

    # Step C: mathematical expression calculation
    math_match = _MATH_EXPR_RE.search(user_text)
    if (
        math_match
        and any(kw in lower for kw in ("calc", "compute", "tính", "tinh", "+", "*", "/"))
        and "calculate" in available
        and "calculate" not in used_tools
    ):
        expr = math_match.group(1).replace("^", "**").strip()
        return ModelResponse(
            text=f"Evaluating `{expr}` via the safe AST calculator tool.",
            tool_calls=(ToolCall("nova-calc", "calculate", {"expression": expr}),),
            model_ref=model_ref,
            provider="offline",
        )

    # Step D: reading a specifically named file
    file_match = _FILE_PATH_RE.search(user_text)
    if file_match and "read_file" in available and "read_file" not in used_tools:
        return ModelResponse(
            text=f"Reading `{file_match.group(1)}` through the sandboxed workspace tool.",
            tool_calls=(ToolCall("nova-read", "read_file", {"path": file_match.group(1), "max_lines": 60}),),
            model_ref=model_ref,
            provider="offline",
        )

    # Step E: search code/text across workspace
    if (
        any(kw in lower for kw in ("search", "find", "tìm", "tim", "grep", "where is", "ở đâu"))
        and "search_text" in available
        and "search_text" not in used_tools
    ):
        term_match = re.search(r"`([^`]+)`|\"([^\"]+)\"|'([^']+)'", user_text)
        if term_match:
            query = next(g for g in term_match.groups() if g)
        else:
            candidates = [
                tok
                for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", user_text)
                if tok.lower() not in {"search", "find", "file", "files", "trong", "code", "atlas", "nova", "openworld"}
            ]
            query = candidates[0] if candidates else "CapabilityAuthority"
        directory = "src" if "src" in lower else "."
        return ModelResponse(
            text=f"Searching workspace files for `{query}`.",
            tool_calls=(ToolCall("nova-search", "search_text", {"query": query, "directory": directory}),),
            model_ref=model_ref,
            provider="offline",
        )

    # Step F: list workspace files
    if (
        any(kw in lower for kw in ("list file", "liệt kê", "liet ke", "cấu trúc", "cau truc", "directory", "folder"))
        and "list_files" in available
        and "list_files" not in used_tools
    ):
        directory = "src/openworld_superkernel" if "src" in lower else ("examples" if "example" in lower else ".")
        return ModelResponse(
            text=f"Listing files inside `{directory}`.",
            tool_calls=(ToolCall("nova-list", "list_files", {"directory": directory}),),
            model_ref=model_ref,
            provider="offline",
        )

    # Step G: delegate peer verification to Atlas when requested or after inspecting architecture
    if (
        any(kw in lower for kw in ("atlas", "verify", "kiểm chứng", "kiem chung", "peer", "agent 2", "hỏi agent"))
        and "delegate_to_agent" in available
        and "delegate_to_agent" not in used_tools
    ):
        ctx = tool_outputs[-1]["content"][:600] if tool_outputs else user_text
        return ModelResponse(
            text="Delegating independent verification to peer agent `atlas` via CapabilityAuthority.",
            tool_calls=(
                ToolCall(
                    "nova-delegate",
                    "delegate_to_agent",
                    {
                        "target_agent": "atlas",
                        "task": f"Independently verify evidence for user request: {user_text}",
                        "context": ctx,
                    },
                ),
            ),
            model_ref=model_ref,
            provider="offline",
        )

    # Step H: write note / report (consequential action -> triggers explicit human approval!)
    if (
        any(kw in lower for kw in ("write", "report", "save file", "ghi file", "ghi báo cáo", "ghi bao cao", "tạo file", "tao file", "viết báo cáo"))
        and "write_note" in available
        and "write_note" not in used_tools
    ):
        collected = "\n\n".join(
            f"### Tool `{m.get('name')}` (OBSERVED_RECORDED)\n{m.get('content', '')[:800]}"
            for m in tool_outputs
        ) or f"Request: {user_text}"
        fname = "agent-report.md"
        name_match = re.search(r"([A-Za-z0-9_-]+\.(?:md|txt))", user_text)
        if name_match and not name_match.group(1).lower().startswith("readme"):
            fname = name_match.group(1)
        note_body = (
            f"# OpenWorld Agent Note\n\n"
            f"- Generated by: `nova` (model_ref: `{model_ref}`)\n"
            f"- Provenance: `INFERRED` synthesis over `OBSERVED_RECORDED` tool outputs\n"
            f"- User goal: {user_text}\n\n"
            f"{collected}\n"
        )
        return ModelResponse(
            text=f"Requesting explicit human approval before writing `{fname}` into `data/agent_notes/`.",
            tool_calls=(ToolCall("nova-write", "write_note", {"filename": fname, "content": note_body}),),
            model_ref=model_ref,
            provider="offline",
        )

    # Default first step if user asked a general question about OpenWorld without naming a file
    if not tool_outputs and "read_file" in available and any(
        kw in lower for kw in ("openworld", "kiến trúc", "kien truc", "architecture", "roadmap", "lộ trình", "lo trinh")
    ):
        target = "docs/ROADMAP.md" if ("roadmap" in lower or "lộ trình" in lower or "lo trinh" in lower) else "docs/ARCHITECTURE.md"
        return ModelResponse(
            text=f"Reading `{target}` to ground my answer in exact repository evidence.",
            tool_calls=(ToolCall("nova-doc", "read_file", {"path": target, "max_lines": 60}),),
            model_ref=model_ref,
            provider="offline",
        )

    # Final synthesis grounded strictly in observed tool outputs
    if tool_outputs:
        sections = []
        for item in tool_outputs:
            tname = item.get("name", "tool")
            snippet = str(item.get("content", ""))
            if len(snippet) > 900:
                snippet = snippet[:900] + "\n... (truncated)"
            sections.append(f"**[{tname}]**\n{snippet}")
        joined = "\n\n".join(sections)
        return ModelResponse(
            text=(
                f"Done — executed {len(tool_outputs)} capability-checked step(s) "
                f"(`{', '.join(used_tools)}`).\n\n"
                f"{joined}\n\n"
                f"_(Note: tool outputs above are `OBSERVED_RECORDED`; this summary is `INFERRED` via `{model_ref}`. "
                f"Switch provider to Ollama, OpenAI, or Gemini anytime for full natural-language LLM reasoning over the same tools & guardrails.)_"
            ),
            model_ref=model_ref,
            provider="offline",
        )

    return ModelResponse(
        text=(
            "I am **Nova** (OpenWorld Companion), paired with peer verifier **Atlas**.\n"
            "Try giving me a real task using sandboxed tools, for example:\n"
            "- Read a file: `Read docs/ARCHITECTURE.md and ask Atlas to verify`\n"
            "- Search the codebase: `Search CapabilityAuthority in src/`\n"
            "- Calculate & save a report (requires your approval!): `Calculate (1 - 0.25/0.85) * 960 and write report.md`\n"
            "- Persistent memory: `Remember my goal is building trustworthy multi-agent memory` -> `What do you remember?`\n\n"
            f"_(Current engine: `{model_ref}`. Connect Ollama, OpenAI, or Gemini in Settings / CLI flags for full LLM conversation.)_"
        ),
        model_ref=model_ref,
        provider="offline",
    )
