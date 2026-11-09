# HUMA — Hyper Universal Memory Algebra

**Status:** Research-program synthesis and mathematical specification draft v0.6 (2026-11-09).  
**Scope:** Documentation only, no runtime implementation, no benchmark, no holdout, no new GitHub Actions, and no production admission.  
**Primary repository:** OpenWorld (public). Canonical normative language: English.

## Why this directory exists

This directory consolidates the **visible ideas and decisions of the current discussion** into one auditable, bounded research program. It is an authored synthesis, **not** a complete verbatim chat transcript, an independently peer-reviewed theory, or an archival transfer from a private repository.

The program asks whether a *typed, contextual, provenance-preserving algebra of memory* can provide rigorously defined transformations, exact reconstruction where necessary, bounded retrieval and accountable revision across multiple symbolic knowledge systems. The intended application domains span formal mathematics, AI agent memory, intellectual history, and traditional symbolic systems.

**No claim is made that divination, physiognomy, numerology, astrology or other esoteric systems predict individual life events.** Mathematical representation of a belief is not evidence for its accuracy.

## Read in order

1. [01 — Research scope and intellectual history](01-RESEARCH-SCOPE-AND-HISTORY.md): where the questions came from and which scientific claims are excluded.
2. [02 — Formal mathematical core](02-FORMAL-FOUNDATIONS.md): typed memory objects, contexts, transformations, evidence, revision and exactness.
3. [03 — Provenance, DAG and reconstruction](03-PROVENANCE-DAG-AND-RECONSTRUCTION.md): semiring semantics, lemmas, resource limits, persistence and privacy.
4. [04 — Symbolic case studies](04-SYMBOLIC-CASE-STUDIES.md): I Ching, stem–branch cycles and numerology, clearly separated from empirical predictions.
5. [05 — Proof obligations and critical review](05-PROOF-OBLIGATIONS.md): established facts, proposed axioms, unproved claims, counterexamples and novelty criteria.
6. [06 — Theory-only continuation plan](06-THEORY-ONLY-ROADMAP.md): bounded writing milestones and independent review criteria without running experiments.
7. [07 — Typed contextual provenance calculus](07-TYPED-PROVENANCE-CALCULUS.md): syntax, typing, unverified traces, and elementary no-promotion proof sketch.
8. [08 — Typed syntax and denotational semantics](08-TYPED-SYNTAX-AND-DENOTATIONAL-SEMANTICS.md): precise formation rules, source valuations, witnessed context translations, conditional coherence and trace/proof separation.
9. [09 — Exact memory and information bounds](09-EXACT-MEMORY-AND-INFORMATION-BOUNDS.md): impossibility of uniformly compressing all strings, exact query-sufficiency quotient theorem and mutual-information constraints.
10. [10 — Revision, time and revocation](10-REVISION-TIME-AND-REVOCATION.md): deterministic replay, provenance availability, anti-rollback conditions and lawful deletion boundaries.
11. [11 — Compositional research theorems](11-COMPOSITIONAL-RESEARCH-THEOREMS.md): conditional positivity preservation across contexts, counterexamples, combined safety obligations and the novelty gate.
12. [12 — Unified contextual axioms](12-UNIFIED-CONTEXTUAL-AXIOMS.md): ten candidate axioms covering typed claims, provenance, exactness, event updates and witnessed translations.
13. [13 — Dynamic-query memory theorem](13-DYNAMIC-QUERY-MEMORY-THEOREM.md): a complete finite-state behavioral quotient proof, minimal exact-state bound and future-update counterexamples.
14. [14 — Guarded translation non-collapse](14-GUARDED-TRANSLATION-NONCOLLAPSE.md): proof that source-distinguishable states cannot be merged by a strong observation-preserving simulation.
15. [15 — Originality frontier](15-NOVELTY-FRONTIER-AND-THEOREM-PROGRAMME.md): explicit no-go boundaries, open research problems and critical prior-art gates.
16. [16 — Compositional product quotient baseline](16-COMPOSITIONAL-QUOTIENT-BASELINE.md): sufficient local-interface factorization conditions, full written proof and a hidden-bit interaction counterexample.
17. [17 — Coupled-context interface closure](17-COUPLED-CONTEXT-INTERFACE-CLOSURE.md): exact dynamic summary under local query/event interface certificates, dependent parity example, and explicit failure cases.
18. [18 — Principal-scoped memory and noninterference](18-PRINCIPAL-SCOPED-MEMORY-AND-NONINTERFERENCE.md): how current denial differs from future-grant distinguishability, and when declared low-view factorization protects observable results.
19. [19 — Provenance-preserving interfaces](19-PROVENANCE-PRESERVING-INTERFACES.md): exact source-renaming laws, injectivity, identity collisions and withdrawal limits.
20. [20 — Affine interface certificate](20-AFFINE-INTERFACE-CERTIFICATE.md): matrix and kernel conditions for a coupled deterministic binary model without global raw-state enumeration.
21. [21 — Critical review and next proofs](21-HUMA-N1-CRITICAL-REVIEW-AND-NEXT-PROOFS.md): theorem-status register, adversarial counterexamples, novelty obligations and publication boundaries.
22. [22 — Graph-local multi-agent certificate](22-GRAPH-LOCAL-MULTIAGENT-CERTIFICATE.md): conditional future-query preservation on dependency hypergraphs, interface-local constraints and bounded-neighborhood certificate verification.
23. [23 — Temporal authorization and future grants](23-TEMPORAL-AUTHORIZATION-AND-FUTURE-GRANTS.md): exact-memory lower bound when future grants may reveal protected content; policy rollback and declassification caveats.
24. [24 — Fan-in provenance and withdrawal](24-FAN-IN-PROVENANCE-AND-SOURCE-WITHDRAWAL.md): global source-rename faithfulness, multi-agent alias collisions, pullback availability and onward-sharing limits.
25. [25 — Graph-local theorem agenda and countermodels](25-GRAPH-LOCAL-THEOREM-AGENDA-AND-COUNTERMODELS.md): status ledger, open synthesis problems, explicit countermodels and privacy-first research gates.
26. [26 — Coarsest local memory congruence](26-COARSEST-LOCAL-MEMORY-CONGRUENCE.md): a finite descending partition refinement, written optimality proof within product-local quotients and a bounded-neighborhood checking bound.
27. [27 — Worked contract synthesis models](27-CONTRACT-SYNTHESIS-WORKED-MODELS.md): two-agent CopyX, future SwapA, attribution fan-in, future grants and coupled-state counterexamples.
28. [28 — Positive and negative refinement certificates](28-LOCAL-CERTIFICATES-AND-REFINEMENT-TRACES.md): complete local QC/EC checks, decreasing reasons for state-pair splits and restricted optimality certificates.
29. [29 — Reachable-state theorem frontier](29-CONTRACT-SYNTHESIS-OPEN-THEOREM-AND-REVIEW.md): precise open problem for coupled constraints, scopes, source identity and authorization with no novelty overclaim.

