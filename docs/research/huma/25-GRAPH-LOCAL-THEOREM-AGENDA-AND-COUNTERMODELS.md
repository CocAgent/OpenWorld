# 25 — HUMA-N1 Review Ledger and the Unproved Graph-Local Theorem Agenda

**Status:** Critical theory checkpoint after Chapters 22–24. All mathematical work is written, not machine checked; no experiments or implementation are authorized. **No claim of a novel theorem or new fundamental physics.**

## 1. The central mathematical question is now explicit

An interconnected multi-agent memory system has four distinct layers:

    M = (raw/source history, attributed trace graph,
         exact or task-limited interface views, current authority).

Agents may exchange claims or compressed memories, but the system should not infer source authenticity from a hash, truth from a citation, or authorization from an algebraic rename.

The immediate theoretical question is:

> Under what **locally checkable** conditions can typed, partially shared memories remain exact for a declared set of future authorized observations and updates, including source withdrawal and changing permissions?

The goal is not to represent everything in a constant-size embedding. An exact restoration contract for arbitrary original bytes has the information lower bounds derived in Chapters 09 and 23.

## 2. The theorem-status ledger

| ID | Mathematical statement | Status | Location |
| --- | --- | --- | --- |
| HUMA-B1 | Fixed query/update family admits a minimal dynamic observation quotient | Established automata-style argument | Ch. 13 |
| HUMA-B2 | A strong witnessed translation cannot collapse source-distinguishable states | Established simulation argument | Ch. 14 |
| HUMA-B3 | Product quotients compose under query/event factorization | Conditional baseline | Ch. 16 |
| HUMA-B4 | Interface closure preserves future queries in coupled finite systems | Conditional baseline | Ch. 17 |
| HUMA-B5 | Affine local-interface consistency can be checked using finite-field matrix equalities | Conditional linear-algebra baseline | Ch. 20 |
| HUMA-B6 | A graph-local certificate implies future-query preservation, with a bounded-neighborhood check count | Conditional compositional abstraction baseline | Ch. 22 |
| HUMA-B7 | Future exact grants require payload distinctions to remain in the *combined internal state* | Elementary dynamic observation lower bound | Ch. 23 |
| HUMA-B8 | Rename-only fan-in is faithful exactly when the combined source rename is injective | Elementary semiring and finite-set algebra | Ch. 24 |
| HUMA-N1 | Sound **and constructively useful** certificate synthesis for partial, typed and permission-changing graph interactions | **Unsolved** |
| HUMA-N2 | Erasure-aware provenance and scoped sharing without forbidden source-identity retention | **Unsolved** |

Even where a proof is supplied, independent mathematical critique and exact prior-art review remain pending. A condition stated as an assumption is not an experimentally established feature of the OpenWorld runtime.

## 3. An explicit candidate formal theorem to investigate — not proved

Define a *principal-indexed source-aware contract network* by:

1. A finite directed hypergraph whose vertices are typed agent contexts and policy services.
2. A local raw state and an interface code space at every vertex.
3. Partial events with **explicit typed error results**, each declaring all data/policy/source dependencies and source/target scopes.
4. Per-principal observation families with Denied, Unavailable and Value outputs.
5. Context-tagged source alphabets and trace provenance over commutative semirings.
6. A source withdrawal, grant and revocation event vocabulary with versions/epochs.
7. Local interface proofs for query and event closure and a separate authority assumption.
8. Explicit exact-retention and erasure obligations for protected source bytes.

### Open problem N1-G

Find a nontrivial structural class K of such networks and a *certificate synthesis procedure* Synth satisfying:

**Soundness:** If Synth returns a certificate, every declared authorized query agrees between the raw system and the abstract system after every admitted finite event sequence, including specified source withdrawal and policy changes, and the exposed provenance preserves the identity distinctions promised by that principal's query contract.

**Declared completeness:** For a precisely defined subclass K, Synth either returns a certificate whenever one exists within a bounded interface grammar, or reports an explicit counterexample or a proof of nonexistence in that grammar.

**Complexity:** Prove a construction and checking bound on a stated input representation that improves over full global-state enumeration for a specified growing family of networks, including the cost of policy and provenance interface sizes.

