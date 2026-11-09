# OpenWorld hosted-research execution freeze

**Status:** Proposed configuration change in PR; effective only after review and merge.
**Owner request date:** 2026-11-09.
**Scope:** This public repository's GitHub Actions, not external services, private repositories or local machines.

## Decision

Suspend automatic cloud-hosted tests and all W5 PostgreSQL research runs
to avoid unattended consumption of hosted runner minutes. Preserve
source code, benchmarks, raw data, prior audit history and tests. This
freeze does **not** authorize a new experiment, reproduce old outcomes,
or change existing scientific acceptance gates.

## GitHub Actions policy after merge

| Workflow | Automatic push / PR / schedule | Manual availability | Hosted resource impact |
| --- | --- | --- | --- |
| `python-package.yml` | **No** | Opt-in on `main` only, requires `RUN_FAST_ONLY` acknowledgment | Zero unless deliberately run; the manual run still consumes runner minutes |
| `w5-postgres-parity-manual.yml` | **No** | Workflow is visible but all jobs are unconditionally skipped | No PostgreSQL container or hosted runner allocated |

The Python manual workflow explicitly sets `OPENWORLD_SLOW_TESTS=0` and omits
benchmark compilation. It is a fast correctness/security smoke check, not
a research-matrix executor. A user with Actions permissions can request
the workflow, but only the exact required input allows the fast job.

No currently checked OpenWorld workflow has a cron schedule. As of the
repository check on 2026-11-09, queued, waiting and in-progress run
queries each returned zero. This is a time-bounded observation, not a
continuing-monitoring claim.

## Local-only validation

No cloud runner is needed for the fast local checks:

```bash
python -m unittest discover -s tests -v
python scripts/check_repository.py
python examples/r0_agent_cycle.py
```

The small R0 example is a simulated local fixture; it is not a live
world experiment. The slow research matrices remain excluded when
`OPENWORLD_SLOW_TESTS` is unset. Do **not** set it to `1` as part of a
routine verification while the freeze is in place.

## Important effects

1. New pull requests and commits will **not** receive automatic Python
   validation after this configuration is merged. Reviewers must not
   interpret missing CI as passing CI.
2. Existing branch rules that require particular status checks may block
   merges; inspect and update branch/ruleset settings through an
   explicitly approved administrative review, rather than bypassing them.
3. This repository change cannot stop a workflow already running on the
   old default branch, a personal computer, an external runner, or another
   repository. Existing run history and artifacts remain subject to their
   retention policies.
4. It does not remove Python tests, benchmark scripts, research evidence,
   or historical source; it changes only when CI may allocate resources.
5. The freeze is about cost control. It does not resolve scientific
   uncertainty or close independent evidence Gate #11.

## Re-enable (separate owner decision required)

Create a new PR with a budget cap, exact workflow changes, expected runner
cost, task/seed policy, review of leakage and security, rollback and an
explicit owner approval. Keep scheduled and PR-triggered slow research
disabled by default. Security fixes remain allowed without running
expensive research workloads.

## Rollback

A reviewed PR may restore the previous workflow files from the commit
preceding this freeze. Do not blindly restore automatic slow-matrix
execution without a specific approval and cost estimate.
