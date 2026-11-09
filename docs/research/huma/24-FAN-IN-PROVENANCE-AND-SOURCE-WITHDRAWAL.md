# 24 — Multi-Agent Provenance: Fan-In, Identity Collision and Source Withdrawal

**Status:** Written-only source-provenance mathematics and explicit interface contracts. Standard semiring arguments; no claim of new mathematics, security implementation, or empirical evidence.

## 1. The critical multi-agent case is *fan-in*

When a receiving agent combines statements from two or more source owners, each incoming mapping might preserve identifiers internally while the **combined** mapping conflates their identities.

This is distinct from the truth of the statements and from consent to disclose them. HUMA must separately retain:

1. a source's context-tagged identity in the allowed evidence domain;
2. the algebraic structure of the recorded derivation;
3. the currently available and authorized source references;
4. the epistemic status of the claim (Trace, Proof or separately tested Observation).

Only (1) and (2) are modeled by the semiring maps below. Authorization and evidence correctness require independent contracts.

## 2. Tagged source alphabets and coproduct input

Let n incoming agent contexts have pairwise disjoint, **tagged** source alphabets

    X_1, X_2, ..., X_n.

A receiving agent's source alphabet is Y. Each incoming agent supplies a rename-only mapping

    f_i:X_i -> Y.

Let X be the disjoint union (coproduct) of the X_i, and define the combined function

    f:X -> Y, with f|X_i=f_i.

Each f_i extends uniquely to a semiring homomorphism

    h_i:N[X_i] -> N[Y].

The combined map likewise extends to

    h:N[X] -> N[Y].

The use of tagged X_i matters: two agent libraries can both call a source "record-1" without referring to the same actual source object.

### Proposition 24.1 — Individual injectivity is insufficient at fan-in

It is possible that each f_i is injective while the combined map f is not injective.

**Proof/counterexample.** Let X_1={a}, X_2={b} and Y={z}. Each singleton-domain map f_1(a)=z and f_2(b)=z is injective. But the combined map maps the distinct tagged sources a and b to the same z, so f is not injective. Therefore

    h(a) = z = h(b)

and their source identities cannot be distinguished from the translated provenance polynomial alone. QED.

This is a direct finite-set observation. It blocks the incorrect claim "each agent's source aliases are individually unique, therefore merged citations remain unique."

## 3. Theorem 24.2 — Fan-in attribution faithfulness criterion

For **rename-only** provenance maps, the following are equivalent:

(A) the combined source map f:X -> Y is injective;

(B) the semiring homomorphism h:N[X] -> N[Y] is injective;

(C) any two distinct single-source polynomials x and x' in X remain distinguishable after translation.

### Proof

(A) implies (B): An injective variable rename sends different source multisets to different target multisets, so distinct polynomial monomials retain distinct target images and nonnegative integer coefficients cannot cancel. Thus distinct polynomials remain distinct.

(B) implies (C): Single-variable polynomials are particular polynomials.

(C) implies (A): If f(x)=f(x') for distinct tagged variables, then h(x)=h(x'), contradicting C. QED.

**Scope:** This applies to rename-only substitutions of individual generators by individual generators. Arbitrary polynomial substitutions require separate hypotheses and generally are not characterized by simple source-map injectivity.

**Meaning:** Faithfulness here is *syntactic provenance attribution*. It is not a guarantee of source authenticity, identical interpretation or independent real-world support.

## 4. Source availability across a merged interface

For B subset Y (target available source identifiers), let A=f^{-1}(B) subset X. Define 0/1 source valuations ev_A on N[X] and ev_B on N[Y] as in Chapter 19.

### Proposition 24.3 — Availability and derivation-count compatibility

For every P in N[X],

    ev_B(h(P)) = ev_A(P).

**Proof.** The two semiring homomorphisms agree on each generator x in X, because x belongs to f^{-1}(B) precisely when f(x) belongs to B. Uniqueness of extension from a free commutative semiring proves equality on all polynomials. QED.

The equality of nonnegative integers preserves the *number of algebraic derivation paths* under the prescribed availability match. It does **not** turn path counts into independent evidence or a calibrated likelihood.

**Why fan-in collisions matter operationally:** If f(a)=f(b)=z, a target availability flag for z cannot independently represent "a withdrawn, b still active." There is no B subset {z} for which f^{-1}(B)={b}. Thus an independently revocable two-source contract requires either distinct target identities or another separately protected source-identity mechanism.

## 5. Scope-qualified provenance translation

