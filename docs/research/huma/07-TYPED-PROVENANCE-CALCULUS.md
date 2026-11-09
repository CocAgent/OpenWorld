# 07 — Typed Contextual Provenance Calculus: First Formal Sketch

**Status:** Candidate calculus HUMA-TCPC/0.1. No executable proof checker, no mechanized proof and no claim of novelty.

## 1. Judgment forms

We distinguish four judgments:

1. Gamma |- c : Context — a named admissible context exists.
2. Gamma |- s : Source(c,tau) — s is a source record with kind tau.
3. Gamma |- t : Trace(c,phi) — t is a recorded argument **about** proposition phi in context c, with no implication that phi is true.
4. Gamma |- pi : Proof(c,phi) — pi is a valid proof term under a separately defined and checked formal calculus.

The third and fourth judgments are intentionally disjoint. A well-formed argument trace is not automatically a formal proof.

## 2. Term constructors

Let X be a set of source identifiers and Phi_c the set of propositions syntactically available in context c.

~~~text
Source(c, tau, x, raw)
Cite(c, phi, Source(c, tau, x, raw))
Joint(c, phi, [trace_1, ..., trace_n], rule_label)
Alternative(c, phi, trace_1, trace_2)
Translate(c, d, phi, trace, translation_witness)
~~~

The last constructor is **partial** and admissible only when a checked translation witness explicitly specifies how the proposition phi and its provenance are mapped from c to d.

The field rule_label in Joint is merely a named argument step. Without a proof rule and checked premises it cannot yield Proof(c,phi).

## 3. Selected formation rules

**Citation:**

    s : Source(c,tau)
    phi : Phi_c
    -----------------------------
    Cite(c,phi,s) : Trace(c,phi)

This records a source attribution, not the proposition's validity.

**Joint trace:**

    t_i : Trace(c,phi_i), i=1..n
    phi : Phi_c
    label : RuleName
    -----------------------------------
    Joint(c,phi,[t_1,..,t_n],label) : Trace(c,phi)

The result is an unverified trace, even if all premises have sources.

**Alternative trace:**

    t1 : Trace(c,phi)   t2 : Trace(c,phi)
    ------------------------------------
    Alternative(c,phi,t1,t2) : Trace(c,phi)

Different phi or different contexts fail the formation rule.

**Verified proof introduction (external obligation):**

    Check_c(pi,phi) = ACCEPT
    ---------------------------
    pi : Proof(c,phi)

The semantics of Check_c, and whether it is sound for the chosen theory, must be defined and justified separately. HUMA does not assume an AI-generated text explanation is a proof.

## 4. Provenance semantics

Map traces to N[X]:

~~~text
P(Cite(_,_,Source(_,_,x,_))) = x
P(Joint(_,_,[t1,...,tn],_)) = Product_i P(ti)
P(Alternative(_,_,t1,t2)) = P(t1) + P(t2)
~~~

For translations, require a source-preserving homomorphism h between explicitly declared source alphabets and set

    P(Translate(c,d,phi,t,w)) = h_w(P(t)),

provided the witness w is admissible. If w does not preserve a referenced source's meaning or legal scope, translation is undefined.

A source homomorphism alone cannot establish semantic proposition translation; that needs a second condition on phi.

## 5. Structural theorem (under these constructors)

**Proposition 7.1 (no implicit proof introduction).** If an expression is built solely using Source, Cite, Joint and Alternative and is well formed, then it cannot be assigned a Proof(c,phi) type by the formation rules in Section 3.

**Proof sketch.** Structural induction on its derivation tree. Source yields Source; Cite, Joint and Alternative yield Trace only. No listed rule concludes Proof. A Proof can enter solely through the separately checked introduction rule. This is a syntactic safety result; it is *not* soundness of the external checker, nor proof of empirical truth. It is also straightforward rather than novel.

**Proposition 7.2 (provenance homomorphism).** On terms formed by Cite, Joint and Alternative, P respects trace-level joint and alternative composition by multiplication and addition in N[X], respectively.

**Proof sketch.** Immediate by the recursive definition of P. This is a restatement of interpretation, not a novelty claim.

## 6. Structural counterexamples

**Wrong context:** Joint(c,phi,[Trace(c,alpha),Trace(d,beta)],r) with c≠d is ill formed until a compatible explicit translation is supplied.

**Wrong conclusion status:** Joint(c,"wealth prediction",traces,r) is still Trace(c,phi), even if many sources exist. It is not Proof(c,phi), nor an empirical validation.

**Wrong provenance independence:** Alternative(c,phi,t,t) has polynomial 2·P(t), not two independent scientific confirmations.

**Wrong exactness claim:** A lossy summary L(Source(raw)) cannot satisfy Restore(L(raw))=raw for all arbitrary byte inputs unless L remains information-preserving on that domain.

## 7. Next theoretical tasks

- Give a precise definition of Context and Phi_c, including equality and substitution.
- Specify an admissible translation witness as a pair of proposition and provenance maps with coherence laws.
- Select a concrete sound proof calculus for a restricted fragment, rather than trusting arbitrary textual inference rules.
- State an observational semantics for revision and revocation, with different source history and active authority.
- Prove preservation for composition and define countermodels when context translators lose information.
- Compare the construction with existing typed provenance and categorical database models before making originality claims.

No experiment or benchmark is authorized by these tasks.
