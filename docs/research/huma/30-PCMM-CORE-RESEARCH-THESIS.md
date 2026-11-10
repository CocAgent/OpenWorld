# 30 — HUMA-PCMM: Proof-Carrying Minimal Memory

**Status:** Research thesis and formal baseline v0.7, **written theory only**. This is a proposed research direction, not a deployed architecture, verified privacy system, new established theorem, or an empirical performance claim.

**Recommended primary question:** What is the least internal state that a network of typed agents must preserve to answer its *declared authorized future questions* exactly under its *declared future events*, while retaining only the source distinctions required by its provenance contract?

## 1. The focused research idea

Call the proposed program **Proof-Carrying Minimal Memory (PCMM)**.

Instead of claiming that a small vector can remember everything, PCMM asks each memory-sharing operation to carry a *checkable preservation contract*. A contract says:

- which agent, context and owner are involved;
- which current and future query results must remain exact;
- which event requests, including grants, withdrawals and erasure, are in scope;
- which source IDs or derivation paths must remain separately traceable;
- which data are available only through an independent protected exact store;
- which obligations guarantee that no forbidden observation is introduced.

The word *proof-carrying* is aspirational here: the manuscript provides a logical certificate **format and proof obligations**, not a checker. A provenance DAG is not itself a proof of logical correctness, security or source authenticity.

The strongest reason to pursue this direction is that it puts an information-theoretic optimization problem under a precise behavioral and authorization contract rather than treating unqualified compression as inherently good.

## 2. Model with explicit scope

Let V be a finite set of agent/context nodes. Let S be a finite set of **complete internal states** containing the declared source-history, provenance, current authoritative policy view and other state necessary to interpret the model. In a real architecture, the authoritative policy service must remain independently protected from rollback of data snapshots; the mathematical S is not a claim that everything is in one database.

Let E be a finite alphabet of **totalized, deterministic event requests**, with each e interpreted by U_e:S->S. A refused request has a declared refusal outcome, rather than being silently treated as permission to write.

For each principal p, let Q_p be a finite family of total observable functions q:S->A_q. Output tags can distinguish Value(v), Denied and Unavailable when declared by the threat model. An agent can have a very small public view while the **combined protected internal state** retains more information.

Let Q = union_p Q_p be the declared observation family for the complete system. This union is a *requirement for internal exactness*, not a right for one principal to inspect another principal's observations.

Let X be an explicitly context-tagged source alphabet, and let each recorded claim trace have a provenance annotation P(t) in N[X]. The trace’s source identifiers, claim validity, and principal authorization are different sorts of information.

A candidate exact internal abstraction is a surjective map

    alpha : S -> Z.

Its target is the set of reachable abstract codes, not a guaranteed fixed-bit implementation.

## 3. The precise mathematical criterion: kernel factorization

Define the kernel relation of a function f as

    ker(f) = {(s,t) in S x S | f(s)=f(t)}.

The intended requirements for every q in Q and e in E are

    q = q_hat o alpha
    alpha o U_e = V_e o alpha.                    [PCMM-Q/E]

Thus the abstract code answers all declared observations and updates exactly.

### Proposition 30.1 — Necessary and sufficient exactness conditions

For any surjective alpha:S->Z on a finite set S, the following are equivalent:

**(A)** There exist functions q_hat:Z->A_q and V_e:Z->Z satisfying PCMM-Q/E for every q in Q and e in E.

**(B)** The following two kernel inclusions hold for all q and e:

    ker(alpha) subset ker(q)
    ker(alpha) subset ker(alpha o U_e).

**Proof.**

(A) implies (B): If alpha(s)=alpha(t), applying q_hat gives q(s)=q(t). Similarly applying V_e gives alpha(U_e(s))=alpha(U_e(t)). These are exactly the two kernel inclusions.

(B) implies (A): Since alpha is surjective, for every abstract code z choose a representative s with alpha(s)=z and define

    q_hat(z)=q(s)
    V_e(z)=alpha(U_e(s)).

The first inclusion ensures q_hat is independent of the chosen representative. The second ensures the same for V_e. By construction the factorization equations hold for every s. QED.