A guarded transfer from source agent i to receiver j should contain a typed witness

    W_(i,j) = (Context_i, Context_j, allowed_claim_kinds,
               allowed_source_scope, f_ij, policy_epoch,
               admitted_queries, event_contract).

A meaningful interface certificate must explicitly say whether it promises:

- only boolean existence of a recorded derivation path;
- exact coefficient/multiplicity preservation;
- individual source identity and version;
- exact original source bytes (only with a permitted archive and restoration contract).

A receiver is not allowed to infer a stronger guarantee from a weaker one.

For full attribution across multiple incoming agents, the combined fan-in rename must be injective *on the source distinctions that the declared authorized query family requires*. If some identities are deliberately declassified or redacted into a shared category, the public contract must be narrowed accordingly; privileged exact attribution must reside in a separate authorized lane.

## 6. Revocation and time dependence

Let active source availability vary by time, A_t subset X. Let the receiver's active availability be B_t subset Y. A provenance-aware exact transfer should require, at every declared time/epoch,

    A_t = f^{-1}(B_t)

for the translated identity domain to which exact support queries apply.

This is a **compatibility requirement**, not a statement that the source owner and receiver have identical policies. An actual source-authority workflow must specify who may withdraw which source references and how the receiver learns of those changes.

For a claim lineage P=a*b+c, withdrawing a makes its a*b path unsupported at the specified scope, but c can remain. The historical expression P may remain attributable under valid retention. Neither a source withdrawal nor a retained P establishes that any user is authorized to read the content.

If policy epochs change, an outdated transfer witness must fail until revalidated. Automatically replaying an old witness from a data snapshot is not an authorization mechanism.

## 7. Theorem 24.4 — Algebraic composition of multi-hop renames

Suppose f:X->Y and g:Y->Z are injective rename-only maps permitted by their individual scope contracts. Then g∘f is injective and the induced polynomial homomorphisms satisfy

    h_(g∘f) = h_g ∘ h_f.

**Proof.** Composition of injective functions is injective. On each source generator x,

    h_(g∘f)(x)=g(f(x))=(h_g∘h_f)(x).

Both sides are semiring homomorphisms and agree on generators, hence are equal everywhere in N[X]. QED.

**What does not follow:** permission to send the sources across both hops. If i authorizes receiver j only, a second transfer j->k needs **separate** authorization. Algebraic composition alone cannot grant onward disclosure.

## 8. Joint interface certificate with Chapter 22

For a source-aware global query q_source(s) that reports an authorized attribution, Chapter 22's QC obligation must remain true after every admitted fan-in and withdrawal event, not only at initial transfer.

A sufficient **mathematical shape** of the certificate is:

- local event read/write neighborhoods for transfer and withdrawal;
- explicit current-policy dependency in each authorized read/transfer event;
- a faithful combined rename where source identity is a required query output;
- semiring-coherent lineage annotation for each translated Trace;
- source-availability compatibility at every policy/withdrawal epoch;
- protected exact archive for any full-source restoration queries;
- no implicit Trace -> Proof coercion.

These are conditions to prove or verify, **not properties of an existing production implementation**.

## 9. Reviewer counterexamples

| Invalid intuition | Counterexample |
| --- | --- |
| Each incoming rename injective => combined rename injective | Two singletons a and b both map to z |
| A hash proves a source owner's consent | A hash only checks a chosen digest, not the issuer's authority |
| Source support means a proposition is true | A trace can cite unreliable or misinterpreted material |
| Revoked a but merged alias z stays alive for b => exact source support preserved | a and b cannot be withdrawn independently through z alone |
| Multi-hop source map composes => multi-hop disclosure allowed | An authorization scope may prohibit onward sharing |
| Public summary retains a source label => full raw document recoverable | A label is not a reversible content encoding |

## 10. Prior art and novelty boundary

Free commutative provenance semirings, polynomial homomorphisms, source renaming and their composition are established theory. Relevant sources include:

- Green, Karvounarakis and Tannen (2007), Provenance Semirings: https://www.cs.ucdavis.edu/~green/papers/pods07.pdf
- A modern provenance formalization (bibliographic comparison, not executed here): https://zenodo.org/records/22900284
- HUMA Chapter 19 on individual source renaming.

A genuinely new result would require a **nontrivial integration** of scoped attribution, changing permissions, partial domain translations and locally checkable compositional contracts with an independently established originality argument. This chapter does not claim that goal has already been achieved.

**Research freeze:** No benchmarks, experiments, workflow runs, model fitting, real data, code, proof assistant or external service integration is involved.