## Theory v0.6: local contract synthesis with an explicit proof baseline

Chapters 26–29 no longer merely *assume* that exact local memory interfaces are supplied. In a **finite, deterministic, full-product, fixed-contract setting**, Chapter 26 defines a descending refinement that computes the **coarsest locally admissible tuple of equivalence relations**. Chapter 28 provides a human-reviewable positive QC/EC certificate and finite negative witness chains for excluded local state pairs. Chapter 27 works through two-agent and grant/provenance examples, and Chapter 29 specifies the unresolved harder case of coupled admissibility and changing authority.

The optimality result is **restricted to product-of-local quotient abstractions**, not arbitrary global encodings or deployed storage. It follows standard congruence/partition-refinement reasoning and **is not claimed to be an original theorem**. The coupled reachable-state synthesis and privacy-aware provenance problem remains open.

**Review-only, not execution:** no tests, benchmarks, simulations, Python, Lean, CI, holdout, third-party confidential material or changes to runtime policy. The public documentation continues to exclude unrelated private research and product affiliations.

## Theory v0.5: previous milestone

Chapters 22–25 model typed **dependency hypergraphs** of multiple agents. A written finite deterministic result states that if every declared local query and event factors through authorized interface codes, then future query answers are preserved under any admitted event word. A stronger guard condition handles interface-defined cross-agent constraints. For bounded neighborhood size, verification of explicitly supplied local certificate conditions avoids enumeration of the entire global raw state space; this is a *mathematical case-count bound*, not a measured performance gain.

Future grant and revocation events are modeled separately from source-lineage support. An exact future read can force the *internal combined state* to retain distinctions currently hidden from an agent. Attributing sources across fan-in requires a globally faithful rename on the distinctions promised by the authorized query contract, not just an injective rename per sender.

**Scientific status:** the results apply known finite-state simulation, quotient, information-flow and provenance semiring reasoning. They are **not presented as a newly discovered HUMA theorem or deployed security control**. The open problem is useful certificate *synthesis*, under partial updates, time-changing authority and exact permitted attribution.

**Privacy:** no unrelated private-project references, sensitive evidence records, user identities, actual access tokens or externally private research work are imported.

**Resource freeze:** Markdown editing only; experiments, CI, simulations, benchmarks, Python, Lean, holdouts and hosted runners remain **NOT RUN**.

## Theory v0.4: previous milestone

HUMA-N1 now has a **conditional coupled-context interface-closure theorem** (Chapter 17), a **principal-scoped observability/noninterference model** (Chapter 18), exact algebraic **source-renaming and attribution** propositions (Chapter 19), and a **checkable binary-affine special case** based on matrix equalities and finite-field linear algebra (Chapter 20). Chapter 21 identifies all remaining theorem and originality obligations.

