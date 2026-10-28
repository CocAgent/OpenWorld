# W3 — Experimental Local World Fixture

**Status:** Research-only, no protocol freeze or production/security certification. **Tracking:** [Issue #4](https://github.com/CocAgent/OpenWorld/issues/4), W0 [Issue #1](https://github.com/CocAgent/OpenWorld/issues/1), W5 [Issue #11](https://github.com/CocAgent/OpenWorld/issues/11).

## Scope and compatibility

- Source: src/openworld_superkernel/world_fixture.py is a standalone W3 experiment; it does not change existing package exports, RFC-006's event envelope, HyperMemory, MathKernel or examples/composable_world.py.
- Simulated agents have fixed ID, owner, region and integer resource balance. Undirected graph edges define valid one-hop interactions; candidate traversal visits only neighbors of active agents.
- The in-memory authoritative reducer accepts transfer and signal intents. Every tick requires an explicit tuple of exogenous weather updates, including the empty tuple when none occurred. Missing external inputs fail closed.
- Conflicting transfers are serialized by (request_id, action_hash) order, duplicate IDs are blocked, and unsupported/stale/unauthorized/non-neighbor actions are rejected. This is deterministic but NOT a fairness or Sybil-resistance policy.
- Every applied event is marked SIMULATED, hash-linked and sequenced. The world retains the complete in-memory submitted tick-input journal including rejected actions, for strict replay from genesis. Hash agreement is not a signature, independent witness or protection against a malicious host.
- Agent observation includes its own balance, local weather, graph neighbors and targeted signal receipts. Other agent balances, owners and unrelated event contents are not returned. This is demonstration-level filtering, NOT authenticated access or isolation from hostile Python code.
- Seeded social demo policies choose one neighbor by SHA-256 of (seed, tick, actor) to remove Python PRNG-version differences. SHA-256 does not represent independently verifiable entropy.

## Reproduce CPU tests and microbenchmark

~~~sh
python -m unittest discover -s tests -p 'test_world_fixture.py' -v
python examples/world/demo.py --agents 30 --ticks 20 --seed 2026
python scripts/check_repository.py
~~~

The first isolated W3 test run in the authoring environment passed **13/13** on Python 3.13.5. For a 30-agent, 20-tick synthetic chain-graph scenario, the local example recorded 220 simulated events with an exact replay match. Recorded authoring-environment measurements: 0.025850 CPU-observation wall seconds (perf_counter, not process CPU time), around 8,510 events/second and 146,806 tracemalloc peak bytes. These **single-run toy measurements** are not independently verified, are not RSS, and should not be extrapolated to production loads. GitHub CI/full-suite status must be checked at the precise PR commit.

## Missing / next gates

1. Real authenticated identity, capability grants, revocation and durable access audit require W0 and W4.
2. Event persistence, crash recovery, compact checkpointing, external input validation and replay versioning are absent; do not promise long-lived worlds.
3. In-memory journal and event tuples scale with total history; event throughput is not proven linear as time grows. High agent counts and unknown partner policies are not yet benchmarked.
4. No agent policy learning, model inference, World Pack, federation, human UI, secure mod sandbox, real economy or institution emergence.
5. W5 should run independent workloads across sparse/hub graphs, adversarial inputs, multi-seed holdouts, CPU, RAM, event throughput and replay mismatches before W3 acceptance.

**Rollback:** Remove only the new W3 fixture, tests, demo and this research document. No schema migration, deployment or paid resources.
