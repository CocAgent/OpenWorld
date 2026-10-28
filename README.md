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

## Research foundations and related projects

The [curated research map](docs/research/RELATED-RESEARCH-AND-PROJECTS.md) covers **16 primary papers** on applied category theory, Markov categories, POSGs, multi-agent environments, generative societies, quality-diversity and co-evolution, plus candidate open-source implementations. It maps each publication to a falsifiable OpenWorld experiment and clearly distinguishes prior art from OpenWorld outcomes.

The [October 2026 session synthesis](docs/project/SESSION-SYNTHESIS-20261028.md) reconciles the owner-supplied design iterations: an open strategic game, local-first community worlds, agent genesis, the trusted SuperKernel and optional compositional mathematics. **OpenWorld** is the canonical project name; "Open Civilization Protocol" (OCP) and "OpenWorld Protocol" (OWP) remain unratified design labels. Neither social evolution nor federation is a shipped feature.

## Experimental compositional world research

[RFC-007: Mathematical Foundations](docs/math/RFC-007-OPENWORLD-MATHEMATICAL-FOUNDATIONS.md) is the existing proposed W2 research architecture. The independent [EXPR-001 fixture](docs/experiments/COMPOSABLE-WORLD-FIXTURE.md), [mathematical notes](docs/math/COMPOSITIONAL-WORLD-NOTES.md), and [dependency-free example](examples/composable_world.py) explore only pure typed composition, agent blueprints and resource transfer/replay. They do **not** constitute approved OWP/OCP standards or production SuperKernel code.

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

Start new work sessions with the [canonical project continuity](docs/project/PROJECT-CONTINUITY.md), [decision ledger](docs/project/DECISION-LEDGER.md), [source register](docs/project/SESSION-SOURCE-REGISTER.md), and [execution handoff](docs/project/EXECUTION-HANDOFF.md). Refer to the source register for evidence provenance and verification status.
