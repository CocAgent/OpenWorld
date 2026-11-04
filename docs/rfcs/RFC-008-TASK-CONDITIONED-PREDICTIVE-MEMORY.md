# RFC-008 — Task-Conditioned Predictive Memory and Temporal-Aliasing Evaluation

**Status:** PROPOSED, opt-in research; not a runtime, security or paper acceptance decision.  
**Date:** 2026-11-04  
**Ownership:** W1 HyperMemory / W2 MathKernel / W5 Evaluation, with W0 review for any future shared API.  
**Tracking:** [Issue #84](https://github.com/CocAgent/OpenWorld/issues/84).  
**Context:** [RFC-007](../math/RFC-007-OPENWORLD-MATHEMATICAL-FOUNDATIONS.md), [RFC-006](RFC-006-MEMORY-AND-AGENT-CONTRACTS.md), [W5 representation study](../evaluation/W5-POPULATION-REPRESENTATION-BASELINES.md).

## Decision

Study whether a **small conditional predictive state** can preserve decision-relevant temporal dependence that a marginal-only summary loses, and whether a **past-loss gate** can reduce exposure to a misspecified conditional model. The experiment MUST be compared against simple baselines under identical information and scenarios; any claimed improvement is task-specific. Fourier/ECF, RFF and nonlinear kernels remain optional research comparators, not requirements or replacements for the exact ledger.

No production defaults, public interfaces, real-world records, permission systems or cross-owner sharing change under this RFC.

## Kernel terminology and mathematical scope

These are distinct concepts:

1. The **null space** (linear kernel) of a linear encoder A is ker(A) = {v : Av=0}. If two histories h1 and h2 share Ah, then h1-h2 belongs to ker(A). Most actual memory encoders are nonlinear, so their collision/equivalence class f(h1)=f(h2) is the relevant generalization.
2. A **Markov transition kernel** K(B|x,a) is a probability distribution over next states for each current state and action; it is not the null space.
3. A **positive-definite similarity kernel** k(x,x') supports feature maps or an RKHS. Finite random Fourier features approximate specified shift-invariant kernels, but do not automatically preserve histories.
4. An **integral kernel** is the function K(x,y) defining an integral operator. It need not equal any of the three above.

For a declared action and query family Q and prediction horizon h, an approximate task-sufficiency requirement is that histories colliding under f yield close conditional future task distributions, assessed with a declared metric (e.g. total variation, Brier loss or task regret). Neither dimensionality reduction nor a finite ECF sketch gives a universal guarantee.

## Falsifiable counterexample

Let X0 be uniform on {0,1}. A two-state Markov chain keeps the previous value with probability q and flips otherwise. For all q, the stationary marginal is Bernoulli(0.5); hence its one-time characteristic function is identical at every frequency. Yet P(X[t+1]=X[t]|X[t])=q. Compare q=0.9 and q=0.1. Marginal-only compression cannot identify this transition law; conditioning on the previous state can.

This is a standard mathematical construction, **not a novel theorem**. Finite frequency sketches additionally suffer aliasing and are order-insensitive absent explicit lag or joint features.

## Research method

### Predictors (common full-feedback stream)

- **Marginal:** a Beta(1,1) smoothed Bernoulli count, p=(successes+1)/(n+2).
- **Conditional:** a first-order two-state transition count with Beta(1,1) row smoothing; marginal fallback until a row has two transitions.
- **Cost Gate (research heuristic):** maintain discounted prequential Brier losses L_M and L_C. At time t choose conditional only if n>=12 and L_M-L_C>0.005; otherwise choose marginal. After seeing outcome y_t, update each loss using L <- 0.96 L + 0.04(p-y_t)^2, then update both experts. The gate's threshold is a **model-complexity proxy**, NOT a measured CPU-cost optimization or proven regret guarantee.

All probabilities p_t MUST be computed **before** observation y_t. A full-feedback synthetic tape is used by all methods. This is NOT a selective-feedback offer/hold agent policy. Both models receive each observed synthetic label after forecasting; no unobserved counterfactuals are invented.

### Scenarios and split

Use fixed deterministic seeds 83001–83005, length 300, first 60 ticks for online warmup and score prequential forecasts on the remaining 240 ticks. Models **continue updating during the scored interval** after each prediction, so it is an online held-out time segment, not a frozen-policy generalization test.

Predeclared scenarios:
- iid_half: Bernoulli(0.5)
- iid_high: Bernoulli(0.75) (initial t0 is uniform)
- persist: q=0.9
- alternate: q=0.1
- switch: q=0.9 in first half, q=0.1 in second half

Use the same outcome tape per seed/scenario for all predictors. Publish per-seed Brier, source commit, tape SHA-256 and environment.

### Mandatory future extensions before substantive paper claims

1. Independent holdout seed matrix decided **after** code and hyperparameters are frozen; paired uncertainty intervals and tests across seeds.
2. An ablation isolating recency loss, transition counts and gate threshold, with baseline period misspecification if Fourier is included.
3. Separate partial-feedback decision study where abstention reveals no counterfactual label, with measured utility/regret and equal action/probe budgets.
4. Realistic resource study including SQLite main/WAL/SHM online peak, p95 snapshot/forecast latency, CPU/RSS and exact-ledger bytes; do not equate JSON bytes with total storage.
5. Negative controls: shuffled order, same-marginal different dynamics, rare transition regime, missing observation gaps, and deterministic replay.
6. W0/W1/W5 independent review and reproducibility check before integration or scientific conclusions.

## Exact-evidence and privacy non-substitution

Protected/observed/verified/contract-relevant events must remain exact for their authorized retention window; a predictor snapshot, mean, histogram, ECF or spectral sketch is not evidence that an event happened. Checksums are not witness authentication. Authorized erasure, provenance, owner scope and local transactional semantics stay governed by existing RFC-006/implementation. This benchmark does **not** exercise the exact evidence lane.

All new experiments are local CPU-only, simulated, no credentials/network/LLM calls, no real personal data. The gate is not approved for security, resource transfers or real-user decision-making.

## Reproduce pilot

~~~sh
python -m unittest discover -s tests -p 'test_iccies2027_temporal_memory.py' -v
python benchmarks/iccies2027_temporal_memory.py --seed-start 83001 --seeds 5 --steps 300 --warmup 60 --out /tmp/iccies2027-pilot.json
~~~

Do not overwrite existing evidence files. Record raw output and the exact commit SHA; do not report tests as independently verified merely because they ran locally.

## Primary background

- Littman, Sutton and Singh (2001), *Predictive Representations of State* — https://proceedings.neurips.cc/paper/2001
- Rahimi and Recht (2007), *Random Features for Large-Scale Kernel Machines* — https://papers.nips.cc/paper/3182-random-features-for-large-scale-kernel-machines
- Muandet et al. (2017), *Kernel Mean Embedding of Distributions: A Review and Beyond* — https://doi.org/10.1561/2200000060
- Shalev-Shwartz (2012), *Online Learning and Online Convex Optimization* — https://doi.org/10.1561/2200000018

**Originality boundary:** PSRs, Markov conditional probabilities, Fourier features and prequential expert selection are prior art. A publishable contribution requires a carefully defined new question, protocol, negative findings, fair matched baselines and/or independently demonstrated method improvement, not rebranding established mathematics.

**Rollback:** Delete research-only benchmark/tests/RFC; no persistent user state or migrations are affected.
