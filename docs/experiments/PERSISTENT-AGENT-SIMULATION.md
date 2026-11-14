# Persistent same-owner agent simulation

This optional CPU-only example keeps a bounded W3 simulation and HyperMemory
across process restarts. It creates exactly two same-owner scripted agents,
Alice and Bob, initially holding three resources each. They alternate turns.
The action rule is transfer one unit when the actor's prediction is at least
0.5 and its balance is positive; otherwise send a zero-resource signal.

The lab supplies the repeating feedback sequence `0, 1, 1` after accepted
actions. This is not a return decision from the receiving agent, outside
evidence, a trained language model or proof of policy utility. Each agent's
statistics and exact events are separate under its owner/agent keys.

## Run and resume

From the repository root:

```sh
python examples/persistent_agents.py --db data/openworld.sqlite3 --steps 3
python examples/persistent_agents.py --db data/openworld.sqlite3 --steps 3
python examples/persistent_agents.py --db data/openworld.sqlite3 --status
python examples/persistent_agents.py --db data/openworld.sqlite3 --status --history
```

Use the same database path on every invocation. Relative paths are relative to
the shell's current working directory; the JSON output reports the resolved
absolute path. The first call creates the file and ends at tick 3. The second
starts at tick 3 and ends at tick 6, with six exact memory events. At this point
Alice has four resources, Bob two, and each has three feedback observations and
two successes. `--status` adds no simulation actions; it can repair a lagging
memory projection from committed exact journal records. `--history` includes
the exact recorded inputs, predictions, world hashes and feedback.

Each invocation accepts 1-100 additional steps; the example is bounded to
1,000 total ticks. There is no destructive reset command. Choose a new database
path for an independent fresh experiment. An existing unrelated database is
refused, and no schema migration is attempted.

## What is saved

One SQLite file contains four application tables:

| Table | Responsibility |
|---|---|
| `persistent_demo_meta` | Fixed format, owner, agents, feedback schedule and genesis fingerprint |
| `persistent_demo_journal` | Authoritative accepted action plus synthetic outcome for every tick, with a record hash chain |
| `exact_events` | HyperMemory's protected exact feedback events, payload bytes and hashes |
| `agent_state` | Each agent's observation count, successes, fast/slow/static estimator state and latest idempotency receipt |

World balances, ticks and event history are restored by deterministic replay of
the exact journal. Predictions are not used to invent past events. Startup
checks the complete journal, action rule, expected sequence, feedback schedule,
world hashes and already-materialized memory before applying missing records.
Existing mismatched memory or journal data causes a stop, not silent repair.
Reference validation uses a temporary in-memory HyperMemory database.

## Commit and failure boundary

1. The trusted host obtains ephemeral same-owner capabilities and executes an
   action through the existing guarded in-memory W3 reducer.
2. It commits the exact action and feedback as one SQLite journal record. That
   commit defines a durable step in this **pure simulation**.
3. It updates HyperMemory using a second SQLite transaction. Exact memory
   events and predictor state are atomic within this second transaction.
4. On restart, an uncommitted journal insert has no saved effect. A committed
   journal record with a missing memory update is materialized exactly once.
   If memory was already updated, the recorded agent sequence prevents another
   training update.

Sharing a file does not turn these into one transaction. The example relies on
an authoritative exact journal and explicit recovery, not a claim that the W3
reducer and HyperMemory are atomically committed. There are no external tool,
payment or network effects to replay. Persisted records omit bearer tokens and
signing keys; keys are generated afresh for each live step. Historical replay
does not re-authenticate the original grants.

A cross-platform OS file lock rejects concurrent instances of this example and
is released by the OS when a process exits. The small `.sqlite3.lock` file may
remain. The lock is advisory for cooperating example processes; this is not a
multi-writer server or protection from another SQLite client editing the file.
Hash chains detect checked inconsistencies, not a malicious complete rewrite
or restoration of an internally consistent old backup without an external
anchor. Replay/startup cost grows with history; no scaling claim is made.

## Verification

```sh
python -m unittest discover -s tests -p test_persistent_agents.py -v
```

Tests cover separate-process resume, both agents' memory, equivalence to an
uninterrupted run, predictor warmup, status/history without new actions,
pre-commit rollback, actual process exit between journal and memory commits,
exit after both commits, duplicate prevention, corruption rejection, refusal
of unrelated databases and concurrent-process exclusion. These local tests do
not establish power-loss durability, disk-full recovery or production safety.

Execution evidence: [`research/runs/2026-11-14/persistent-agents/`](../../research/runs/2026-11-14/persistent-agents/).
The optional example and tests add no shared `src/openworld_superkernel` API,
no schema migration for existing stores, paid dependency or external endpoint.
Rollback removes the example and its documentation/tests. Preserve any demo
database the user wants to retain; deleting source does not delete saved data.
