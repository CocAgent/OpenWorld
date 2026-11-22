"""Interactive CLI for the real OpenWorld Companion + Multi-Agent Runtime.

Examples:
  # Zero-key offline ReAct tool agent with persistent SQLite memory:
  python examples/openworld_agent.py --db data/companion.sqlite3 --ask "Read docs/ARCHITECTURE.md and ask Atlas to verify"

  # Interactive chat REPL (with human approval prompts for file writes):
  python examples/openworld_agent.py --db data/companion.sqlite3 --chat

  # Free local LLM via Ollama:
  python examples/openworld_agent.py --provider ollama --model qwen2.5:7b --chat

  # Any OpenAI-compatible API (OpenAI, OpenRouter, DeepSeek, Groq, LM Studio):
  OPENAI_API_KEY=... python examples/openworld_agent.py --provider openai --model gpt-4o-mini --chat

  # Google Gemini API:
  GEMINI_API_KEY=... python examples/openworld_agent.py --provider gemini --model gemini-2.5-flash --chat
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples"))

from companion_agent.model_router import ModelConfig, PROVIDERS
from companion_agent.runtime import OpenWorldAgentRuntime


def _print_turn(result: dict) -> None:
    print("\n--- ReAct & Delegation Trace ---")
    for step in result["trace"]:
        kind = step["kind"]
        agent = step["agent_id"]
        prov = step.get("provenance", "")
        if kind == "thought":
            print(f"  [{agent}] thought ({prov}): {step['content']}")
        elif kind == "tool_call":
            print(f"  [{agent}] call `{step['tool']}` args={json.dumps(step['arguments'], ensure_ascii=False)}")
        elif kind == "tool_result":
            preview = step["output_preview"].replace("\n", " ")[:180]
            print(f"  [{agent}] result `{step['tool']}` ({prov}): {preview}")
        elif kind == "tool_denied":
            print(f"  [{agent}] DENIED `{step['tool']}`: {step['error']}")
        elif kind == "delegation_request":
            print(f"  [{agent} -> {step['target']}] DELEGATE: {step['task']}")
        elif kind == "delegation_reply":
            print(f"  [{agent} -> nova] VERIFICATION ({prov}): {step['content'][:220]}")
        elif kind == "approval_required":
            apr = step["approval"]
            print(f"  [CONSENT REQUIRED] id={apr['approval_id']} tool={apr['tool_name']} file={apr['arguments']['filename']}")
    print("\n=== Nova Response (INFERRED) ===")
    print(result["answer"])
    st = result["state"]
    print(
        f"\n[model={result['model']['model_ref']} | ledger={st['ledger_count']} "
        f"chain={'PASS' if st['ledger_chain_verified'] else 'FAIL'} | {result['latency_ms']}ms]"
    )


def _handle_approvals(runtime: OpenWorldAgentRuntime, pending: list[dict], *, auto_deny: bool = False) -> None:
    for apr in pending:
        print(f"\nHuman approval required for `{apr['tool_name']}` -> data/agent_notes/{apr['arguments']['filename']}")
        print(f"Intent SHA-256: {apr['intent_digest']}")
        if auto_deny:
            res = runtime.approve_action(apr["approval_id"], approved=False)
            print(f"Auto-denied: {res['approval']['status']}")
            continue
        ans = input("Approve write to disk? [y/N]: ").strip().lower()
        res = runtime.approve_action(apr["approval_id"], approved=(ans in ("y", "yes")))
        if res["executed"]:
            print(f"APPROVED & WRITTEN: {res['written_path']} ({res['bytes_written']} bytes, ledger={res['ledger_digest'][:12]}...)")
        else:
            print(f"DENIED: 0 files written (ledger={res['ledger_digest'][:12]}...)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=PROVIDERS, default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--db", default="data/openworld-companion.sqlite3")
    parser.add_argument("--ask", help="Run a single goal/prompt and exit")
    parser.add_argument("--chat", action="store_true", help="Start interactive chat loop")
    parser.add_argument("--status", action="store_true", help="Print persistent memory & ledger status")
    parser.add_argument("--json", action="store_true", help="Emit JSON output for --ask or --status")
    args = parser.parse_args()

    config = ModelConfig.from_env(
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
    )
    with OpenWorldAgentRuntime(workspace_root=ROOT, db_path=args.db, model_config=config) as runtime:
        if args.status:
            print(json.dumps(runtime.status(), indent=2, ensure_ascii=False))
            return
        if args.ask:
            result = runtime.run_turn(args.ask)
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return
            _print_turn(result)
            if result["pending_approvals"]:
                _handle_approvals(runtime, result["pending_approvals"], auto_deny=not sys.stdin.isatty())
            return

        print(f"OpenWorld Companion CLI | model={config.model_ref} | db={args.db}")
        print("Type your goal/question, '/status', or '/quit' to exit.")
        while True:
            try:
                line = input("\nYou> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye.")
                break
            if not line or line in ("/quit", "/exit"):
                break
            if line == "/status":
                st = runtime.status()
                print(
                    f"Agents: {[a['agent_id'] for a in st['agents']]} | "
                    f"Ledger: {st['ledger_count']} (chain={st['ledger_chain_verified']}) | "
                    f"Saved facts: {len(st['facts'])}"
                )
                continue
            try:
                result = runtime.run_turn(line)
            except Exception as exc:
                print(f"Error: {exc}")
                continue
            _print_turn(result)
            if result["pending_approvals"]:
                _handle_approvals(runtime, result["pending_approvals"])


if __name__ == "__main__":
    main()
