# OpenWorld

**An open ecosystem for adaptive, collaborative, and evolving AI agents.**

OpenWorld is an independent, experimental open-source project exploring persistent agent identity, auditable memory, online adaptation, resource-aware reasoning, and collaboration. It is **not production ready**.

## Core components

| Component | Responsibility |
|---|---|
| **SuperKernel** | Agent lifecycle, policy, tools, budgets, and scheduling |
| **HyperMemory** | Exact historical evidence plus compact predictive memory |
| **MathKernel** | Stochastic processes, Bayesian learning, predictive state, information theory |
| **World Runtime** | Reproducible environments, event queues, sparse social interactions |
| **Open Protocols** | Capability-based interoperability and trusted interfaces |

An agent identity is **not** a dedicated foundation model. Agents may share inference engines while retaining separate memories, permissions, and histories.

## Getting started

Requires Python 3.11+; no GPU, model key, or paid GitHub Actions.

```bash
python -m unittest discover -s tests -v
python scripts/check_repository.py
```

See [Architecture](docs/ARCHITECTURE.md), [Workstreams](docs/WORKSTREAMS.md), [Roadmap](docs/ROADMAP.md), [Research limitations](research/RESEARCH-STATUS.md), and [Contributing](CONTRIBUTING.md).

## Experimental compositional world research

[RFC-007](docs/rfcs/RFC-007-COMPOSITIONAL-WORLD-FOUNDATION.md) proposes a layered mathematical foundation combining typed composition, stochastic games and world dynamics. See the [mathematical notes](docs/math/COMPOSITIONAL-WORLD-NOTES.md) and [dependency-free example](examples/composable_world.py). These are **research prototypes**, not approved OWP/OCP protocol standards or the production SuperKernel.

```bash
python -m unittest discover -s tests -p 'test_composable_world_experiment.py' -v
```

## Scientific and safety boundaries

- No claim of billion-agent scalability, universal compression, or human-level intelligence.
- A simulated or inferred memory is never evidence of an observed real-world event.
- External actions and memory sharing require explicit authorization.
- Benchmarks must include actual on-disk cost (including WAL), CPU, accuracy, uncertainty and baselines.
- Historical prototype ZIP files are **not public** pending independent license, secret, security and reproducibility review.

## Language and license

English is the canonical language for code, comments, issues, RFCs and pull requests. New source and documentation are available under [Apache-2.0](LICENSE).

## Project continuity and previous sessions

Start new work sessions with the [canonical project continuity](docs/project/PROJECT-CONTINUITY.md), [decision ledger](docs/project/DECISION-LEDGER.md), [source register](docs/project/SESSION-SOURCE-REGISTER.md), and [execution handoff](docs/project/EXECUTION-HANDOFF.md). Two externally shared ChatGPT session URLs are logged as **pending access**, not represented as imported transcripts. Research findings and merged-source statuses are clearly distinguished from independently reproduced measurements.
