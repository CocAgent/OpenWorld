# Durable two-agent receipts and memory

This bounded W3/W1/W5 integration connects the existing two-agent receipt lab
to persistent HyperMemory. A sends a simulated resource; B independently follows
the configured return/keep rule. Feedback now comes from B's completed phase,
rather than the separate persistent example's fixed `0, 1, 1` lab sequence.
Both agents belong to the same synthetic owner. There is no LLM, network call,
paid service or real-world action.

## Run, exit and resume

From the repository root, using Python 3.11 or newer:

```sh
python examples/durable_two_agents.py --db data/pair.sqlite3 --rounds 3
python examples/durable_two_agents.py --db data/pair.sqlite3 --rounds 3
python examples/durable_two_agents.py --db data/pair.sqlite3 --status --history
```

The second command starts at round 3 and ends at round 6. A round contains two
W3 ticks: A's gift phase and B's response phase, including empty phases. Status
adds no rounds; startup can recover missing memory from committed records.
Without `--history`, output contains the current balances, budget, unresolved
origins, delayed notices, per-agent predictions and observation counts.

Settings are saved on creation. Resume loads them automatically. An explicitly
different setting is refused; choose a new database for a new experiment.
The total bound is 20 rounds, matching the original P7 toy lab. There is no
destructive reset or migration of existing databases.

```sh
# Default memory policy can stop offering after negative feedback.
python examples/durable_two_agents.py --db data/hostile-memory.sqlite3 --rounds 20 --scenario hostile --delay 0 --drop-every 0

# Fixed-policy control reaches the four-unit risk cap on the same hostile rule.
python examples/durable_two_agents.py --db data/hostile-control.sqlite3 --rounds 20 --scenario hostile --policy always_offer --delay 0 --drop-every 0

# Missing positive notices can block the notifications-only control.
python examples/durable_two_agents.py --db data/notices.sqlite3 --rounds 20 --mode notifications
python examples/durable_two_agents.py --db data/receipts.sqlite3 --rounds 20 --mode reconcile
```

## Decisions, memory and evidence

| Agent | Exact observation task | Use of memory |
|---|---|---|
| A | Whether its issued gift was returned, learned only from delivered feedback or a reconciled committed return | Default `memory` policy requires the HyperMemory return estimate to exceed `0.25 / 0.85`, in addition to available resources and risk budget |
| B | Whether a gift arrived in the completed A phase, including an empty gift phase | Reports its next-gift estimate; return/keep decisions remain the scripted scenario rule |

The threshold is inherited from the synthetic risk-budget reward assumptions,
not calibrated real-world utility. `--policy always_offer` disables the estimate
gate while keeping the same hard cap. B is cooperative, hostile, or starts
returning gifts at the configured zero-based `--recover-at` round. Neither
policy sees evaluator-only actual loss or the future scenario transition.

A's estimate has no access to undelivered outcomes. Positive feedback must
match both its issued origin's completed phase and the exact accepted W3 return
event digest. A negative observation requires the trusted host's completed B
phase; an absent receipt alone is not a loss observation. Missing or dropped
negative feedback remains unresolved. A reconciles positive receipts every
three rounds in `reconcile` mode. Later duplicate notices cannot release the
same reservation or train A again.

Every stored event is `SIMULATED`; predictions are labeled `INFERRED`. B's
incoming-gift estimator is a separate task from A's return estimator. This
does not demonstrate two mutually learning policies or a memory-quality gain
on held-out partners. For example, after two immediate negative outcomes A's
memory policy can stop permanently before a later recovery becomes observable.
The fixed-policy control can exhaust all four loss units permanently.

## Durable boundary and recovery

One local SQLite file contains:

| Table | Role |
|---|---|
| `durable_pair_meta` | Version and fixed experiment settings |
| `durable_pair_journal` | Hash-chained complete rounds: both phase inputs/events, decisions, observations, budget, notification queue and final world fingerprint |
| `exact_events` | Protected HyperMemory evidence under separate owner/agent keys |
| `agent_state` | Each agent's predictive state and latest memory-update receipt |

The live round uses ephemeral same-owner capability tokens through the existing
guarded W3 reducer. Tokens and signing keys are never persisted. Both transfers,
the accepted gift's reservation, B's decision, feedback and resulting channel
state form **one authoritative round transaction**. An interruption before
that commit has no durable simulated effect, including no accepted gift
without its reservation. This boundary works because there are no outside
effects to undo. It is not a distributed authorization/effect transaction.

HyperMemory is a second transaction, atomic across the round's observations for
both agents. If this projection fails after the journal commits, the object
refuses more steps or status until reopened. Startup first replays and verifies
every saved round using fresh in-memory reference memory. It checks all
existing exact/predictive rows against a valid atomic round prefix, then applies
the missing observation suffix in one transaction. A corrupted existing row
or inconsistent journal is refused, never silently replaced with predictions.

SQLite uses WAL and `synchronous=FULL`; an OS file lock excludes cooperating
example processes. Other SQLite clients can bypass this advisory lock. The
hash chain is not an external authenticity or anti-rollback witness. Complete
malicious rewrites and internally consistent old backups are outside scope.
Replay grows with history, and physical power loss, disk-full behavior,
distributed writers and production identity/consent remain unqualified.

## Verification, assumptions and rollback

```sh
python -m unittest discover -s tests -p test_durable_two_agents.py -v
python scripts/validate_durable_two_agents.py
```

The validation script records commands, exit codes, source SHA/digests,
Python/SQLite/OS metadata, raw test logs, separate-process restart outputs and
synthetic control results in
[`research/runs/2026-11-14/durable-two-agents/`](../../research/runs/2026-11-14/durable-two-agents/).
Its tests cover the hard cap after repeated restarts, delayed/duplicate feedback,
receipt origin/digest binding, real process exits at both commit boundaries,
projection rollback, corruption and unrelated-store rejection, and concurrent
writer exclusion. Process exits do not certify storage-hardware durability.

This is an example-only integration stacked on the existing research branch,
with no new shared `src/openworld_superkernel` interface or schema migration.
The original two examples remain compatible. Upstream Issue #11 and known
security expected failures remain open; local tests do not ratify shared
contracts. Ownership: W3 example implementation, W1 existing memory consumer,
W5 fault/equivalence validation. No benchmark speed, compression or general
policy-superiority claim is made.

Rollback the source commit and its evidence follow-up; retain any user-created
SQLite files. The existing examples use different table names and refuse this
store. Never open a saved experiment under a different format or silently
convert its evidence. No changes are merged into `main` by this work.
