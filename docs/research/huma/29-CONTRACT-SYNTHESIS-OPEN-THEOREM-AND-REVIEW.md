# 29 — HUMA-N1: Reachability-Aware Synthesis and the Next Theorem Frontier

**Status:** Research problem statement, scope-limited negative results and independent-review checklist. It does **not** claim an original theorem, a verified security protocol or an experimental outcome.

## 1. What Chapters 26–28 establish

For finite deterministic multi-agent networks with:

- complete Cartesian product of typed local states;
- total, precisely specified local queries and events;
- explicit read and write neighborhoods;
- a fixed query/event vocabulary;

Chapter 26 constructs the **coarsest contract-admissible product of local equivalence relations**, proves that the refinement terminates and states a bounded-neighborhood local-check complexity bound.

Chapter 27 demonstrates why future events, exact source attribution and authorized later reads can require distinctions that a currently adequate cache discards.

Chapter 28 describes human-reviewable certificates: positive local QC/EC tables and finite, decreasing negative-refinement witness chains. These results are rigorous *under the stipulated model*, but belong to the established family of congruence/partition-refinement methods.

**Do not present the results as a new universal algebra, as a solved general HUMA-N1 problem or as verified runtime protection.**

## 2. The difficult case: coupled admissible states

In many realistic agent graphs, only some Cartesian tuples of local states are valid. Let

    G subset product_(i in V) S_i

be the admissible global states and assume every admitted global event maps G to itself.

A product interface alpha=(alpha_i) is *G-exact* when:

    q(s) = q_hat(alpha(s)), for all s in G,

and

    alpha(U_e(s))=V_e(alpha(s)), for all s in G,

for each declared query q and event e, with abstract transitions defined on the reachable interface set B=alpha(G).

This is a **relative** contract. It need not be correct on impossible raw combinations outside G.

### Negative observation 29.1 — Product-local refinement need not be G-minimal

Take two bits a,b, with G={(0,0),(1,1)}, no events and the only query q(a,b)=a XOR b. On G the query is identically zero, so the constant global abstraction is exact. The unrestricted product-local refinement considers (0,1) and (1,0) and therefore distinguishes both local bits.

This demonstrates that a method complete for the full product can be over-conservative for G. It is not a new impossibility theorem.

## 3. Open research problem N1-R — Reachable local certificates

Identify a restricted, clearly represented class of coupled agent graphs (for example, bounded-treewidth compatibility constraints with typed local updates) for which there exists a certificate-synthesis procedure satisfying all of the following:

**Soundness:** Every output certificate preserves all declared authorized observations after every admitted finite update word on G.

**Relative completeness:** If there is an exact product-of-local-quotients abstraction from a specified finite grammar satisfying a stated memory bound, the procedure finds one; otherwise it supplies a verifiable obstruction relative to that grammar.

**Locality and resource theorem:** The construction and checking costs are bounded using the graph/tree decomposition width, local alphabet sizes, event/query neighborhood widths, and the size of source/policy annotations—not by a hidden enumeration of all G.

**Source and authority typing:** Distinguish exact source identity, semiring provenance support, valid proof terms and current principal authorization. Retain only the identity distinctions required by the authorized observation contract and lawful retention policy.

**Temporal scope:** State whether grants, source withdrawals, erasure, concurrent updates and policy rollback are admitted events. A theorem for a horizon excluding them must not imply coverage of those events.

This is an **open research target**. Bounded graph width alone is not a proof of tractability for arbitrarily encoded updates and global questions. Interface discovery may be more expensive than contract checking or may require preserving nearly all raw state.

## 4. A deliberate limitation on 'smallest memory'

There are three different optimization targets:

1. minimum count of **local quotient classes** subject to a fixed product representation;
2. minimum count of **reachable global abstract states** over G;
3. minimum total operational storage, including exact originals, policy metadata, source attribution, index tables and audit trails.

Chapter 26 proves an optimality property for the **first** target on the full-product model. It does not solve the second on arbitrary coupled G or the third on any deployed system.

A mathematical lower bound on the number of abstract state codes does not equal a measured disk/RAM reduction.

## 5. Mandatory adversarial examples for the next paper

A future proof must explicitly address, or exclude with clear assumptions:

- an event that reads a raw bit outside its declared neighborhood;
- a global guard dependent on source bytes absent from local interfaces;
- a current Denied read that later becomes Value after an authorized grant;
- a revoked capability reintroduced by restoring stale policy;
- two source owners whose identifiers collide at fan-in;
- an intermediate translation that is algebraically valid but violates onward-sharing consent;
- exact historical content removed under lawful erasure;
- a new query introduced after the abstraction was fixed;
- nonlinear or nondeterministic events outside the finite deterministic model;
- an agent-generated argument trace incorrectly promoted to a verified proof.

A successful theorem must make these cases impossible under its hypotheses, produce a counterexample, or honestly narrow its domain.

## 6. How to justify originality

Before any claim that HUMA-N1-R is new, examine and compare precise statements with:

- Myhill–Nerode / deterministic automata minimization;
- partition refinement and abstract interpretation;
- assume–guarantee verification;
- compositional and symbolic model checking;
- finite constraint-satisfaction problems and tree decompositions;
- provenance semirings and annotated relational databases;
- typed partial bidirectional transformations;
- information-flow noninterference and declassification;
- versioned authorization, erasure and rollback security.

A new *terminology* or a familiar theorem rewritten for agents is not sufficient for an original mathematics claim. A publishable contribution would need a genuinely different structural condition, constructive algorithm, proof or lower bound that survives critical prior-art review.

## 7. Suggested writing-only next manuscript structure

Working title:

**Local Memory-Contract Refinement for Typed Multi-Agent Systems: A Finite-State Baseline**

1. Typed operational semantics of agents and exact observation contracts.
2. Coarsest product-local congruence and its written proof.
3. Positive and negative refinement certificates.
4. Coupled-state over-refinement counterexample.
5. Scoped provenance and authorization as explicit dependent query/event signatures.
6. Candidate reachable-graph certificate theory, with no novelty claim until proved.
7. Adversarial examples, limits and independent bibliographic review.

No article submission, experimental measurement or release is authorized here.

## 8. Privacy and resource restrictions

No unrelated confidential project names, conference affiliations, private experiments, credentials, personal identifiers or restricted source data belong in this public folder.

The OpenWorld Actions freeze remains in force. **NOT RUN:** Python, Lean, unit tests, model training, simulations, benchmarks, holdout checks, CI and any hosted compute.

The intended next step is independent review of the **written mathematics**, not execution.
