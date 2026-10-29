# OpenWorld Population Representation and Agent Genome — Research v0.1

**Status:** PROPOSED mathematical architecture + isolated standard-library experiment, **not** a public protocol or trained population.  
**Date:** 2026-10-29. **Owners:** W2 MathKernel + W3 simulation + W5 evaluation; W0 controls any future shared contracts.  
**Motivation:** Reconcile earlier open-ended agent/civilization sessions with the owner's specific characteristic-function, QID, FQID, Riemann-hypothesis and quantum-computation references.

## 1. Recommendation (engineering first)

**Choose heterogeneous, stratified mean-field MARL and sparse graph interactions** for population modeling; use **empirical characteristic functions (ECFs)** or random Fourier/kernel mean embeddings as **optional bounded distribution features**, not as complete agent state, proof of independence, or primary DNA. Keep the existing W2 finite Markov kernel and W3 authoritative world as implementation foundations. Shared policies may be conditioned on local genome traits and memory; the exact event ledger remains separate.

| Purpose | Proposed representation | Why / limitation |
|---|---|---|
| World transition | Controlled stochastic kernel with trusted, replayable external inputs | W2 existing core; may be expensive in a large joint state |
| Large population | Empirical measures per role/region, mean-field summaries | Cheap **if** reward/dynamics depend on those summaries; heterogeneous populations need strata |
| Agent neighborhood | Sparse typed interaction graph and bounded messages | Important individual exceptions remain explicit rather than lost in an average |
| Population distribution feature | ECF at K fixed frequencies, optionally random Fourier features | Cost O(NKd) for N points of dimension d, K frequencies; finite K **not injective** |
| Learning | Parameter sharing per role + individual conditioning, optional offline population encoder | Training/inference still costs per active agent; no billion-agent claim |
| Individual "DNA" | Versioned typed genome: archetype, bounded traits, policy artifact *reference*, lineage | No identity, secret, capability, proof of cognition, exact memory or raw model weights |
| Agent identity, memory, rights | W0/W1/W4 trust/ledger contracts | Must **never** be derived from population ECF or genome |
| Emergence/evolution | Offline evolutionary search, quality-diversity/archive and held-out admission | Evolution is a tested process, not unrestricted executable-code mutation |

**Do not choose** quasi-infinitely divisible/free-QID distributions, the Riemann hypothesis or quantum computing as first-stage runtime foundations.

## 2. Finite-population mathematical model

Let agent i carry observable/simulated state x_i(t) and role/region stratum r(i). For each nonempty stratum r:

```math
\mu_t^{(r)} = \frac{1}{N_r(t)}\sum_{i:r(i)=r}\delta_{x_i(t)}.
~~~

An optional **empirical characteristic signature** for fixed frequencies $\omega_1,\ldots,\omega_K$ is

```math
\widehat{\varphi}^{(r)}_t(\omega_k)
=\frac{1}{N_r(t)}\sum_{i:r(i)=r}
\exp(\mathrm{i}\,\omega_k^{\mathsf T}x_i(t)), \quad 1\leq k\leq K.
~~~

Each sketch comprises K real/imaginary pairs; the overall feature size is O(number-of-strata * K), excluding counts and feature definitions. The **cost to compute** is O(N K d), and input/point states remain elsewhere. For a fixed true distribution, the characteristic function at **all** frequencies uniquely identifies its probability law; the finite list of K samples of the function does **not**. ECF also does not encode which sample belongs to which agent, its history, causal network, owner or capability.

For an illustrative role-specific decision rule (not implemented):

