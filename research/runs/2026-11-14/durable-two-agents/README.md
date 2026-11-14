# Durable two-agent integration: local execution evidence

This is synthetic same-owner CPU research for the optional
[durable two-agent example](../../../../examples/durable_two_agents.py).
It adds no shared runtime API, external effects, user data or paid dependency.

- Branch: `codex/world-durable-two-agent-receipts`.
- Integration base: `f39cd0afe6493df9d77a51004c33368f26884b82`.
- Implementation: `ef369403230909241172a5885d7cb544ada2e151`.
- Final tested source: `c0dae577d9a9934ade4b56fc7cf949bf310a7130`; the
  source hashes, environment, commands and actual exit codes are in
  [validation.json](validation.json).
- The evidence commit follows the tested source and does not change runtime code.

Reproduce from the repository root:

```sh
python scripts/validate_durable_two_agents.py
```

The script runs the new fault/equivalence tests, the full repository suite,
structure/syntax/diff checks, three separate CLI processes and four synthetic
controls. It writes UTF-8 logs and JSON; only temporary synthetic database paths
are normalized in the saved CLI outputs. No user-created database is opened.

Final invocation: exit 0. All 14 targeted tests passed. The full suite ran
500 tests in 137.757 seconds with no unexpected failures, six skips and two
preserved expected security failures. The skips are one real PostgreSQL test
requiring explicit isolated opt-in and five Bash-runner tests unavailable on
this Windows environment. The known security gaps concern restoration of old
capability state and atomic authorization/effects; this integration does not
resolve them.

| Synthetic control | Gifts sent | Returned | Actual loss | Peak actual exposure |
|---|---:|---:|---:|---:|
| Cooperative, notifications only | 8 | 8 | 0 | 1 |
| Cooperative, receipt reconciliation | 20 | 20 | 0 | 1 |
| Hostile, memory gate with immediate feedback | 2 | 0 | 2 | 2 |
| Hostile, fixed offer policy with immediate feedback | 4 | 0 | 4 | 4 |

| Evidence | Purpose |
|---|---|
| [Targeted tests](targeted-tests.log) | Crash boundaries, causal receipts, atomic projections, duplicates, corruption and restart compatibility |
| [Full test suite](full-tests.log) | Repository regression checks, including preserved known security expected failures and explicit skips |
| [First run](restart-1.json), [resume](restart-2.json), [status/history](restart-status.json) | Separate-process continuation at rounds 3, 6 and 6 |
| [Hostile memory policy](hostile-memory.json), [fixed-policy control](hostile-control.json) | Saved feedback can affect A's decisions while both policies retain the four-unit hard cap |
| [Notifications only](cooperative-notifications.json), [reconciliation](cooperative-reconcile.json) | Reconciliation restores cooperation blocked by missing positive notices |
| [Initial findings](initial-validation-note.md) | Preserved initial tuple/list assertion and Windows wrapper-output failure; includes the first raw full-suite log |

Assumptions: one trusted local host, one synthetic owner, two scripted agents,
initial resources 8/0, 20 rounds, seed 2026, exact two-phase world transitions.
The controls use the configuration included in each JSON output. Immediate,
complete feedback is used for the hostile memory-versus-fixed comparison;
the cooperative comparison uses delay 1 and drops every second notification.

Limitations: these are deterministic examples, not a holdout policy benchmark,
independent human acceptance or production security/durability evidence. Six
optional environment checks and the two existing known security failures must
be read from the full-suite summary, not treated as newly certified features.
Memory-gated offers may stop before a partner recovers. Missing negative
feedback never creates budget credit. No runtime speed, storage compression,
power-loss or distributed-writer claim is made.

Rollback the branch's source and evidence commits, preserving any user-created
SQLite file. The existing examples and shared `src` contracts remain unchanged.
The [design document](../../../../docs/experiments/DURABLE-TWO-AGENT-RECEIPTS.md)
describes the transaction/recovery boundary and remaining research gates.
