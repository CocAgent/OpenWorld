# OpenWorld Decision and Hypothesis Ledger

This ledger is a **living summary**. It does not supersede normative ADRs in [docs/DECISIONS.md](../DECISIONS.md) or the proposed RFC-006. A prior chat recommendation is not an adopted interface, and a merged code change is not a production qualification.

| ID | Decision or hypothesis | State | Evidence / next action |
|---|---|---|---|
| OW-D01 | Project name and repository: **OpenWorld**, `CocAgent/OpenWorld` | **Confirmed** | Public GitHub repository |
| OW-D02 | The project is independent from AHappy | **Confirmed scope** | Owner's earlier explicit architecture choice; project documents |
| OW-D03 | English-only public repository artifacts and one monorepo | **Accepted** | ADR-001 / ADR-002 |
| OW-D04 | Separate agent identities from shared model weights and per-agent memory/state | **Design principle** | OpenWorld architecture, requires scaling evaluation |
| OW-D05 | Memory uses exact evidence + predictive state + replayable generative processes | **Design principle; partial prototype** | RFC-006 + HM-P1e; exact/predictive interfaces evolving |
| OW-D06 | A simulated or inferred memory must not masquerade as observed history | **Required safety invariant** | RFC-006 proposed; source checks exist but not production-enforced end to end |
| OW-D07 | Digital genome and epigenome can encode stable initial traits and adaptive parameters | **Research hypothesis** | Prior conceptual design; not a biological claim or general data compression theorem |
| OW-D08 | Characteristic functions support stochastic representation but not by themselves temporal dependence | **Mathematical clarification** | Needs family of finite-dimensional laws / controlled transition model |
| OW-D09 | Predictive sufficiency is scoped to tasks, horizon, observations, actions and evaluation loss | **Mathematical requirement** | W2 / RFC-006 |
| OW-D10 | Adaptive models (static, discounted fast/slow, ensembles) should be selected only when they add measured benefit | **Research hypothesis** | HM-P1e heuristic; W5 holdout/ablation required |
| OW-D11 | Retain exact events according to retention and user rights; do not deduce authenticity from a hash alone | **Required safety invariant** | RFC-006 proposed; operational security pending |
| OW-D12 | Implement CPU-only tests and independent benchmarks before GPUs/distributed runtime | **Accepted execution policy** | ADR-004 and Issue #11 |
| OW-D13 | W0/W1/W5 first, W2/W3/W4 after interface/quality review | **Accepted work order** | Issues #1–#6; W0/W1/W5 PRs merged but test gate remains open |
| OW-D14 | Apache-2.0 applies to new OpenWorld-authored content; historical prototypes need audit before release | **Accepted publication boundary** | ADR-005; repository LICENSE |
| OW-D15 | OpenWorld Companion and Civilization are possible future products, not current released features | **Product hypotheses** | Needs validated user value, consent, security and operational cost |
| OW-D16 | Billion-scale populations are aspirational research goals, not benchmark results | **Explicit non-claim** | Issue #11 / research status |

## Acceptance distinctions

- **Proposed:** design agreed for exploration but may lack owner signoff or implementation.
- **Implemented:** source committed to repository; not automatically tested or deployed.
- **Independently verified:** reproducible execution on a pinned SHA and documented environment.
- **Deployed:** actual operating system with measured monitoring and safety controls.
- **Rejected/superseded:** keep historical trail explaining what changed and why.

## Known negative results and open tradeoffs

Earlier dialogue reported that HM-P1d ensemble-style adaptation sometimes improved drift prediction yet lost to a simpler static estimator in stable/noisy conditions, while consuming more resources. Earlier HM-P1 and HM-P1c storage performance varied with SQLite WAL and checkpoint behavior. These historical results are **not independently verified here** and must be reproduced before becoming acceptance evidence.

The memory compiler is not an automatic truth detector. A compressed summary cannot, in general, answer every query that exact historical records could answer. A purported 'cost-aware' gate must measure total runtime cost, not only impose a threshold on predictive loss.

## What not to infer

The presence of RFCs, issue tickets, unit tests, or GitHub merges does not establish user consent enforcement, identity key management, globally distributed correctness, algorithm novelty, published research, or production reliability.