All results remain mathematical manuscript statements under declared assumptions; the techniques are largely known automata, simulation, semiring and linear algebra results and **are not claimed to be novel**. Formal security, human consent, privacy, semantic truth and empirical performance are not established.

HUMA-N1 is still open in the general setting of arbitrary partial, nonlinear, stochastic, privacy-constrained and provenance-dependent context graphs. These chapters advance its **restricted tractable formulation**, not its general solution.

**No GitHub Actions, experiments, Python, Lean, simulations, holdouts, benchmarks, private data, production changes or new runtime dependencies.**

## Theory v0.3: previous milestone

The v0.3 writing track advances from static memory to *dynamic behavioral memory*, where the declared future event alphabet matters for safe compression. It gives a finite-state quotient theorem, a guarded cross-context non-collapse theorem, and a product-factorization theorem under strong interface requirements. These are **established automata, simulation and quotient proof patterns applied to a candidate memory system**, not novel HUMA discoveries.

**Open HUMA-N1:** determine nontrivial and efficiently checkable interface certificates that let a graph of partial context transformations compose without losing future authorized query or source-provenance distinctions. HUMA-N2 concerns scoped provenance and erasure-aware authority. Neither problem is solved by these chapters.

This is a *writing-only manuscript addition*. GitHub CI, benchmark matrices, Python, Lean, simulation, holdout selection and private evidence transfer remain **NOT RUN**.

## What the new mathematical chapters establish (and do not)

- **Proved in finite abstract models, by written arguments:** lossless encoding cannot strictly compress every fixed-length source; an exact summary for a query family must distinguish its query-equivalence classes; a well-formed provenance polynomial's availability semantics respects admissible source substitutions; a trace-only calculus does not introduce a formal proof term.
- **Conditional, not deployed security:** rollback-safe revocation relies on a separately current authoritative policy history.
- **Not shown:** novel HUMA theorem, validated cross-context semantic equivalence, empirical prediction of events from traditional symbols, effective compression of real agent histories, authenticated source evidence, verified Lean proofs or production safety.

No test, benchmark, holdout, code generation, simulation or hosted CI is part of this manuscript update. The [OpenWorld hosted-workflow freeze](../../operations/RESEARCH-EXECUTION-FREEZE-20261109.md) remains in force.

## The target structure

Let C index contexts and T index memory types. A research candidate is the disjoint family

    M = coproduct over (c,tau) in C x T of M[c,tau].

A memory record may be described by (content, type, context, provenance, valid-time, recorded-time, version, evidence-status). This is **a proposed data structure**, not a result of axiomatization by itself.

The target algebra should expose the following operators with explicit domains:

| Operator | Intuition | Required qualification |
| --- | --- | --- |
| E, D | exact encode/decode | equality only for declared lossless domain |
| +, · over N[X] | alternative and joint derivation provenance | not evidence independence or truth |
| F(c,d) | context translation | partial, typed, laws required |
| join/r | relation between typed memory objects | relation not equivalence |
| project(c) | select information interpretable in a context | may be undefined |
| update(M,e) | apply a recorded update | must not rewrite accepted past |
| compress(M,q) | task-specific lossy summary | cannot replace exact protected evidence |

## Boundaries relative to OpenWorld

- Current OpenWorld execution priority remains **R0 and independent Gate #11**. This theoretical directory does not change production interfaces or reprioritize implementation.
- HyperMemory has an exact-evidence lane distinct from predictive summaries. HUMA must respect that separation.
- Any prior **private** implementation, experimental evidence or frozen archive stays private unless separately cleared for a specific public diff under rights, privacy, evidence and owner-review gates.
- OpenWorld Actions have been configured with an owner-requested hosted-experiment freeze (see [operations freeze](../../operations/RESEARCH-EXECUTION-FREEZE-20261109.md)). This directory must not re-enable CI or use hosted runners.
- No claim of mathematical novelty, string-theoretic physics, clinical relevance, socioeconomic prediction, general intelligence or production maturity follows from this document.

## Prior-art starting points

- Green, Karvounarakis, Tannen (2007), *Provenance Semirings*, PODS.
- Shannon (1948), *A Mathematical Theory of Communication*.
- Mac Lane (1971), *Categories for the Working Mathematician*.
- W3C, [PROV-O](https://www.w3.org/TR/prov-o/), provenance ontology.
- W3C, [RDF 1.1 Concepts](https://www.w3.org/TR/rdf11-concepts/), data representation.
- Belnap (1977), *A Useful Four-Valued Logic*.
- Existing OpenWorld [architecture](../../ARCHITECTURE.md), [RFC-007](../../math/RFC-007-OPENWORLD-MATHEMATICAL-FOUNDATIONS.md), [review policy](../../GOVERNANCE-REVIEW-POLICY.md) and [decision ledger](../../project/DECISION-LEDGER.md).

These are research inputs; citing them does not claim that HUMA is an established new theory.
