# 12 — Axioms for Typed, Contextual, Revision-Aware Memory

**Status:** HUMA-TCPC v0.3, candidate axiomatic specification. Written mathematics only: no runtime, experiments, proof assistant or claim of a new mathematical theory.

**Depends on:** Chapters 08–11; source provenance, formal proof, authorization and exact reconstruction must remain different semantic layers.

## 1. Objective

We seek a common language for recording claims and their transformations across formal or cultural contexts **without assuming the claims are true**.

A context might describe a mathematical theory, a textual tradition, a simulation or a scientific model. The type Trace(c,phi) denotes a recorded argument *about* proposition phi. Proof(c,phi) requires a separate checked proof. A source identifier does not establish authenticity; a provenance polynomial does not give a probability of truth.

Only a minimal **deterministic** fragment is axiomatized here. Stochastic, concurrent and distributed systems require further assumptions.

## 2. Candidate mathematical structure

Define a system

    H = (C, {S_c, X_c, Q_c, E_c, O_c, P_c}_c, W, Store, Policy),

where:

- C is a set of named contexts.
- S_c is a nonempty set of complete abstract states for context c. A state may include source records, traces, versions and policy references.
- X_c is a context-tagged source alphabet, disjointly labelled across contexts.
- Q_c is a declared family of *total observable queries*. Each q defines O_(c,q): S_c -> Result_q, with tagged outcomes Value(v), Denied, Unavailable or a declared error.
- E_c is an alphabet of event requests. Each e induces a deterministic total abstract transition U_(c,e): S_c -> S_c. A rejected action has an explicit status, rather than silently pretending a write succeeded.
- P_c maps well-formed trace terms to N[X_c], the free commutative semiring of source-provenance polynomials.
- W is a family of witnessed, partial context translations with declared domains and preservation contracts.
- Store and Policy are abstract interfaces with independently specified exact-restoration and current-authorization requirements.

Totalizing events is a modeling choice. Real failure handling and authentication remain external obligations.

## 3. Ten proposed axioms and contracts

**AX-01 — Context tagging.** Every stored claim declares its context and epistemic kind. Same literal words or source labels in different contexts are not automatically equivalent.

**AX-02 — Evidence separation.** The constructors Cite, Joint, Alternative and witnessed Translate create Trace objects, not Proof or EmpiricallySupported objects. Formal proof introduction requires an external verified derivation. Empirical acceptance requires an external evidence protocol.

**AX-03 — Provenance semiring.** For correctly typed same-context traces,

    P_c(Alternative(t1,t2)) = P_c(t1) + P_c(t2)
    P_c(Joint(t1,...,tn)) = Product_i P_c(ti), n >= 1.

Polynomial multiplicity counts formal derivation paths, not independent observational evidence.

**AX-04 — Declared observations.** Each q in Q_c has a stable declared meaning within this versioned model. A Denied read does not return hidden raw values. Principal, logical time and policy epoch are explicit parameters or components of state. Adding a new query changes the mathematical specification; earlier compression guarantees do not automatically extend.

**AX-05 — Deterministic event composition.** Every event is represented by a total state transition; a finite event word has an induced transition. Let U_empty be the identity. Let U_(we)(s)=U_e(U_w(s)), where we is word w followed by event e.

**AX-06 — Guarded context translation.** A witness w:c -> d contains

    (D_w, F_w, f_w, h_w, k_w, eta_w, obligations_w),

where D_w subset S_c is its domain; F_w:D_w -> S_d is the state map; f_w is a partial proposition map; h_w:N[X_c] -> N[X_d] is a semiring homomorphism; k_w:E_c -> E_d maps declared source events; eta_w:Q_c -> Q_d maps the query family the witness promises to preserve; and obligations_w records interpretation and disclosure prerequisites without pretending they have been checked.

A **strong witnessed simulation** satisfies, for all s in D_w, e in E_c and q in the preserved query family:

    U_e(s) in D_w
    F_w(U_e(s)) = U_(d,k_w(e))(F_w(s))
    O_(c,q)(s) = O_(d,eta_w(q))(F_w(s)).

The final equation needs compatible tagged result types or a separately declared result translation. If it fails, the witness is not valid for that query family; it cannot silently drop the query.

A source-only homomorphism h_w does not establish these conditions, and no context map is presumed semantically faithful merely because it is algebraically well formed.

**AX-07 — Provenance coherence.** For a translated trace t where the operation is defined,

    P_d(Translate_w(t)) = h_w(P_c(t)).

This is a provenance condition, not evidence of shared physical meaning or permission to disclose.

**AX-08 — Exact retained bytes.** On a declared authorized-retention domain B_exact,

    Decode(Encode(x)) = x.

An independently checked current read authorization is also necessary. A lossy summary is not a substitute for protected originals. After a lawful erasure, the corresponding read may be Unavailable.

**AX-09 — Authorization is external.** A digest, provenance expression, record version and successful decode are insufficient to grant access. Restoring data snapshots must not restore revoked access rights; preventing rollback of the *authoritative policy* is a separate security requirement.

**AX-10 — Resource limits are explicit.** Where resource bounds are claimed, exceeding node count, fan-in, depth, integer size, retention or serialization limits produces an explicit error or an explicitly approximate result, never silently a supposedly exact answer.

These are **requirements to be modeled and checked**, not guarantees already achieved by OpenWorld.

## 4. Semantics kept separate

| Layer | Relevant contracts | An invalid inference |
| --- | --- | --- |
| Syntax and typing | AX-01, AX-02 | A citation is a proof |
| Provenance | AX-03, AX-07 | A surviving path guarantees real-world truth |
| Dynamics and observations | AX-04, AX-05, AX-06 | A current summary answers all future questions |
| Storage and authority | AX-08, AX-09, AX-10 | Exact decoding authorizes disclosure |

An unverified reading, hypothesis, recorded observation and theorem are distinct epistemic objects, not labels on a universal "truth score."

## 5. Identity and composition of partial witnesses

An identity witness uses the full domain S_c with identity state, event, query, proposition and provenance maps.

To compose w:c -> d with z:d -> e, restrict to states s in D_w whose images F_w(s) lie in D_z; require closure under declared event transitions and compatibility of event and query maps. State, observation and provenance equations then compose by substitution on the restricted domain.

However, a restricted domain may omit records; permissions may not be composable; target queries may demand more than source queries; and a source substitution may merge identifiers. Consequently, these are **simulation candidates**, not categorical equivalences or universal semantic translations. A full category of partial witnesses needs additional coherence and domain proofs.

## 6. Small consistency example

Use one context with S={0,1}^6, Q the six coordinate queries and E six single-bit flips. Use exact six-bit encoding, identity translation only, source traces annotated in N[{a}], and a constant-allow policy in this deliberately harmless toy model.

The bounded algebraic fragment has a concrete interpretation. This is not a general consistency theorem, a security proof or an experiment involving people or divination.

## 7. Next proof obligations

- Define the *minimal* memory representation that supports every declared query **after every finite event sequence**, not merely at the current time (Chapter 13).
- Show what a witnessed context translation must preserve to avoid conflating distinguishable source states (Chapter 14).
- Investigate whether their joint requirements produce an original result beyond existing automata minimization, abstract interpretation, categorical simulation and provenance semirings (Chapter 15).
- Keep source lineage, proof checking, authentication, authority and privacy as separate validation gates.

**No experiments, CI, simulations, Python or Lean are run or authorized by this chapter.**