**Nontriviality:** Demonstrate a case outside simple independent products or a direct restatement of linear-algebra factorization, and compare with established compositional verification, symbolic model checking, data abstraction, assume–guarantee contracts and data lineage systems.

This is a **research problem**. It could be false without strong structural restrictions. Bounded degree or a tree-shaped dependency graph alone does not ensure that a useful small interface exists.

## 4. What counts as an interface contract?

Every written certificate should contain:

    Context-ID, Owner/Principal, Policy-Epoch,
    Read-Neighborhood, Write-Neighborhood,
    Query-Signature, Event-Signature,
    Source-Alphabet and Scope,
    Current-Authorization Obligation,
    Provenance-Map and Identity Rule,
    Exact-Retention / Erasure Contract,
    Failure/Denied/Unavailable Semantics,
    Proof/Counterexample References.

These are **abstract type and proof fields**, not a request to publish real owner identifiers, private source IDs, access tokens or operational secrets.

A public review of such a certificate should include only synthetic labels and the general mathematical contracts. Any real authorization details, raw source history, actual customer data or private research datasets remain outside the public repository.

## 5. A formal countermodel checklist

Before accepting a purported general theorem, test it **on paper** against these countermodels:

1. **Cross-neighborhood hidden read:** an event uses a state component absent from its declared source neighborhood (violates locality).
2. **Future grant:** previously Denied payloads become distinguishable after an authorized policy event (breaks small current-only summaries).
3. **Rollback:** a restored old policy epoch reactivates a revoked capability (authority assumption fails).
4. **Fan-in alias:** two independent source owners both map distinct citations to the same target source label (attribution collapses).
5. **Unapproved forwarding:** algebraic source renames compose across two transfers but a permission scope denies the second transfer.
6. **Undeclared source query:** a newly added provenance query requires a version/source distinction that the interface discarded.
7. **Global guard leak:** a compatibility condition depends on hidden raw bytes rather than the declared interfaces.
8. **Expanding evidence path count:** a provenance DAG is compact but expansion to an exact polynomial blows up in size; ignore neither representation nor arithmetic costs.
9. **Claim-type laundering:** repeated cultural or model-generated traces are treated as independently verified proof.
10. **Lawful erasure:** an archived exact source was correctly deleted, but a proposed "universal memory" theorem promises it can still be restored.

A correct theorem must exclude, detect or deliberately incorporate these behaviors. Merely changing variable names will not eliminate a counterexample.

## 6. Bibliographic and novelty challenge

The following are not interchangeable fields, but all are relevant prior art:

- deterministic automata minimization and behavioral quotients;
- simulation/refinement and compositional verification;
- assume–guarantee contracts and abstract interpretation;
- noninterference, declassification and data erasure;
- database provenance semirings and provenance circuits;
- capability security, current authority epochs and versioned state;
- finite-domain constraint satisfaction and dependency-graph decomposition.

Recent work also formalizes provenance semantics directly in Lean 4; introducing Lean syntax or a provenance polynomial is not by itself a new scientific result. See the freely described research release at https://zenodo.org/records/22900284 and the classical provenance paper at https://www.cs.ucdavis.edu/~green/papers/pods07.pdf. These references are included for a **prior-art check**, not as imported code or authority for a HUMA novelty claim.

## 7. The next written-only manuscript section

A useful next phase, without experiments, is a restricted model of **policy-scoped graph-local contract synthesis** with:

- a fixed finite grammar of interfaces;
- an explicit, independently specified owner/permission event semantics;
- a cost model for certificate size and retained exact source references;
- a proof of either a positive restricted result or a negative lower bound;
- a systematic reduction to or distinction from known algorithmic problems.

Only after complete proofs and independent review should one discuss a novel HUMA theorem. Real-world security and empirical performance would require separate engineering, rights and cost approvals, and are intentionally not addressed by this manuscript.

## 8. Publication and privacy boundary

This document deliberately contains no private cross-project affiliations, conference planning information, actual identities, protected source identifiers, raw records, API secrets or unreviewed experimental results.

OpenWorld's hosted research workflow remains frozen. No Python, Lean, CI, benchmarks, simulations, experiments, holdouts or production code are part of this work.
