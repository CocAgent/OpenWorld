# ICCIES 2027 temporal memory — secondary holdout note

**Status:** assistant-run local experiment, not independent replication or final paper evidence.  
**Date:** 2026-11-04; **Issue:** [#84](https://github.com/CocAgent/OpenWorld/issues/84).  
**Benchmark code:** ../..//benchmarks/iccies2027_temporal_memory.py (research only).  
**Locked pilot configuration:** gate decay 0.96, penalty 0.005, n>=12; no tuning on this holdout.

## Provenance

- After initial five-seed pilot and draft benchmark code were written, ran a distinct fixed seed block **83101–83130** (30 seeds x 5 scenarios = 150 scenario-seed cases).
- 300 ticks per scenario and seed; first 60 used as online warmup, remaining 240 scored **prequentially**; models continue learning after each scored prediction.
- Python **3.13.5**; Linux 6.18.57 x86_64 with glibc 2.41, observed in the local execution container.
- Raw JSON filename **holdout30-results.json**, 120,706 bytes; SHA-256 **0aaf94408a4b2970154cf3e844bee89ac9c65518332cd13280f1f7a58badc4da**. This raw file is not yet checked into GitHub: obtain it from the research operator or regenerate from pinned code and capture a new checksum. Instrumented CPU timings may change across reruns.
- Each predictor observes the same synthetic label, **after** producing its forecast. This is full-feedback probabilistic forecasting, not counterfactual partial-feedback learning.

## Mean Brier score on secondary holdout (lower is better)

| Scenario | Marginal | Conditional | Cost Gate |
|---|---:|---:|---:|
| iid_half | 0.2515 | 0.2531 | 0.2517 |
| iid_high | 0.1850 | 0.1863 | 0.1850 |
| persist q=0.9 | 0.2513 | 0.0897 | 0.0897 |
| alternate q=0.1 | 0.2517 | 0.0930 | 0.0930 |
| switch q=0.9 -> 0.1 | 0.2565 | 0.2881 | 0.2106 |

**Paired gate-minus-marginal mean differences**, with exploratory 95% percentile bootstrap intervals over 30 independent seeds (5,000 resamples from a separate fixed RNG seed 2027; resample pairs by seed):

| Scenario | Difference | Exploratory bootstrap interval |
|---|---:|---:|
| iid_half | +0.00023 | [-0.00001, +0.00044] |
| iid_high | +0.00006 | [-0.00013, +0.00024] |
| persist | -0.16163 | [-0.16901, -0.15397] |
| alternate | -0.15870 | [-0.16433, -0.15297] |
| switch | -0.04592 | [-0.04980, -0.04212] |

These confidence intervals condition on the specific synthetic generator and fixed code; they do not measure generalization to realistic agents or other dynamics. Historical selection of experimental scenarios must be acknowledged in author-written text.

## Resource warning

Across these 150 runs, median serialized **predictor JSON only** at the end was approximately 17 bytes (marginal), 54 bytes (conditional), 184 bytes (gate). Median instrumented process CPU measured over the 300 ticks per case was approximately 0.2444 ms, 0.3293 ms and 0.5684 ms respectively on this single system. CPU samples include Python instrumentation and have not been independently standardized or cross-machine replicated.

These are NOT SQLite footprint, WAL/SHM, p95 end-to-end latency, process RSS, exact ledger cost, energy or infrastructure benchmarks. Cost Gate is a historical-error gate with a model-complexity penalty proxy; it can have **higher** real compute cost even when selecting the cheaper predictor because both experts are updated.

## Interpretation and limitations

- In stationary Markov synthetic regimes, transition counts accurately capture dependence missing from the Bernoulli marginal, as expected by construction. This is not a new theorem.
- IID regimes show little/no gate advantage; added complexity may be unjustified.
- Abrupt switch exposes the pooled transition counter's failure and shows the discounted gate's ability to fall back; neither is guaranteed in arbitrary nonstationary processes.
- This test cannot justify claims about exact event recall, access control, real-world data, a functioning multi-agent system, published novelty or production memory efficiency.
- The authoring assistant ran this, so it is a **secondary holdout**, not independent researcher replication. A genuinely independent reviewer must run the committed benchmark and additional stress cases, and the author must verify the paper's original contribution.

## Required follow-up

1. Archive raw JSON and a SHA-256 checksum alongside the pinned PR head.
2. Re-run six focused tests and full repository checks on the PR branch; record CI status and interpreter version.
3. Add missing/partial feedback, rare events, threshold sensitivity and a realistic decision objective; use separate new seeds.
4. Measure actual SQLite peak online bytes and p95 latency alongside exact evidence.
5. Have human authors write the manuscript under the ICCIES 2027 no-AI-generated-text rule.

To reproduce the secondary block on the PR branch:

~~~sh
python benchmarks/iccies2027_temporal_memory.py --seed-start 83101 --seeds 30 --steps 300 --warmup 60 --out holdout30-results.json
~~~

Do not overwrite the existing evidence file. Any change to source/hyperparameters invalidates the frozen claim and requires a new run ID.
