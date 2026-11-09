# 11 — Compositional Preservation: A Written Theory Review

**Status:** HUMA written mathematics v0.2. This chapter provides elementary conditional propositions, proof arguments and concrete failures. None has been independently peer reviewed or machine checked, and no mathematical novelty is claimed.

## 1. The separation principle

HUMA begins from a separation of four semantics:

    (A) traces/source lineage
    (B) formal proof or empirical validation
    (C) current source availability and authorization
    (D) exact or query-bounded data reconstruction.

An algebraic operation on (A) must not silently establish (B), and correct byte reconstruction in (D) does not grant authorization in (C).

This is a **design principle**; its usefulness depends on future implementation, review and operational boundaries.

## 2. Cross-context positive support: precise statement

Take contexts c,d with tagged source alphabets X_c, X_d.

Let w:c -> d be an admissible *partial* translation witness on a particular trace t. Let

    h_w : N[X_c] -> N[X_d]

be the semiring homomorphism induced by substitutions of source variables. Let A_d subset X_d be the set of available and permitted target source identifiers for a specific query scope. Define

    gamma_w,A(x) = ev_(A_d)(h_w(x)) in N

and the induced availability set

    A_c^w = {x in X_c | gamma_w,A(x) > 0}.

### Proposition 11.1 (positive provenance compatibility)

For every finite polynomial P in N[X_c],

    ev_(A_d)(h_w(P)) > 0
       iff ev_(A_c^w)(P) > 0.

**Proof.** Homomorphism composition gives

    ev_(A_d)(h_w(P)) = eval_gamma(P).

Every gamma(x) is a nonnegative integer. On nonnegative sums/products, positivity is preserved by replacing each gamma(x) with the indicator 1_{gamma(x)>0}: a finite sum is positive iff at least one summand is positive, and a finite product is positive iff every factor is positive. Structural induction on the polynomial expression therefore gives

    eval_gamma(P)>0
       iff eval_indicator(P)>0.

By construction the indicator valuation equals ev_(A_c^w) on generators, establishing the equivalence. QED.

**Interpretation:** A syntactically admitted translation is compatible with the *existence of recorded derivation paths*, relative to the induced source-availability set. It does not prove that target source records are authentic or that the original and translated propositions have the same real-world meaning.

### Why extra policy conditions are necessary

Without a constraint on h_w, mapping a source x to constant 1 would make x appear supported even with no target source. A stronger **source-grounded translation policy** should require each h_w(x) to have zero constant term and an authorized, inspectable source lineage. Even that is insufficient to guarantee non-conflation of distinct source identities.

**Conflation counterexample:** h_w(x)=z and h_w(y)=z. Two distinct sources collapse into one. Positive availability can still be preserved in the induced sense, while a query asking "which original source was cited?" becomes impossible to answer from the translated polynomial alone. This is the exact-summary obstruction of Chapter 09.

## 3. A no-promotion property under translation

Suppose the only constructors allowed for a term t are the Trace constructors in Chapter 08, including translate_w. Suppose the type checker has **no coercion** from Trace(c,phi) to Proof(c,phi), and the only proof constructor requires a separate accepted proof certificate.

### Proposition 11.2 (traces remain traces)

Every expression constructed from these trace constructors is of some type Trace(c,phi), never Proof(c,phi), unless a different, explicitly checked proof-introduction judgment has been applied.

**Proof.** Induction on the formation tree. Every base citation produces Trace. Every joint, alt and witnessed translation has Trace as result type whenever well formed. No constructor in the fragment concludes Proof. QED.

**Limit:** This is a syntactic non-escalation property. It does not establish the soundness of a future proof verifier, the authenticity of a document, or the correctness of a divination prediction.

## 4. A combined, deliberately modest preservation statement

Consider:

- a well-typed trace t in context c;
- an admissible witness w:c -> d;
- finite provenance P_c(t);
- a currently authorized target source set A_d;
- an **independent** exact-source store whose decoder satisfies D(E(x))=x for retained x;
- a **separate** current authorization check for any source read.

