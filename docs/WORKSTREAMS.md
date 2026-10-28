# Parallel workstreams

Start as a single monorepo. Each workstream owns a bounded scope and topic branch. Shared contracts require an architecture review.

| Track | Prefix | Ownership | First deliverable |
|---|---|---|---|
| W0 Architecture | `docs/` | RFCs, interface decisions, governance | Ratify memory and agent invariants |
| W1 HyperMemory | `feat/memory-` | Exact ledger, HM-P1e, compaction and replay | Fair resource-aware benchmark |
| W2 MathKernel | `feat/math-` | Process kernels, predictive sufficiency, online learning | Formal models and failure conditions |
| W3 World Runtime | `feat/world-` | Deterministic simulation and sparse event routing | Replayable multi-agent fixture |
| W4 Protocols | `feat/protocol-` | Capabilities and MCP/A2A adapters | Deny-by-default schema |
| W5 Evaluation | `test/` | Security, adversarial and integration benchmarks | Independent reproducible test harness |

## Integration policy

- Each PR links an issue with acceptance criteria, owned paths, tests and rollback.
- New public interfaces in `src/openworld_superkernel` need ADR and compatibility review.
- Do not use one branch for simultaneous agent writes; create a separate branch per workstream.
- Never merge just because unit tests pass; report scientific assumptions, failed cases and operational overhead.
- No unapproved cost-bearing services, unauthorized external actions or private data ingestion.
