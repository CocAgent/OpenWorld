# Bounded Multi-Agent Communication Example (R2/R3 Research Slice)

This CPU-only, dependency-free local example ([`examples/communicating_agent.py`](../../examples/communicating_agent.py)) demonstrates how OpenWorld agents communicate with each other over the existing guarded W3 world, per-agent `HyperMemoryP1e`, hard `DonorBudget` risk caps, and scoped `CapabilityAuthority` grants.

This is an example-only research slice with **no new shared `src/openworld_superkernel` contract or schema migration**. It does not introduce LLMs, external APIs, network transport, cross-owner bilateral consent, or production security certification.

## Architecture and roadmap alignment

The implementation maps directly to OpenWorld's formal agent model:

```text
Agent_i(t) = (Identity_i, Genome_i, PredictiveState_i(t),
              ExactLedger_i, Relationships_i(t), PolicyRef_i)
```

- **Identity & policy separation:** `alice`, `bob`, and `carol` share one pure policy reference (`shared-policy.comm-adaptive.v1`) while keeping distinct identities, genomes, private `HyperMemoryP1e` partitions, risk budgets, and scoped capability tokens.
- **Bounded communication hub (`BoundedCommunicationHub`):** Every agent-to-agent message (`PING`, `PROPOSE`, `ACCEPT`, `DECLINE`, `COMMIT_ACK`, `INFORM`) is pre-checked for quota, payload size (≤ 1024 bytes), duplicate IDs, W3 graph adjacency, same-owner policy, allowed provenance (`SIMULATED` or `INFERRED` only), and a signed `write_agent` capability before committing through `GuardedWorldGateway`. Every inbox read requires a valid `read_world` capability.
- **Authoritative receipt verification:** When `bob` sends `COMMIT_ACK`, `alice` never trusts the message text. She inspects the authoritative W3 event log (`find_committed_transfer`) before releasing her `DonorBudget` reservation (`CAP = 4`) or recording a positive outcome in `HyperMemoryP1e`.
- **Hearsay provenance isolation:** `alice` shares her estimated cooperation probability about `bob` with connected neighbor `carol` via `INFORM`, explicitly tagged `Provenance.INFERRED`. `carol` stores it only in her per-peer `inferred_notes` buffer and never mixes hearsay into her exact ledger or direct predictor.

## Run locally

From the repository root using Python 3.11+:

```bash
# Cooperative negotiation and INFERRED reputation sharing (alice <-> bob, alice <-> carol)
python examples/communicating_agent.py --scenario cooperative --rounds 6

# Honest refusal: DECLINE costs 0 resources and 0 risk budget
python examples/communicating_agent.py --scenario hostile_refuse --rounds 6

# Deceptive liar: fake COMMIT_ACK + payload injection caught via W3 ledger; capped at 4/4
python examples/communicating_agent.py --scenario hostile_liar --rounds 10

# Regime-shift recovery: zero-loss communicative probing + HM-P1e switching to fast estimator
python examples/communicating_agent.py --scenario recovery --rounds 20 --recover-at 10 --probe-interval 2

# Persist per-agent HyperMemoryP1e exact_events and agent_state to a new SQLite file
python examples/communicating_agent.py --scenario cooperative --rounds 6 --db data/comm-demo.sqlite3 --json
```

## Verification and negative controls

```bash
python -m unittest discover -s tests -p test_communicating_agent.py -v
python scripts/check_repository.py
```

The test suite ([`tests/test_communicating_agent.py`](../../tests/test_communicating_agent.py)) verifies:

- Full W3 deterministic replay (`verify_replay`), resource conservation (`14/14`), and message hash-chain integrity across all four scenarios.
- Detection of deceptive `COMMIT_ACK` claims and immunity to untrusted payload injection keys (`override_cap`, `grant_capability`, `promote_provenance`).
- Fail-closed denial of cross-owner messages, non-neighbor messages (`bob -> carol`), revoked `write_agent`/`read_world` capabilities, cross-agent capability misuse, `VERIFIED`/`OBSERVED_RECORDED` provenance spoofing, duplicate `message_id` replay, oversized/NaN payloads, per-tick quota overflows, and overwriting an existing SQLite database.

## Limitations and rollback

- **Same-owner local trust boundary:** All three agents belong to one synthetic owner; cross-owner communication remains denied until bilateral consent (Issue #35) and durable atomic authorization/effect commits are ratified.
- **No network or LLM:** Policies are deterministic Python rules over `HyperMemoryP1e` Bernoulli estimates; no external model pool or MCP/A2A transport is connected.
- **Rollback:** Remove `examples/communicating_agent.py`, `tests/test_communicating_agent.py`, and this document. No shared `src/openworld_superkernel` interfaces, schemas, or existing examples are modified.