This is a **standard quotient/factorization criterion**, not a novel HUMA theorem. It is useful as the precise benchmark that a future graph-local certificate must imply.

### Corollary 30.2 — Future-query preservation

Under (A) or (B), for every finite event word w and query q,

    q(U_w(s)) = q_hat(V_w(alpha(s))).

**Proof:** Induct over the event word using the update equation; apply the query equation. This is the known behavioral-simulation pattern of Chapter 13.

A task-limited public cache may have a different alpha_p with a smaller query/event vocabulary. That does **not** mean alpha_p is exact for every internal query or grant event.

## 4. The minimum-state target and its important limitation

Define behavioral indistinguishability with respect to all declared future event requests and internal observations:

    s ≈_(E,Q) t
       iff for every w in E* and q in Q:
              q(U_w(s)) = q(U_w(t)).

The quotient S/≈ is the **minimum exact deterministic state representation for this fully specified event/query contract**, up to naming of abstract states (Chapter 13). If there are K classes, any fixed-length encoding of all reachable quotient states needs at least ceil(log_2 K) state bits, apart from the decoder and metadata.

However:

- If Q includes full original byte recovery and a future grant can authorize that recovery, the complete internal state must retain enough information for that future result, unless erasure lawfully made it unavailable.
- If Q excludes source-identity queries, a short summary may be correct for Q while still being unfit for scientific citation or source withdrawal.
- A public per-principal view can reveal much less than the internal exact state. Never equate a small public view with small *total* storage cost.
- Different principal views must not be casually combined; joint outputs can reveal facts not available through any declared individual view. A collusion threat requires joint observations in the threat model.

## 5. Source-identity and provenance obligations

The provenance contract has two independently chosen parts:

**Trace algebra:** For a context translation F with allowed source-polynomial map h,

    P_target(F(t)) = h(P_source(t)).                 [PCMM-P]

This is a formal recorded-lineage equality, not a truth or consent check.

**Authorized identity preservation:** If Q includes an exact query distinguishing source identifiers a and b, the abstract source representation must not merge that distinction. For rename-only fan-in, the combined renaming needs to be injective on the identities that the specified query family must retain (Chapter 24).

If a principal’s view is intentionally redacted, that view may use a noninjective aliasing map, provided its actual observation contract does not promise exact identity. An independent protected reference may preserve distinctions for authorized queries without exposing them to the recipient.

A correct source-identity map cannot establish the source's authenticity or an owner’s permission to disclose it.

## 6. Policy events are part of the event language

A grant, withdrawal, revocation or erasure that can affect future observable results must be included in E or explicitly excluded by a restricted, versioned contract.

**Future-grant obstruction:** Consider two secret payloads x != y that currently both return Denied. If a legal future Grant makes exact Value(x) or Value(y) observable, the full internal abstraction cannot merge those states, even if the public principal-specific cache presently shows the same Denied result.

**Revocation obstruction:** An old data snapshot cannot be allowed to replace an external authoritative revocation record. This is an independent assumption on current authority and anti-rollback design; no provenance polynomial or memory compression theorem proves it.

**Erasure obligation:** If an authorized erasure removes the original protected payload, an exact future read can change to Unavailable by specification. A universal exact-reconstruction claim after lawful erasure is inconsistent with that policy.

The model explicitly does **not** prove resistance to timing, cache, network or power side channels, authentic signatures, key rotation, identity management or operational incidents.

## 7. The genuinely open HUMA-PCMM challenge

The mathematical factorization condition of Section 3 is already known. So are provenance semirings, automata minimization and many dynamic information-flow principles.

The proposed **research contribution**, not yet established, is:

> For a nontrivial class of typed, *coupled* agent dependency graphs with policy-changing events and provenance-identity obligations, construct a **small, compositional certificate** that is sound and complete *relative to an explicit bounded interface grammar*, and prove a meaningful synthesis or verification complexity bound without enumerating all admissible global states.

A possible restricted family K could fix:

1. finite local state alphabets with explicit size bounds;
2. a declared dependency hypergraph and bounded neighborhood/tree-decomposition width;
3. deterministic totalized transitions and explicit tagged denial outcomes;
4. finite, versioned permission states whose transitions are included in E;
5. rename-only provenance with per-principal source identity requirements;
6. a finite grammar of local equivalence partitions and guarded translations.

