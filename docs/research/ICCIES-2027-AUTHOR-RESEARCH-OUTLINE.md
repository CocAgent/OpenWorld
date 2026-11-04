# ICCIES 2027 — Human-Author Research Outline (NOT manuscript text)

**Status:** author planning aid, not a submission-ready paper and not a promise of acceptance.  
**Prepared:** 2026-11-04; **tracking:** [Issue #84](https://github.com/CocAgent/OpenWorld/issues/84).  
**Source:** https://iccies.tdtu.edu.vn/2027/ and https://iccies.tdtu.edu.vn/2027/how-to-submit/ .

## Organizing constraints

The official conference announcement dated 2026-11-02 extends submission until **2026-11-15**; conference dates are **2027-04-15 to 2027-04-17**. Submission is a single PDF through https://cmt3.research.microsoft.com/ICCIES2027 . The 2027 guide specifies **English**, **Springer LNCS/LNAI format**, **12–15 pages**, original unpublished contributions, and **prohibits AI-generated text in the submitted paper**. This repository file is a research notebook/outline; the final paper narrative must be written by the human author(s). Confirm latest track details and interpretations with conference organizers.

The proposed paper centers on memory for adaptive agents, so the primary computational-intelligence track is a suitable candidate; the GALLIS special session explicitly covers AI agents and benchmarking but is not necessary to frame a non-LLM method. Do not claim the work evaluates generative AI or LLMs.

## Working title alternatives (human authors must select and independently formulate)

- Temporal Aliasing in Compact Predictive Memory for Adaptive Agents: An Empirical Study
- Evaluating Conditional Predictive Memory Under Matched Marginals and Regime Shifts
- Task-Sufficient Memory for Synthetic Adaptive Agents: What Marginal Summaries Forget

These are working research descriptors only. Novelty must be checked against the literature before submission.

## Research questions

- **RQ1 (aliasing):** How much prediction performance is lost when histories with the same one-time marginal but different temporal dependence are mapped to the same summary?
- **RQ2 (regime shifts):** Does a bounded conditional Markov state beat a marginal-only state, and can a prequential loss gate avoid its worst misspecification failures?
- **RQ3 (resources):** Do benefits remain after accounting for the additional predictor state, runtime, SQLite persistence and independent exact evidence?

## Experimental setup, fixed before pilot

- Dataset: deterministic *simulated* binary sequences, no external/private/user records.
- Five regimes: IID p=0.5; IID p=0.75; Markov persistence q=0.9; anti-persistence q=0.1; q=0.9 then q=0.1 switch.
- Five pilot seeds 83001..83005, 300 ticks per seed/scenario; warmup 60, then prequential Brier scoring on ticks 60..299, with continual post-prediction updates.
- Baselines: Beta(1,1) marginal Bernoulli count; Beta(1,1) first-order conditional transition count; discounted-loss gate (decay 0.96, penalty 0.005, min 12 observations).
- Paired outcome tapes, common observation budget, pre-outcome prediction, deterministic SHA-256 evidence, no benchmark leakage.
- No real agent decision regret, partial feedback, calibrated uncertainty, or system-level storage validated in pilot.

## Initial local pilot observations, NOT independently reviewed

The authoring assistant executed the isolated experiment locally on 2026-11-04 (Python 3.13.5, Linux x86_64), with six focused unit tests passing. Raw per-seed JSON file is generated separately by the reproducible benchmark command below; it must be committed and independently rerun on the exact PR SHA before paper-quality reporting.

| Scenario | marginal | conditional | cost_gate |
|---|---:|---:|---:|
| iid_half | 0.251210 | 0.252707 | 0.251511 |
| iid_high | 0.189227 | 0.190232 | 0.189560 |
| persist | 0.252082 | 0.093922 | 0.093922 |
| alternate | 0.251642 | 0.085803 | 0.085803 |
| switch | 0.254772 | 0.291833 | 0.210100 |

Lower Brier is better. These values are five-seed averages only: no uncertainty estimates, effect size inferential claims, or representative workload claims. The gate does not win IID; the conditional-only method fails sharply under switch. The synthetic generator deliberately matches model assumptions in some regimes. Publication-level evidence will need independent seeds, ablations and actual resource measurements.

## Author-driven section plan, 12–15 Springer pages (not generated submission prose)

| Section | Scientific evidence/asset required from authors |
|---|---|
| Introduction | Define narrow deployment-motivated question; justify why aliasing affects action-relevant decisions; identify originality limits |
| Related Work | Verify PSR, sufficient statistics, Markov switching models, online expert selection, RFF/ECF and memory/evidence literature; cite actual primary papers |
| Formal Problem | State history-to-memory encoder, loss/query/horizon, non-equivalence of marginal and temporal law, assumptions and failure cases |
| Candidate Method | Define marginal/conditional/gate recursions, complexity, no-regret non-claim, protected exact evidence boundary |
| Experimental Protocol | Pre-registered seeds, workloads, equal information budget, calibration/decision/resource metrics, independent test design |
| Results | Only measured tables with intervals and raw input/output hashes; negative and adverse cases not omitted |
| Ablations and Threats | Shift sensitivity, gap handling, threshold/decay dependence, partial feedback and fairness of baseline compute costs |
| Conclusion | Qualify empirical scope and avoid generalization to production, LLM cognition, global multi-agent intelligence |

### Figure and table specification

- Figure A: two symmetric Markov chains with identical stationary marginals and different transition matrices.
- Figure B: cumulative prequential Brier losses by tick, including the shift boundary.
- Figure C: utility/runtime or Brier/state-size tradeoff (only after resource measurement).
- Table A: paired per-seed scores and confidence intervals.
- Table B: ablation, positive/negative controls and CPU/SQLite cost.
- Table C: safety/data boundaries and which claims were NOT tested.

## Evidence collection

~~~sh
python -m unittest discover -s tests -p 'test_iccies2027_temporal_memory.py' -v
python benchmarks/iccies2027_temporal_memory.py --seed-start 83001 --seeds 5 --steps 300 --warmup 60 --out pilot.json
python -m unittest discover -s tests -v
python scripts/check_repository.py
git rev-parse HEAD
sha256sum pilot.json
~~~

Never overwrite existing pilot evidence. Run a separate, locked follow-on seed matrix, with paired confidence intervals and fixed hyperparameters; save raw outputs and failed trials. Do not call two samples statistically significant without appropriate repeated-run analysis.

## Prior art to verify (not an automatic bibliography)

1. Littman, Sutton, Singh (2001), Predictive Representations of State — https://proceedings.neurips.cc/paper/2001
2. Shalev-Shwartz (2012), Online Learning and Online Convex Optimization — https://doi.org/10.1561/2200000018
3. Rahimi and Recht (2007), Random Features for Large-Scale Kernel Machines — https://papers.nips.cc/paper/3182-random-features-for-large-scale-kernel-machines
4. Muandet, Fukumizu, Sriperumbudur, Schölkopf (2017), Kernel Mean Embedding of Distributions — https://doi.org/10.1561/2200000060

Human authors must confirm bibliography metadata, priority of related methods, originality and the conference AI-text rule. The software benchmark and this planning file are not themselves publication text.

## Decision gate

**Do not submit the current pilot as if it were a validated new memory algorithm.** Proceed to independent replication, held-out uncertainty, partial-feedback action study and true storage/cost tests. The human authors then decide whether evidence is sufficiently original and robust for ICCIES 2027.
