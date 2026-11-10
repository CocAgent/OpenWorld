# 34 — PCMM v0.8: Theorem Ledger, Critical Review and Next Written Research Gates

**Status:** Human-readable review dossier. Manuscript theorems have not been independently peer-reviewed or machine-checked. This directory remains public *conceptual mathematics only*, without private project data or deployed security claims.

## 1. The three-track research decision

**PCMM-A — Exactness in coupled state spaces:** determine whether a **candidate** memory interface is correct for all admitted reachable states, event requests and principal-scoped queries.

**PCMM-B — Scoped provenance and authority:** make source attribution, path availability, formal proof status, current authorization and legally retained exact bytes distinct components of the contract.

**PCMM-C — Restricted constructive synthesis:** search a declared finite grammar of candidate interfaces, with honest bounds on the verification cost and the number of candidates.

These tracks form an increasingly demanding program, not three already-solved general problems.

## 2. Precise results and caveats

| ID | Statement | Status | Proof location |
| --- | --- | --- | --- |
| PCMM-30.1 | Surjective interface factorization iff two kernel inclusions | Elementary quotient/factorization theorem | Ch. 30 |
| PCMM-31.1 | A candidate interface is exact on G iff all exact closure/query/event obstruction CSPs are unsatisfiable | Conditional finite-state theorem | Ch. 31 |
| PCMM-31.2 | Exact interface factorization preserves every declared finite future event-word observation | Standard induction | Ch. 31 |
| PCMM-32.1 | Future authorized exact grants require retaining internal payload distinctions | Elementary dynamic observation lower bound | Ch. 32 |
| PCMM-32.2 | An allowed source-attribution query cannot factor through an abstraction that merges its distinct outputs | Elementary contradiction | Ch. 32 |
| PCMM-32.3 | Modeled principal-scoped outputs agree between raw and abstract system under a complete declared contract | Conditional behavioral-preservation theorem, **not** a security proof | Ch. 32 |
| PCMM-33.1 | An explicitly finite grammar admits exhaustive, cost-minimal candidate search under a correct decision oracle | Standard finite enumeration | Ch. 33 |
| PCMM-33.2 | Arbitrary refinement of an exact memory interface can destroy event-compatibility | Explicit two-bit counterexample | Ch. 33 |
| PCMM-N1-OPT | General useful locally compositional synthesis for coupled source-/policy-aware graphs | **Open, not proved** | Ch. 33 |

All results marked as theorems are **hand-written under stated assumptions**. Their mathematical novelty is **not** established. Prior-art identification is mandatory before considering publication.

## 3. The most important complexity correction

Bounded treewidth of the **original** agent graph does not alone imply easy exactness verification. The actual counterexample question can duplicate source states, join principal views, compare query outputs, and connect provenance or policy nodes that were not adjacent in the raw graph.

Therefore any tractability claim must state a width bound for the **augmented witness CSP**, with a supplied decomposition and an accounting of constraint representation costs.

If the candidate family contains R choices and checking one candidate costs T, an enumerative synthesis approach costs roughly R*T. The factor R may be exponential in the number of agents even when T is polynomial for fixed CSP width. It is inaccurate to present the tractability of verifying one candidate as tractability of finding the globally best one.

A future paper must treat the query/event vocabulary and authorized future horizon as part of its **input**, rather than choosing them after seeing the result.

## 4. Necessary assumptions that must appear in theorem statements

1. **Finite, nonempty admissible state set:** G is specified and constraints are meaningful; an empty G makes preservation vacuous.
2. **Totalized, deterministic transitions:** rejected actions have explicit outcomes and no hidden writes.
3. **Correct dependency scope:** all reads, writes, policy checks, source identity and external effects required by the contract are included.
4. **Declared fixed vocabulary:** a new grant, source-identity query or data-restoration operation changes the contract.
5. **Exact CSP encoding:** negative witness satisfiability matches genuine raw counterexamples; an approximate encoding cannot certify exactness.
6. **Source and type separation:** Trace, Proof, Observation, source availability and current authorization are distinct.
7. **Protected exact source lane where required:** lawful erasure must be honored; a public summary cannot promise arbitrary exact restoration without the retained information.
8. **Explicit resource accounting:** the width of the augmented two-copy CSP, number of grammar candidates, local domain sizes and protected archive costs are distinct.
9. **No automatic confidentiality inference:** agreeing with an insecure raw access policy is not proof of security.
10. **Independent critique before novelty claims:** published equivalent methods may already prove the central proposition.

