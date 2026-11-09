# 19 — Provenance-Preserving Interfaces: Source Identity, Withdrawal and Scope

**Status:** Written-only elementary algebraic propositions with counterexamples. Not independently peer reviewed, machine checked, implemented or a demonstrated novel theorem.

## 1. Provenance is not just a source-count field

In the provenance model of Chapters 03 and 08, each context c has a source alphabet X_c and a commutative semiring N[X_c] of finite polynomials with nonnegative-integer coefficients.

An expression such as

    P = a*b + c

records two alternative derivation patterns: one path jointly cites a and b, and one path cites c. The expression is not a proof of logical entailment or a probability estimate.

There are several distinct possible requirements for an interface:

1. **Support preservation:** after a source withdrawal, determine whether some recorded path survives.
2. **Derivation multiplicity:** count algebraic derivation paths, without calling them independent evidence.
3. **Attribution preservation:** distinguish which original identifiers were cited.
4. **Versioned source preservation:** distinguish different versions of the same source.
5. **Scoped disclosure:** expose only what the current principal and consent policy allow.

These requirements are not interchangeable. A mapping preserving boolean support might lose attribution, and a mapping preserving raw identities might be unauthorized to disclose them.

## 2. A narrowly defined source-rename interface

Take finite source alphabets X and Y and a function

    f : X -> Y.

Define the semiring homomorphism h_f:N[X]->N[Y] as the unique extension of

    h_f(x)=f(x)

on individual generator symbols and with h_f(0)=0, h_f(1)=1, preserving sums and products.

This is a **rename-only** transformation, not an arbitrary provenance substitution such as x -> (u+v) or x -> u*v.

For A subset X and B subset Y define source-availability valuations

    ev_A(x) = 1 if x in A, else 0,
    ev_B(y) = 1 if y in B, else 0.

### Proposition 19.1 — Exact availability transfer under source pullback

If A = f^{-1}(B), then for every P in N[X],

    ev_B(h_f(P)) = ev_A(P).

**Proof.** Both sides are semiring homomorphisms from N[X] to N. On every generator x in X,

    ev_B(h_f(x)) = ev_B(f(x))
                  = 1 iff f(x) in B
                  = 1 iff x in f^{-1}(B)
                  = ev_A(x).

The homomorphisms agree on all generators and hence agree on every polynomial by the universal property of N[X]. QED.

**Interpretation:** The *integer count* of algebraic derivations and therefore its positive/zero support status agree under correctly pulled-back availability. The result does not require f to be injective, and it does **not** establish that different sources remain individually identifiable after translation.

A target source's availability is not equivalent to current user authorization to read that source; permission checks remain external.

## 3. Theorem 19.2 — Attribution-preserving renaming is injective

**Statement.** If f:X->Y is injective, then h_f:N[X]->N[Y] is injective: different provenance polynomials remain different under translation.

**Proof.** Represent a polynomial as a finite mapping from monomials (finite multisets of variables from X) to nonnegative coefficients. An injective f sends distinct source variables to distinct target variables, hence induces an injective mapping on finite multisets. Two distinct monomials therefore have distinct images. Extending coefficientwise cannot merge separate monomials, so two different polynomials map to different polynomials. QED.

This preserves **formal algebraic source identity**, not legal authority, semantic meanings or actual independence of observations.

### Corollary 19.3 — Rename-only attribution cannot use fewer target identifiers

If X and Y are finite and every individual source must remain distinguishable in the translated provenance polynomial, a rename-only map f must be injective and therefore

    |Y| >= |X|.

**Proof.** If f is not injective, choose a != b with f(a)=f(b). Then h_f(a)=h_f(b), so their identity cannot be distinguished from the translated polynomial alone. Conversely, injectivity is sufficient by Theorem 19.2. The finite cardinality bound follows by the pigeonhole principle. QED.

