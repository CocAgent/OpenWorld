# 05 — Proof Obligations, Counterexamples and Novelty Gate

**Status:** Critical mathematical review checklist. No new theorem has been proved or independently reviewed.

## 1. Classification of propositions

| ID | Statement | Epistemic classification |
| --- | --- | --- |
| K-01 | A six-bit set has 64 states and its hypercube has 192 undirected edges | Established finite combinatorics |
| K-02 | Simultaneously stepping modulo 10 and 12 has period 60 | Established modular arithmetic |
| K-03 | Deterministic functions obey the data-processing inequality | Established information theory under standard assumptions |
| K-04 | N[X] is a commutative semiring with + and multiplication | Established algebra |
| K-05 | DAG evaluation equals expression-polynomial evaluation | Elementary structural-induction result |
| H-01 | A typed contextual provenance system can be made interoperable with no illicit evidence promotion | Proposed formal-system design; needs definitions and proof |
| H-02 | A bounded shared provenance DAG improves storage or latency on OpenWorld workloads | Empirical hypothesis; **not tested here** |
| H-03 | Exact source memory plus task-limited summaries can improve agent decisions under resource constraints | Empirical hypothesis; **not tested here** |
| H-04 | A new compositional theory beyond existing semirings and categorical databases can be isolated | Open novelty question |
| H-05 | This theory explains physical string dynamics, hidden forces or human destiny | **Not supported** |

## 2. Theorem candidate A — No illegal evidence promotion

### Desired formulation

Let the allowed constructors for claims be well-typed operations with explicit output-evidence rules. Suppose no constructor maps an UNVERIFIED, TRADITIONAL_READING or INFERRED input to FORMALLY_PROVED_IN_CONTEXT without a checked proof term of the required type.

Then every well-formed output claimed as formally proved must have an admissible proof derivation from the relevant axioms.

### Proof obligation

Specify an actual inductive syntax for proof terms and the constructor-level invariant, then use induction on construction. Without defining the checking relation and its soundness with respect to chosen semantics, this is only a **design requirement**, not a proved theorem.

### Counterexample to prevent

A trace of source names "a*b+c" survives withdrawal, so software automatically changes evidence status to VERIFIED. This is unsound: source availability is not proof validity.

## 3. Theorem candidate B — Context preservation under composition

Let F(c,d) and F(d,e) be partial typed translations with explicit domain and preservation predicates. The desired property is:

    whenever m lies in the domain of both successive translations,
    TargetType(F(d,e)(F(c,d)(m))) agrees with the declared type
    of the composite F(c,e)(m).

This depends on coherent typing and compatibility laws. If a translation drops meaning or changes a proposition, the composite may be undefined. The appropriate setting might be a category of partial maps or a bicategory with explicit refinement data; selecting it requires a worked construction and counterexamples.

### Counterexample to prevent

Two schools use the same word "energy"; a translation silently identifies a philosophical symbol with SI-measured physical energy. This is not justified by common spelling.

## 4. Theorem candidate C — Revision safety and trace dependency

Define a version-indexed provenance graph G_t, an authorization set A_t and a typed update e_t. Require:

- recorded versions are not silently overwritten;
- a source withdrawal triggers reevaluation of affected recorded paths;
- restoring a snapshot never restores a privilege whose revocation occurred later;
- independent valid paths remain traceable.

Prove dependency-reachability correctness relative to an explicit transition semantics. This is not just a database history property; security authorization is an additional logic. In particular, a hash and append-only log do not prove authentic consent or lawful erasure.

### Counterexample to prevent

Restore an earlier database snapshot that included a revoked capability; the application starts honoring the old capability again. A sound revision model must reject this.

## 5. Theorem candidate D — Bounded exactness

Let a lossless format have a decoder that either returns exact bytes or emits an explicit failure. For all accepted inputs inside the supported domain:

    D(E(x)) = x.

When serialization or evaluation hits a resource bound, it must reject rather than silently return an approximation labelled exact. Formalize the resource model: DAG node count, fan-in, serialized bytes, maximum coefficient bits, nesting depth and allowed evaluation time.

A lossy projection can only promise bounded error relative to an explicitly specified query distribution and loss function; it cannot guarantee every historical fact is recoverable.

## 6. Proof checking and prior art

A detailed mathematical manuscript should distinguish:

- **Definition:** introduces notation and objects.
- **Proposition:** a statement with a complete proof or reference to established mathematics.
- **Conjecture:** explicitly unproved, with assumptions and plausible counterexamples.
- **Experiment proposal:** hypothesis and baselines, not a result.
- **Historical assertion:** attributed to a source rather than derived mathematically.

Before claiming novelty, compare with semiring provenance, event sourcing, typed knowledge graphs, categorical data integration, bidirectional transformations, sheaves, proof-carrying data and paraconsistent logic. The distinct contribution must survive a hostile prior-art review.

## 7. What counts as progress without experiments?

Permitted now:

- complete syntax and denotational semantics;
- constructively specified example derivations;
- hand-checked lemmas and proof sketches;
- adversarial logical counterexamples;
- literature comparison and bibliographic verification;
- written specification for future Lean 4 proof obligations.

Not permitted under the current freeze without a separate decision:

- running a benchmark or holdout;
- generating simulation outputs or fitting models;
- enabling CI, scheduled workflows or hosted GPUs;
- turning private experimental results into public evidence;
- claiming independent formal verification without an actual checked proof.

## 8. Reviewer questions

1. Are our objects and morphisms well-defined, or just suggestive metaphors?
2. Is every semantic promotion protected by an explicit inference rule?
3. Are exactness, provenance, authenticity and permission distinct?
4. Does each proposed theorem state all side conditions?
5. What simple existing model offers the same capability?
6. Can a critic build a counterexample where the model gives an invalid answer?
7. Which claim remains worth publishing if all divination hypotheses are false?

If we cannot answer these, the proper status is *research idea*, not accepted theory.