## 5. High-value mathematical countermodels

**C1 — Coupled-only exactness.** G={(0,0),(1,1)}; q=a XOR b; the constant interface is sufficient on G but not on the full product.

**C2 — Safe quotient versus unsafe refinement.** A constant summary is compatible with a constant query and event U(x,y)=(y,y); the supposedly more informative beta(x,y)=x is not update-congruent.

**C3 — Future lawful disclosure.** Two payload states currently Denied become distinguishable after an admitted Grant and exact read. A public Denied-only cache is not the complete internal exact state.

**C4 — Fan-in source collision.** Distinct source names from different agents both map to a single target alias. Algebraic support may survive, while separate exact source-attribution queries fail.

**C5 — Policy rollback.** A restored data snapshot contains an old grant. If the authoritative policy also rolls back, the mathematical memory abstraction may reproduce an insecure result exactly.

**C6 — Joint observation leakage.** Separate views r and h XOR r do not individually determine h over all possible masking values, but their coalition computes h by XOR.

**C7 — Width inflation.** A low-width raw dependency graph produces a larger-width obstruction CSP once two copies, equality joins and policy/provenance comparisons are included. No low-width verification bound follows without an augmented-graph argument.

A future theorem must exclude, directly model, or yield a counterexample for each relevant case.

## 6. Next proof problem: go beyond exhaustive search

**PCMM-N1-OPT (formal research question):**

Find a nontrivial graph-constrained class K of finite, typed, provenance-aware and time-scoped agent systems, with a finite candidate-interface grammar, for which there is a *compositional synthesis* procedure that:

1. produces an exact, minimal-cost interface according to an **explicit** code and metadata cost model, or an auditable unsatisfiability/optimality certificate;
2. preserves all declared reachable-state observations under all declared future events;
3. preserves exact source identities *only where required* by the named principal-scoped query contract and separately enforces a current-authority assumption;
4. runs with an analyzed bound significantly better, for a growing stated input family, than enumerating every global raw state **and** every Cartesian combination of interface candidates;
5. has a detailed prior-art analysis and counterexamples showing exactly which structural assumptions matter.

There may be no such theorem without stronger restrictions. A negative complexity result or a restricted positive construction is an acceptable research outcome.

**Proposed first restricted case:** finite local state alphabets; extensional constraints of bounded **augmented** treewidth; deterministic totalized operations; explicitly modeled grant/revoke outcomes; rename-only provenance with typed identity tags; and a small graph-local interface grammar. The difficulty is still in **synthesizing** compatible interfaces and measuring the true width/cost, not in restating classical CSP evaluation.

## 7. Literature review gate

Before a scientific novelty claim compare precise theorem statements, not just keywords, against:

- Freuder's bounded-treewidth CSP methods (1990) and later parameterized-CSP results;
- finite automata minimization, relational congruences and abstract interpretation;
- assume–guarantee reasoning and compositional verification;
- semiring provenance, data lineage and provenance circuits;
- dynamic information-flow policy, erasure, declassification and revocation;
- compositional privacy and coalition observations.

Starting references:

- https://research.ucc.ie/en/publications/complexity-of-k-tree-structured-constraint-satisfaction-problems/
- https://www.cs.bme.hu/~dmarx/papers/marx-stacs2013-tutorial.pdf
- https://doi.org/10.1109/CSF54842.2022.9919639
- https://doi.org/10.1109/CSF.2008.12
- https://www.cs.ucdavis.edu/~green/papers/pods07.pdf

No references here authorize copying proprietary code, using private studies or treating symbolic traditions as scientific predictors.

## 8. The publication and resource boundary

The next deliverable is an internally coherent, human-reviewed *mathematics manuscript*, not a claim that this theory has been experimentally confirmed. A separate decision would be required to run a proof assistant, benchmarks, holdout tests or any hosted workflow.

**NOT RUN:** Python, Lean, automated tests, simulations, bench experiments, model tuning, holdout selection, cloud GPU, scheduled or manual CI.

**Privacy:** The dossier contains no unrelated confidential project names, human data, private source records, hidden research artifacts, credentials or private research affiliations. Future publications require separate source-rights and disclosure review.

**Recommended decision:** Keep the theory program centered on proving or refuting PCMM-N1-OPT under a genuinely restricted coupled graph model, and retain Draft PR review gates until independent critique is complete.