This is a lower bound on the **number of distinct symbolic names** in this particular representation, not on bytes in any realistic compressed data structure. Dictionary coding, pointers, structured version tags or a separate privileged mapping may encode the same identities more economically.

## 4. A noninjective mapping can keep support but lose source identity

Let f(a)=z and f(b)=z for distinct source identifiers a and b. Then

    h_f(a)=z=h_f(b).

If a and b were from different original contexts, failing to context-tag them would make the problem worse.

For the source-availability set A={a}, there is **no** target set B subset {z} such that f^{-1}(B)=A: either both a and b are present in the pullback, or neither is. Thus the source-specific withdrawal of a cannot be modeled faithfully using target availability of z alone.

This failure explains why a boolean "some source exists" bit is not an adequate substitute for source-level revocation and attribution when those queries are admitted.

## 5. Provenance under composite rename witnesses

Let f:X->Y and g:Y->Z be source renamings, with corresponding semiring homomorphisms h_f and h_g.

### Proposition 19.4 — Composition law

    h_(g o f) = h_g o h_f.

**Proof.** Both homomorphisms agree on every generator x in X:

    h_(g o f)(x) = g(f(x))
                  = h_g(h_f(x)).

They also agree on constants and preserve sums and products, hence coincide on all of N[X]. QED.

If f and g are both injective, their composition is injective and formal source distinctions are preserved through both steps. A failed permission or provenance-scope check at either step must still block the actual translation, regardless of algebraic composition.

## 6. Scope and sensitive source identifiers

A public, globally stable source identifier can become a linking key across agents or institutions. Even if a rename is injective, its use may violate privacy or consent rules.

A cautious research design distinguishes:

- **Internal archival identity**, retained only as authorized;
- **Principal-scoped alias**, which may be intentionally noninvertible to the recipient;
- **Authorization epoch and scope**, checked by a separate current authority;
- **Lineage commitment or redacted attribution**, whose privacy and integrity properties must be specified rather than assumed.

An intentionally redacted public view is not required to answer privileged source-attribution queries; it must declare a narrower query contract. The full internal reference may remain separately protected only for the allowed retention period.

A hash is not automatically a secure alias. Hashes of predictable names can be brute-forced or correlated. No cryptographic construction or privacy guarantee is implemented by this manuscript.

## 7. Interface certificate for HUMA-N1

For a cross-context event to preserve the declared exact provenance queries in addition to the dynamic state summary of Chapter 17, the written certificate should name:

1. The source and target **context-tagged alphabets** and versioned schemas.
2. The allowed scope of the translation and its current policy epoch.
3. A rename or explicit polynomial source substitution h.
4. The exact query family retained (e.g. source availability alone, or full identifier attribution).
5. A proof obligation of the appropriate kind:
   - for availability counts: Proposition 19.1 with A=f^{-1}(B);
   - for exact renamed attribution: injectivity of f under Theorem 19.2;
   - for general polynomial substitutions: separately proved properties, not an unjustified use of the rename theorem.
6. A failure result when a withdrawal or authority check makes translation unavailable.
7. A declaration of original-source erasure and retention behavior.

Without these distinctions, a combined memory graph may appear to keep "provenance" while actually losing evidence identity or silently exposing private records.

## 8. Limits and next questions

- Source-renaming and provenance-semiring homomorphisms are **established algebra**, not a new HUMA finding.
- Attribution-preserving syntax does not guarantee true content, authorized consent or correctness of inferred claims.
- Correct source pullback may be impractical when a target alias conflates identifiers, as shown in Section 4.
- A useful HUMA-N1 advance would be a **compositional, independently checkable certificate** combining interface-complete future observations, source-identity preservation and principal-scoped authorization, with explicit complexity benefits for a nontrivial family of dependency graphs.

The final novelty and review roadmap is developed in Chapter 20.

**No benchmarks, code execution, proof assistants, simulations, CI or holdouts are used or authorized here.**
