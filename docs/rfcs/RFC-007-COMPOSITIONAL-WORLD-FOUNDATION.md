# RFC-007 — Compositional World Foundation

**Status:** PROPOSED — not a ratified interface, security guarantee, or production feature.
**Project:** OpenWorld (canonical name and repository).
**Tracks:** W0, W2 (mathematics), W3 (world), W4 (protocols). Related: Issues #1, #3, #4, #5, #11, #13.

## Provenance and name

This RFC adapts ideas **visible in the active OpenWorld conversation**. The separate user-supplied ChatGPT share URL, https://chatgpt.com/share/6ae214d5-8860-83ec-b076-f7834ec8a002, was not fetchable in this execution. The external transcript has **not** been read, imported or credited with unseen details. The earlier two inaccessible shares remain tracked in `docs/project/SESSION-SOURCE-REGISTER.md`; this third URL is distinct and likewise pending access.

OpenWorld is already the canonical name. "Open Civilization Protocol" (OCP) and "OpenWorld Protocol" (OWP) are **conceptual naming proposals**, not approved standards or reasons to rename the repo. Keep Apache-2.0, English-first, local-first, and independence from AHappy.

## Layered foundation

| Layer | Mathematical role | Execution boundary |
|---|---|---|
| Applied category theory | Typed composition; identity and associativity | Only for pure total processes in the experimental fixture |
| Markov kernels | Controlled stochastic transitions and observation | Requires normalization and all exogenous inputs |
| POSG/game theory | Multiple agents with partial information and strategic goals | Policy decisions cannot commit world state |
| Open dynamical systems | Resource, ecology, production, social feedback | Stateful modules require world-authoritative scheduling |
| Agent-based models/graphs | Organizations, communication and sparse interactions | Visibility/ownership must be enforced |
| Evolution and quality-diversity | Candidate selection, adaptation and behavioral diversity | Offline evaluation; never auto-deploy self-generated code |
| Formal contracts/types | Capability boundaries, provenance, invariants | Versioned schema plus tests; no claim of formal proof |

The proposed world state transition is `S[t+1] ~ K(. | S[t], joint_action[t], environment[t])`, while `Omega(o | s)` models observation. For finite kernels, `(K2 o K1)(z|x) = sum_y K1(y|x) K2(z|y)`. Independence between agent policies must be **assumed**, not silently inferred. Category theory does not imply that stateful writes commute.

## Candidate contracts (NOT stable APIs)

| Contract | Direction | Required review |
|---|---|---|
| AgentManifest | creator -> admission | policy ref, owner claim, capabilities, version |
| Observation | world -> agent | filtered visibility, clock, provenance |
| ActionIntent | agent -> world | request ID, principal, tick, schema, bounds |
| WorldEvent | world -> ledger | sequence, stream, provenance, version |
| ModulePorts | world pack -> composer | typed IO, effects, clock, dependencies |
| WorldPackage | creator -> local host | rules/content hashes, licenses, dependencies |
| Federation | host <-> host | explicit trust and transfer/admission policy |

Do **not** mutate the RFC-006 event schema or freeze shared W2/W3/W4 APIs until W0 owner review and migration planning. A2A/MCP may later be adapters for tasks and tools; neither owns simulation truth.

## Experimental implementation

`examples/composable_world.py` is a dependency-free **research fixture** containing:

1. Pure unary typed arrows with identity and sequential composition; mismatched ports fail.
2. Deterministic seeded agent *blueprints*, not identities with real credentials, model weights, learned policies, rights or human psychology.
3. In-memory authorized resource transfers with fixed request ordering, nonnegative balances, per-command atomicity and rejection receipts.
4. Simulation-only events labeled `SIMULATED`, a consistency hash chain and replay from submitted commands under the same code and inputs.

It does **not** implement persistence, real authentication, durable audit of denied actions, source signatures, hardened sandboxing, federated consensus, stochastic simulation, cryptographic tamper resistance, or any form of autonomous weapon control. Request-ID ordering is a toy arbitration policy and may create gameable incentives in production.

## Proposed gates

- G0: composition identity/associativity for pure arrows and port mismatch tests.
- G1: no unauthorized transfers, no negative resources, no double-spend; replay identical with pinned inputs.
- G2: W0-approved compatibility with RFC-006, owner-bound identities, versioned protocol and provenance.
- G3: independent agent and world benchmarks with clear baselines, holdout cases and compute costs.
- G4: sandboxed mods, signed packages and provenance-aware federation after explicit owner approval.
- G5: human playtesting and measurements of meaningful emergent behavior; never infer intelligence from agent count.

**Issue #11 remains open:** tests against this isolated fixture do not replace independently measured tests/benchmarks on merged main.

## Reproduce experiment

```bash
python -m unittest discover -s tests -p 'test_composable_world_experiment.py' -v
```

The submitting environment ran 11/11 isolated tests on Python 3.13.5. The full merged-main suite was **not** executed here because this environment could not reach GitHub through its container network. GitHub Actions and independent verification status must be checked separately.

## Rollback

Remove this RFC, the mathematical notes, the standalone `examples/` module and its test. No existing HyperMemory code, schema, package exports, user records or deployment configurations are modified.
