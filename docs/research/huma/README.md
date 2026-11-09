# HUMA — Hyper Universal Memory Algebra

**Status:** Research-program synthesis and mathematical specification draft v0.1 (2026-11-09).  
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