**Open conjecture (not asserted):** Under *additional* structural restrictions to be discovered, the existence of a sound PCMM certificate for networks in K can be decided by a graph-local procedure whose time and certificate size are bounded by a polynomial in the explicit network description times a function of width and local alphabet size.

Neither bounded treewidth alone nor an ordinary semiring homomorphism proves this. If the unrestricted problem remains hard or the interface must retain all raw information, a formal negative result or a narrower positive theorem is more valuable than an unsupported performance promise.

## 8. Five mandatory countermodels before publication

1. **Hidden future operation:** a currently discarded bit becomes observable after a declared event.
2. **Policy escalation/withdrawal:** a previously denied read becomes authorized, or a revoked capability is mistakenly revived by restoring an old snapshot.
3. **Fan-in alias collision:** two distinct source-owner records map to one receiver source identifier even though exact attribution is promised.
4. **Information through collaboration:** separately limited views are combined in a way that reveals a secret outside the declared joint-observation policy.
5. **Coupled unreachable states:** an unconditional full-product certificate falsely claims to be optimal on a restricted admissible state set.

Every candidate theorem must either account for these cases, provide a correctly scoped exclusion, or produce a concrete failure witness.

## 9. Recommended writing deliverables, still with zero experiments

**PCMM-01: Formal research question.** Specify states, principal observations, events, tagged errors, source alphabets and allowed local interface grammar.

**PCMM-02: Factorization and necessity proof.** Prove Proposition 30.1 carefully and distinguish its baseline status from any new result.

**PCMM-03: Graph-local certificate synthesis conjecture.** Choose a narrow coupled graph class, define certificates and prove either a restricted theorem or an honest impossibility boundary.

**PCMM-04: Privacy/source critical review.** Write every authorization and provenance counterexample, independent prior-art comparison and explicit limitations.

**PCMM-05: Human manuscript review.** Assess if there is any genuinely original statement before preparing a formal proof-assistant plan. No test execution or scientific holdout is approved by this chapter.

## 10. Prior-art comparison required for a defensible contribution

The following works already cover substantial parts of the foundations:

- Stanford CS103, [Guide to the Myhill–Nerode Theorem](https://web.stanford.edu/class/archive/cs/cs103/cs103.1266/guide_to_myhill_nerode), for behavioral distinguishability and finite minimal-state ideas.
- Green, Karvounarakis and Tannen (2007), [Provenance Semirings](https://www.cs.ucdavis.edu/~green/papers/pods07.pdf), for source-polynomial provenance.
- Chilton, Jonsson and Kwiatkowska (2014), [Compositional assume–guarantee reasoning for input/output component theories](https://www.sciencedirect.com/science/article/pii/S0167642314000057), for sound and complete compositional contract reasoning on interface-automata variants.
- Li and Zhang (2022), [Towards a General-Purpose Dynamic Information Flow Policy](https://doi.org/10.1109/CSF54842.2022.9919639), for declassification, delegation, erasure and revocation in changing policies.
- Gouni, Pfenning and Aldrich (2025), [Structural Information Flow: A Fresh Look at Types for Non-interference](https://doi.org/10.1145/3764116), for more recent structural reasoning about permitted information release.

The **research gap is only a hypothesis** until an exact theorem is shown not to be implied by these or other existing approaches.

## 11. Public repository and resource boundaries

This chapter belongs exclusively to public, generic mathematical theory. It contains no unrelated private project names, personal records, source identifiers, confidential conference affiliations, API secrets, experimental raw data or transferred private repository files.

OpenWorld remains under its owner-requested hosted-experiment freeze. **NOT RUN by design:** GitHub Actions, Python, Lean, tests, model fitting, simulations, benchmarks, holdouts or any hosted computation.

**Bottom line:** The strongest HUMA contribution to pursue is not "AI remembers everything"; it is **the exact boundary of what may safely be forgotten, and a checkable, scoped proof that a chosen abstraction stays correct under declared future interactions**.