```math
a_i(t)\sim\pi_{\theta_{r(i)}}\left(
\,\cdot\mid o_i(t),\,m_i(t),\,g_i,\,
\widehat{\varphi}^{(r(i))}_t,\,\mathcal{N}_i(t)
\right).
~~~

Here $m_i$ is an individually scoped memory state, $g_i$ an immutable genome, and $\mathcal N_i$ a bounded local graph observation. This is **not** a proof that the signature is a Markov sufficient statistic, that agents are independent, or that grouped policy optimization converges. For strongly strategic, rare or non-exchangeable interactions, use exact local events/POSG reasoning instead of averaging.

Potential alternative: kernel mean embedding in an RKHS with a characteristic kernel, approximated by Random Fourier Features for a chosen shift-invariant kernel. This is a different embedding scheme from sampling ECF at selected frequencies, although both rely on Fourier representations; experiment against role-wise moments and histograms before introducing dependencies.

## 3. Genome, phenotype and policy weights must remain distinct

**Versioned, bounded typed genome (research proposal):**

~~~text
AgentGenome:
  role                 # explorer, builder, trader, diplomat, researcher
  policy_family        # rules, shared-mlp, external-policy
  policy_digest        # sha256 reference to reviewed policy artifact
  traits               # canonical bounded integer map (0..100)
  parent_genome_id     # content-addressed parent or null
  generation           # lineage depth
  genome_id            # canonical content SHA-256
~~~

Mathematically treat the genome as $g_i\in\mathcal G_{\mathrm{typed}}$, and phenotype/action as an environment-dependent function of *genome, policy parameters, private state and external inputs*:

```math
\mathrm{behavior}_i(t)
=\mathcal F\big(g_i,\theta_{\mathrm{role}(i)},m_i(t),
o_i(t),\mathrm{world}_t\big).
~~~

Genome and identity are separate: cloning a blueprint is **not** cloning agent ownership, consent, permissions, personal memory, or authenticity. \`policy_digest\` is only a content pointer and does not fetch, execute, verify licenses or grant code admission. The experimental \`mutate_genome\` changes one bounded trait, preserves lineage and creates a content-addressed child. **There is no fitness selection, crossover, population training or code execution** in this implementation.

Evolution lab proposals: type-checked mutations; reproducible seed; novelty/quality-diversity; safety and quota constraints; held-out environment/partner evaluation; human-approved promotion. A versioned \`World Genome\` is **separate** from agent DNA and from immutable kernel rules.

## 4. Assessment of the owner's three QID/FQID papers

| Owner source | Actually established topic | Translation to OpenWorld |
|---|---|---|
| [Lindner, Pan & Sato, arXiv:1701.02400](https://arxiv.org/abs/1701.02400), 2017 | *On quasi-infinitely divisible distributions*: Lévy–Khintchine-like characterization with a **signed quasi-Lévy measure** in 1D; related to factorization of infinitely divisible laws | Valuable probability research, **not** a required representation for game agents; signed quasi-Lévy term is not automatically a valid nonnegative event intensity |
| [Berger, Kutlu & Lindner, arXiv:2101.02544](https://arxiv.org/abs/2101.02544), 2021 | *On multivariate quasi-infinitely divisible distributions*: extension to $\mathbb{R}^d$, support/moment/weak-convergence questions | Interesting for specialized distribution modeling; no general training-scalability guarantee |
| [Hotta et al., ALEA 20, 941–971, DOI:10.30757/ALEA.v20-34](https://alea.impa.br/articles/v20/20-34.pdf), 2023 | *On freely quasi-infinitely divisible distributions*: **free** (noncommutative probability) Lévy–Khintchine-type representation and signed Lévy measure | 'Free' means free-probability theory, **not** autonomous-agent freedom; free convolution is not ordinary classical independent addition |

Classical characteristic function:

```math
\varphi_X(\omega)=\mathbb E[\exp(\mathrm{i}\omega^{\mathsf T}X)].
~~~

For **classically independent** X and Y, $\varphi_{X+Y}=\varphi_X\varphi_Y$; dependence invalidates that factorization. An empirical signature of *unpaired marginals* cannot test chronological or causal independence. QID and FQID are restrictive/specialized families, not synonyms for a universal agent distribution codec.

## 5. Why Riemann and quantum are deferred

