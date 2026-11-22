# OpenWorld Companion & Multi-Agent Runtime (R2/R3 Implementation)

This local research runtime upgrades OpenWorld from a fixed two-agent transfer simulation into a **real tool-using, persistent-memory, multi-agent runtime** aligned with OpenWorld's R2 (*Trustworthy Personal Agent*) and R3 (*Social Agents & Interoperability*) roadmap.

It runs on Python 3.11+ standard library + SQLite with **zero required external packages**, and supports plugging in real LLMs at runtime without committing secrets or forcing paid APIs.

## Architecture

- **Shared Model Pool ([`examples/companion_agent/model_router.py`](../../examples/companion_agent/model_router.py)):** Multi-provider router supporting:
  - `ollama`: free local LLMs via `/api/chat` with native tool calling.
  - `openai`: any OpenAI-compatible Chat Completions API (OpenAI, OpenRouter, DeepSeek, Groq, vLLM, LM Studio).
  - `gemini`: Google Gemini `generateContent` REST API with function calling.
  - `offline`: zero-key deterministic ReAct planner for offline execution and reproducible testing.
- **Persistent SQLite Memory & Hash-Chained Ledger ([`examples/companion_agent/memory_store.py`](../../examples/companion_agent/memory_store.py)):**
  - `exact_ledger`: append-only SHA-256 hash-chained log recording real user prompts, real tool outputs, and human consent decisions as `OBSERVED_RECORDED`, and LLM outputs as `INFERRED`.
  - `knowledge_facts`: per-agent persistent searchable memory returning value + provenance + `source_event_id`.
  - Integrates `HyperMemoryP1e` to track empirical tool/delegation reliability per agent.
- **Capability-Gated Sandboxed Tool Gateway ([`examples/companion_agent/tool_gateway.py`](../../examples/companion_agent/tool_gateway.py)):**
  - Every tool call is authorized via OpenWorld's `CapabilityAuthority` HMAC tokens.
  - Enforces strict workspace containment (blocking `..` traversal, absolute paths, `.git`, `.env`, and secret filenames).
  - Safe AST arithmetic evaluator (`calculate`, never `eval()`).
  - Consequential writes (`write_note` inside `data/agent_notes/`) always pause for explicit human approval bound to a SHA-256 `intent_digest`.
- **Two Independent Persistent Agents ([`examples/companion_agent/runtime.py`](../../examples/companion_agent/runtime.py)):**
  - **`nova` (`companion_planner`):** plans and executes user goals, manages persistent memory, stages file writes for human consent, and delegates verification tasks.
  - **`atlas` (`readonly_verifier`):** shares the same `model_ref` while holding an isolated memory partition and **read-only** capabilities only (`list_files`, `read_file`, `search_text`, `calculate`, `recall_memory`).

## Run locally

### 1. Live Web Studio (HTML + Python backend on `127.0.0.1:8780`)

```bash
python examples/openworld_agent_server.py --port 8780 --db data/openworld-companion.sqlite3
```

### 2. Interactive CLI or One-Shot Task

```bash
# Zero-key offline ReAct agent with persistent SQLite memory
python examples/openworld_agent.py --db data/openworld-companion.sqlite3 --ask "Read docs/ARCHITECTURE.md and ask Atlas to verify"
python examples/openworld_agent.py --db data/openworld-companion.sqlite3 --chat

# Connect a free local Ollama model
python examples/openworld_agent.py --provider ollama --model qwen2.5:7b --chat

# Connect any OpenAI-compatible API (key stays in environment / RAM only)
OPENAI_API_KEY=... python examples/openworld_agent.py --provider openai --model gpt-4o-mini --chat

# Connect Google Gemini API
GEMINI_API_KEY=... python examples/openworld_agent.py --provider gemini --model gemini-2.5-flash --chat
```

## Verification

```bash
python -m unittest tests/test_companion_agent.py -v
python scripts/check_repository.py
```

## Boundaries, limitations, and rollback

- **Same-owner local trust boundary:** Binds strictly to `127.0.0.1` / `localhost`. Never expose directly to untrusted networks.
- **No secret persistence:** API keys provided via env vars or the Studio UI remain in process memory only and are excluded from SQLite, logs, and API responses.
- **Provenance discipline:** Model outputs are labeled `INFERRED`; tool outputs are labeled `OBSERVED_RECORDED` and treated as untrusted data. Neither is promoted to `VERIFIED`.
- **Rollback:** Remove `examples/companion_agent/`, `examples/openworld_agent.py`, `examples/openworld_agent_server.py`, `examples/web/companion_ui.html`, `tests/test_companion_agent.py`, and this document. No shared `src/openworld_superkernel/` public interfaces are altered.