Then, as long as these assumptions hold:

1. The translated trace's recorded path availability is consistent with induced availability by Proposition 11.1.
2. Trace constructors cannot produce a formal proof merely from their lineage by Proposition 11.2.
3. The exact-store decoder reconstructs retained permitted bytes by its *declared* round-trip requirement.
4. Unauthorized reads must be refused by the external authorization check, not by provenance arithmetic.

This conjunction is a *conditional design consistency claim*. It is not a newly proved safety theorem for an actual agent or database: assumptions 3 and 4 explicitly require correct implementations external to the algebra.

## 5. Where the real research challenge lies

The existing results above are assembled from familiar algebraic facts. The more interesting **open** problem is to define a nontrivial calculus in which:

- source-preserving but possibly partial translations carry typed **proof obligations**;
- updates and revocations modify the permitted observations while retaining authorized historical citations;
- exact and approximate memory views are linked by declared query families;
- compositionality and privacy are expressed without assuming irrevocable eternal storage;
- the resulting theory has a genuinely new theorem, rather than a collection of design requirements.

One possible mathematical object is an indexed family of partially ordered observation spaces O_(c,p,t) over context c, principal p and time t, with partial translation morphisms, exact-source projections and provenance annotations. It remains an **unformalized candidate** until all orders, maps and diagram commutation requirements are defined.

## 6. Category-theoretic direction, with explicit caution

A prospective diagram may represent:

    Trace(c,phi) --F_w--> Trace(d,psi)
        | P_c                  | P_d
        v                      v
       N[X_c] ----h_w---->    N[X_d]

The square commutes for the *defined provenance semantics* of Chapter 08:

    P_d o F_w = h_w o P_c

on the witness's admissible domain.

This square alone is neither a categorical equivalence nor evidence of any physical relation between traditional symbolism and string theory. If maps are partial, one needs a correct category of partial maps or a suitable enriched setting, along with a consistent treatment of domain restriction.

Potential use of sheaf theory to glue local interpretations remains speculative until a precise site, presheaf, restriction maps and gluing axioms exist.

## 7. Negative cases for reviewers

| Invalid leap | Mathematical or epistemic blocker |
| --- | --- |
| "Polynomial is nonzero, therefore the claim is true" | Nonzero provenance denotes recorded paths only |
| "Two identical citations are two independent studies" | Multiplicity is not statistical independence |
| "A translated symbol preserves every cultural meaning" | Context maps are partial and need semantic witnesses |
| "A hash proves an event really happened" | Integrity checks are not authenticity certificates |
| "A short vector can answer every exact-history query" | Query-sufficiency equivalence lower bound |
| "Rollback of a snapshot also safely rolls back access" | External monotonic authority must remain current |
| "String diagrams imply physical superstring theory" | Distinct mathematical and physical objects |

## 8. Peer review and publication gate

Before any research-paper novelty claim, require:

1. Full comparison with semiring provenance and K-relations.
2. A formal equivalence/non-equivalence comparison with existing typed/categorical data migration.
3. A detailed argument why proposed temporal authorization semantics are not merely standard event sourcing with policy checks.
4. At least one theorem with assumptions and a proof that is not immediate from definitions or an existing result.
5. Independently verified bibliography and explicit countermodels.
6. Separate empirical evaluation if making *performance* claims; **not authorized under the current resource freeze**.

The current record supports advancing a conceptual manuscript, not a claim of a novel fundamental law.

## Sources

- T. J. Green, G. Karvounarakis and V. Tannen (2007), [Provenance Semirings](https://doi.org/10.1145/1265530.1265535).
- W3C, [PROV-O](https://www.w3.org/TR/prov-o/), for interoperable record descriptions.
- [OpenWorld mathematical research RFC-007](../../math/RFC-007-OPENWORLD-MATHEMATICAL-FOUNDATIONS.md) and [architecture invariants](../../ARCHITECTURE.md).