- [Clay: Riemann Hypothesis](https://www.claymath.org/millennium/riemann-hypothesis/) concerns nontrivial zeros of $\zeta(s)$ and prime distribution; it is still unsolved. It is **not a prerequisite** for stochastic simulation, ECF, mean-field games, genome encoding or deep RL.
- Quantum machine learning and quantum-inspired tensor networks may be **optional later benchmarks** only if an explicit problem, hardware/input assumptions, classical baseline and compute budget show a tangible gain. We have no evidence of a quantum advantage for OpenWorld's local CPU agent simulation. See [Gundlach et al. (2025)](https://arxiv.org/abs/2511.01253) and QML reviews; *complex numbers in characteristic functions do not imply quantum computing*.

## 6. Falsifiable gates

1. **Representation laws:** ECF(0)=1, conjugate symmetry, norm at most 1, convolution of **independently combined empirical distributions**, validation of finite input/frequency dimensions and NaN denial.
2. **Counterexamples:** distinct distributions can share the same finite-frequency signature; permuting a time series leaves its marginal ECF unchanged. Keep exact history for sequence-dependent tasks; do not advertise lossless reconstruction.
3. **Genome law:** content IDs reproducible, typed trait bounds, one-step mutation reproducible, parent/generation consistent; no privilege/memory fields.
4. **Cost and predictive utility:** compare simple mean / role-wise mean / role-wise histogram / ECF / kernel embedding / learned low-dimensional sketch on identical tasks, budgets, seeds and holdout partner/world shifts. Report wall/CPU/RSS, feature calculation/inference latency, task reward, error, calibration and independence failures.
5. **Population and social utility:** run 30 -> 100 -> 1,000 *synthetic* active agent experiments only as capacity allows, using sparse/hub graphs, skewed role compositions and rare critical events. No large-scale claim from stored-agent count.
6. **Security:** per-agent observation privacy, no group sketch released for tiny groups, no sensitive feature leakage, and no bypass of W0/W3/W4 contracts. \`min_group_size\` alone **does not guarantee k-anonymity or differential privacy**.
7. **Promotion:** offline experiments require W2/W3/W5 reproducible results; W0 reviews any API freeze. Checkpoint replay does not authenticate exogenous observations.

## 7. Prototype and scope

The optional standard-library \`src/openworld_superkernel/population_repr.py\` module implements only: typed immutable genome blueprints with deterministic bounded mutation, finite empirical characteristic signatures and grouped population sketches. It does not import TensorFlow/PyTorch, train a model, change the trusted reducer, or require external APIs.

~~~sh
python -m unittest discover -s tests -p 'test_population_repr.py' -v
python -m unittest discover -s tests -v
python scripts/check_repository.py
~~~

**Rollback:** delete the standalone prototype and tests, and revert documentation changes. No production database migrations, releases, permissions, external model files or paid infrastructure.

## Primary references

- [Yang et al. (2018), Mean Field Multi-Agent Reinforcement Learning](https://proceedings.mlr.press/v80/yang18d.html).
- [Makkar et al. (2026), Towards Scaling Reinforcement Learning to Massive Populations: Learning Mean-Field Representations](https://arxiv.org/abs/2609.02928) (preprint, online 2026-08).
- [Muandet et al. (2017), Kernel Mean Embedding of Distributions: A Review and Beyond](https://doi.org/10.1561/2200000060).
- [Rahimi & Recht (2007), Random Features for Large-Scale Kernel Machines](https://papers.nips.cc/paper_files/paper/2007/hash/013a006f03dbc5392effeb8f18fda755-Abstract.html).
- [Lindner, Pan & Sato (2017)](https://arxiv.org/abs/1701.02400); [Berger, Kutlu & Lindner (2021)](https://arxiv.org/abs/2101.02544); [Hotta et al. (2023)](https://alea.impa.br/articles/v20/20-34.pdf).
- [Clay Mathematics Institute: Riemann Hypothesis](https://www.claymath.org/millennium/riemann-hypothesis/).
- [Gundlach et al. (2025), Quantum Deep Learning Still Needs a Quantum Leap](https://arxiv.org/abs/2511.01253).
