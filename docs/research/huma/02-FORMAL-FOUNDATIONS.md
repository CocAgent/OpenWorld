# 02 — Formal Foundations for Typed Contextual Memory

**Status:** Candidate formalization v0.1. This chapter distinguishes definitions and proposed axioms from proved mathematics.

## 1. Basic sorts

Fix:

- A set C of explicit contexts (e.g., a particular formal theory or named textual tradition).
- A set T of disjoint memory types: SOURCE, DEFINITION, FORMAL_CLAIM, HYPOTHESIS, OBSERVATION, TRADITIONAL_READING, SIMULATED and INFERRED. Each type requires separate admissibility rules.
- A set B* of finite byte strings for exact payloads.
- A set X of opaque source identifiers (not assumed to be authenticated identities).
- A totally ordered set of recorded times R, and separately a domain of valid-time intervals V.
- A set E of evidence records that may include proof objects, empirical citations, critical objections or an explicit "none" marker.

A memory item is a typed dependent record (not merely a vector):

    m : Memory(c, tau)
    m = (id, raw-or-reference, c, tau, P, valid_time, recorded_time,
         version, evidence_status, derivation_refs)

and the universe is an indexed disjoint union

    M = coproduct_{(c, tau) in C x T} Memory(c, tau).

A context identifier is **not** a truth predicate. Equal strings from distinct contexts remain distinct terms.

## 2. Typing judgments

Use a typing judgment Gamma ; c |- m : tau, where Gamma contains verified well-formedness assumptions and c selects the context. This judgment only says the record is well formed; it does not imply its proposition holds.

Define a **separate proof judgment**

    Gamma ; c |- pi : Proof(phi)

that requires a rule checker or a formal derivation under the stated axioms. The existence of a provenance polynomial cannot manufacture a term pi.

For empirical claims, use a separate assessment relation

    data, protocol |- claim : empirical_status

with explicit study design and uncertainty. This relation is *not defined* by the memory algebra.

## 3. Primitive operations and contracts

### E/D — Exact encoding and restoration

For a specified exact domain B_exact subset B*, require

    D(E(x)) = x, for all x in B_exact.

This is a reversible encoding requirement. A cryptographic digest can detect some unwanted change but is not a signature of source authenticity. Lossy embeddings or summaries are excluded from this identity.

### Alt / Joint — Provenance combination

Let the provenance of a derived claim be a polynomial in N[X]. Alternative routes combine by addition; jointly required sources combine by multiplication:

    Prov(alt(d1,d2)) = Prov(d1) + Prov(d2)
    Prov(joint(d1,d2)) = Prov(d1) · Prov(d2)

Important: the first equation is only for alternative traces of the **same claim in the same context**. The second denotes joint lineage, not proof of semantic entailment or independent probabilistic evidence.

### Translation between contexts

Let F[c,d] be a **partial typed map** for explicitly compatible portions of Memory(c,tau) to Memory(d,sigma). Its admissible domain and what it preserves must be declared. Candidate coherence requirements:

    F[c,c](m) = m
    F[d,e](F[c,d](m)) = F[c,e](m)

where *both sides are defined* and the translation contract permits composition.

If the maps satisfy all required functor laws on a suitable category, they may be organized as functors; the word "functor" must not be applied before the relevant objects, morphisms, identities and composition have been specified.

### Typed relations

Given a relation schema r : A x B -> Proposition, a relation edge (m1, r, m2) records the relation under a context and provenance. A citation relation is not an equivalence relation, and a semantic similarity edge is not a logical implication.

### Revision

A proposed event transition is

    M_(t+1) = Apply(M_t, event_t).

The event must carry a declared effect, version, authority scope, recorded time and reversible/replay metadata where applicable. Updating a claim does not rewrite earlier versions or resurrect revoked access rights. This describes a proposed model, not an already authenticated persistence system.

## 4. Evidence and paraconsistency

Different epistemic states must remain explicit:

- FORMALLY_PROVED_IN_CONTEXT: has a machine-checkable derivation under known axioms (not yet implemented).
- EMPIRICALLY_SUPPORTED: requires recorded protocol/evidence, not provenance alone.
- TRADITIONAL_INTERPRETATION: an attributed cultural interpretation.
- UNVERIFIED: claim has not passed a relevant checker.
- DISPUTED: contesting evidence or interpretations have been recorded.

A non-classical or four-valued logic (e.g., Dunn–Belnap) may distinguish support-for, support-against, both and neither. That bookkeeping needs a precise semantic algebra. It is not a numerical posterior and must not be misrepresented as probability of truth.

## 5. Memory correctness layers

Separate at least four independent guarantees:

1. **Byte exactness:** restore an original protected byte sequence, subject to authorized retention.
2. **Structural preservation:** retain declared relations and permitted compositions.
3. **Proof checking:** accept only valid derivations under an explicit theory.
4. **Empirical grounding:** show that any observational prediction matches external evidence.

Success at one level does not imply success at another.

## 6. Privacy is part of the formal domain

Authorization, erasure and retention cannot be treated as incidental implementation details. A future model should index access by principal and scope:

    Read(principal, m, t) defined only when Authorized(principal, m, t).

A mathematical object may be immutable while a personal-data payload is deleted or rendered inaccessible. Do not assert "immutable forever" for sensitive records. The present theory has not proved compliance with legal deletion, cryptographic erasure or owner isolation.

## 7. Open questions

- Can the typing and provenance rules be extended into a compositional logic without unsound "truth promotion"?
- When can a partial cross-context translation have a left inverse or preserve a chosen query family?
- What classes of updates commute, and what classes must be serialized?
- What query classes admit compact sufficient memory without exact history?

These are **unresolved research questions** until given conditions, proofs and counterexamples.
