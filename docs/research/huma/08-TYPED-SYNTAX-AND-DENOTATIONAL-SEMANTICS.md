# 08 — A Small Typed Calculus for Contextual Provenance

**Status:** HUMA-TCPC v0.2, manuscript-level definitions and hand-written proofs; no formal proof checker or machine verification.  
**Relationship to Chapter 07:** This chapter sharpens the earlier *sketch*; it does not claim to complete a universal memory theory.

## 1. Minimal domains and explicit assumptions

Let C be a set of named contexts. Every context c has a set Phi_c of proposition identifiers. Their interpretation can remain opaque: a string that names a proposition does not establish its truth.

For each c let X_c be a set of source identifiers. Require the tagged source alphabets to be **disjoint across contexts**, even where two communities use the same literal identifier (e.g. "text-42"). A source identifier denotes a citation slot, *not* authentication, reliability or permission.

A context may also have a theory T_c with a separately specified logical consequence relation; this additional structure is **not used** to interpret the provenance traces below. Do not assume a proof checker exists merely because T_c is named.

Let Tag be an explicit finite collection of epistemic classifications:

    SOURCE / TRADITIONAL_READING / HYPOTHESIS /
    OBSERVATION_RECORDED / SIMULATED / INFERRED.

The tags do not lie on one ordered scale of truth; in particular OBSERVATION_RECORDED does not imply VERIFIED.

## 2. Formation grammar

A judgment of the form

    Gamma |- t : Trace(c, phi)

means that t is a *well-formed recorded argument trace* associated with proposition identifier phi in context c.

Assume a source registry Gamma maps each pair (c,x) to a source record (tag, bytes-reference, version).

Use the following *inductive, finite* constructors:

    cite(c, phi, x)                 source x is cited for proposition phi
    joint(c, phi, rule, [t1,...,tn])    all premise traces are used
    alt(c, phi, t1, t2)            two alternative traces of identical proposition

Side conditions:

- cite requires phi in Phi_c and x in X_c with a registry entry.
- joint requires n >= 1; every ti must be Trace(c, phi_i) for some phi_i in Phi_c; phi must be in Phi_c; rule is an uninterpreted, nonempty label. No entailment check is implied.
- alt requires both traces have precisely the same context c and syntactically identical proposition identifier phi.
- Expressions are finite trees. A shared DAG may implement them, but its semantics is obtained by unfolding; cycles require additional fixed-point theory and are excluded.

**Important typing distinction:** No trace constructor has codomain Proof(c,phi), Verified(c,phi) or EmpiricallySupported(c,phi).

For illustration, cite(c,phi,x) may be well formed even if x is an inaccurate text or phi is false.

## 3. Provenance interpretation into a commutative semiring

Define K_c = N[X_c], the free commutative semiring of finite polynomials in the source identifiers of c.

Define recursively:

    P_c(cite(c,phi,x)) = x
    P_c(joint(c,phi,r,[t1,...,tn])) = product_i P_c(ti)
    P_c(alt(c,phi,t1,t2)) = P_c(t1) + P_c(t2)

The empty joint is excluded deliberately. The algebraic unit 1 exists in K_c but is not, without a separate axiom rule, an automatically true claim.

These are **definitions of annotations**, not a proof of logical correctness. A polynomial of nonzero value proves only that some syntactic lineage exists under the chosen valuation.

### Example

    t_ab = joint(c,K,"unverified-rule",[cite(c,A,a),cite(c,B,b)])
    t_c  = cite(c,K,c)
    t    = alt(c,K,t_ab,t_c)

Then P_c(t) = ab+c.

A single identifier used twice yields a^2 or 2a as appropriate; such multiplicities do not certify independence of evidence.

## 4. Valuation theorem (established algebraic consequence)

Let v:X_c -> N. By the universal property of N[X_c], v extends uniquely to a semiring homomorphism

    eval_v : N[X_c] -> N.

**Proposition 8.1 (structural soundness for annotation evaluation).**
For any well-formed Trace(c,phi) term t, recursive evaluation of its constructors with cite mapped to v(x), joint to product and alt to sum equals eval_v(P_c(t)).

**Proof.** Structural induction on t. In a cite leaf, both sides equal v(x). For joint, apply the induction hypothesis to each subterm and the homomorphism law for multiplication. For alt, apply both induction hypotheses and the addition law. These constructors exhaust the grammar. QED.

**Scope:** "soundness" here concerns equivalence of two ways to calculate a polynomial. It is **not** logical soundness of the quoted rule label or evidence validity.

## 5. Context translation as a *partial witnessed operation*

A translation witness w:c -> d contains, at minimum:

1. A partial proposition map f_w: Phi_c ⇀ Phi_d.
2. A source substitution g_w: X_c -> N[X_d] (total for the selected source alphabet, or defined only on sources actually occurring in the translated term).
3. An explicit policy obligation documenting allowed source attribution and reuse.
4. A domain D_w of source traces such that every referenced proposition has a compatible target and every referenced source has a permitted substitution.

The source map g_w uniquely extends to a semiring homomorphism

    g_w*: N[X_c] -> N[X_d].

**Proposed admissible constructor:**

    t : Trace(c,phi),  t in D_w,  f_w(phi)=psi
    ------------------------------------------------
    translate_w(t) : Trace(d,psi)

Define its provenance by P_d(translate_w(t)) = g_w*(P_c(t)).

The witness MUST NOT be construed as a proof that phi and psi are empirically equivalent. It is a declared formal correspondence and attribution rule; interpreting it as semantic equivalence needs additional independently checked conditions.

### Proposition 8.2 (conditional provenance preservation)

For every well-formed t in D_w,

    P_d(translate_w(t)) = g_w*(P_c(t)).

**Proof:** Definitional in the present model. If translation is instead implemented structurally, it follows by structural induction provided every constructor and child stays inside the declared domain and source substitutions obey the semiring laws.

**Not yet established:** that a given proposed translation is semantically faithful, lawful with respect to consent, or reversible.

## 6. Composition of translation witnesses: exact side conditions

Suppose w:c -> d and z:d -> e are translation witnesses. A valid composite z∘w is defined **only** for traces t where:

- t belongs to D_w;
- translate_w(t) belongs to D_z;
- the target proposition mapping f_z(f_w(phi)) is defined;
- the required source substitutions and attribution scope are valid at both steps.

Define on this restricted domain:

    f_(z∘w) = f_z ∘ f_w
    g*_(z∘w) = g_z* ∘ g_w*.

**Proposition 8.3 (algebraic coherence).** With these conditions,

    P_e(translate_z(translate_w(t)))
      = (g_z* ∘ g_w*)(P_c(t)).

**Proof.** Apply Proposition 8.2 twice and use function composition. QED.

This does **not** assert translate_(z∘w)(t) exists in every implementation or preserves all of t's cultural meaning. A full categorical structure requires explicit identity witnesses, associative domains and coherence of the translated propositions, not just the polynomial map.

## 7. No truth-promotion by provenance constructors

Introduce a distinct type Proof(c,phi), with terms admitted only by a separately specified rule checker:

    Check_c(pi,phi)=ACCEPT ==> pi : Proof(c,phi).

There is no coercion Trace(c,phi) -> Proof(c,phi).

**Proposition 8.4 (syntactic non-promotion).**
In the subsystem generated solely by cite, joint, alt and translate_w, no derivation can conclude t : Proof(c,phi).

**Proof.** Every introduction rule in this subsystem has result type Trace. Induction on the last rule of any derivation establishes that its conclusion is Trace, never Proof. QED.

**Countermodel to an overclaim:** A faulty checker may ACCEPT an invalid proof term. Proposition 8.4 does not certify the checker sound. Similarly, a cited real-world proposition may still be false.

## 8. Counterexamples that the syntax rejects

- **Context collision:** cite(c,"fire",x) and cite(d,"fire",x) are distinct by tagging; alt across them is undefined.
- **Proposition collision:** two traces with identifiers K and K' cannot be combined by alt merely because they share a title.
- **Unwitnessed translation:** a Chinese philosophical notion of "qi" cannot be silently mapped to SI physical energy.
- **Source spoofing:** possessing a source identifier does not certify a signed, authorized or genuine record.
- **Evidence laundering:** ten citation traces for an unverifiable numerology claim still have type Trace, not Proof or Verified.
- **Hidden inference:** joint's rule label is not a checked logical rule, so it cannot elevate a conclusion.

## 9. Precise gap to future theory

This small calculus permits **well-formed, attribution-preserving symbolic descriptions**. It does not yet have:

- a sound logic of empirical propositions;
- dependent type checking of all propositions and translations;
- proof-producing revision semantics or authorization certificates;
- a safe cross-owner permission implementation;
- a theory of cycles or probabilistic beliefs.

The next chapters treat query sufficiency, compression limits, revision and epistemic safety independently. Only after the actual new connective structure is defined can HUMA make a defensible claim of theoretical novelty.

### Related prior art

- Green, Karvounarakis, Tannen, [Provenance Semirings, PODS 2007](https://doi.org/10.1145/1265530.1265535).
- Bohannon, Pierce, Vaughan et al., [A Language for Bi-Directional Tree Transformations](https://www.cis.upenn.edu/~bcpierce/papers/lenses.pdf), for partial bidirectional transformation laws; no such laws are claimed here.
