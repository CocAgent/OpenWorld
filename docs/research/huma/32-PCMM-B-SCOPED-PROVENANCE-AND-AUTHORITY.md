# 32 — PCMM-B: Scoped Provenance, Authority and Future Knowledge

**Status:** Theory-only obligations and conditional propositions. Not an authorization protocol, cryptographic proof, legal compliance determination, independently verified mathematics or experimentally evaluated system.

## 1. Three different forms of 'knowing'

An agent memory may contain:

- a **Trace**: a recorded explanation or citation path to a source;
- a **Proof**: a separately checked derivation under explicit formal axioms;
- an **Observation**: a report requiring independent empirical validation.

These do not imply one another. In particular, a nonzero provenance polynomial does not prove a statement correct. Source identifiers from different contexts are different even if their visible strings happen to match.

Separately, a **Principal** may or may not have current permission to read a source. The authorization predicate and the provenance semiring must never be identified.

## 2. The principal-scoped observation contract

Fix a finite, deterministic, totalized abstract state system S and a set P of principals. A state contains enough mathematical information to interpret the modeled data and policy transitions, but a real authoritative policy service is a distinct trust boundary.

For each principal p choose a family Q_p of **tagged allowed observable functions**, including explicit outcomes

    Value(v), Denied, Unavailable, Rejected(reason)

as relevant to that public protocol.

The contract may include some but not all of:

- exact attributed source identity under a named version;
- existence of a currently admissible recorded derivation path;
- exact original bytes where retention and authority permit;
- denial or unavailability without returning secret payload;
- formal proof-certificate status (never inferred from a trace);
- policy-epoch version or grant validity where the interface permits disclosure.

A request to read unauthorized material is not converted into an allowed query yielding Value. The model instead describes the actual allowed response, such as Denied, as a total observable.

For every declared event e, including Grant, Revoke, WithdrawSource, ErasePayload and RestoreData when admitted, require a total transition U_e:S->S, **with all event authority checks represented as assumptions or explicit policy-state tests**. A denied event must not silently mutate protected data.

## 3. The combined internal memory versus an agent's view

Let alpha:S->Z be a shared *internal* abstraction and beta_p:S->Z_p a principal-specific *exposed* view.

An exact shared internal contract for Q=union_p Q_p asks that all q in Q factor through alpha and that every admitted U_e acts consistently on alpha.

A beta_p may intentionally be coarser than alpha; it need only answer its own specified Q_p and support its own declared authorized future operations. It is **not** promised to answer all other principals' queries.

### Proposition 32.1 — Future authorized exact reads forbid premature conflation

Suppose the declared internal event alphabet contains a correctly authorized future Grant event and the corresponding read query returns exact Value(x) for retained payload x. If two internally possible states differ only in x, then any fully exact internal summary for this event/query contract must distinguish those states.

**Proof.** If the summary codes were equal, exact abstract event compatibility would give equal post-Grant codes. Exact query compatibility would then give equal Value outputs, contradicting x != y. This is Chapter 23's future-grant argument. QED.

The result does **not** require exposing x before authorization: the principal's current beta_p may return Denied in both states, while alpha or an additional protected exact store retains the distinction.

A small public embedding does not establish low total storage when a protected exact archive still exists.

## 4. A precise provenance-fidelity contract

Let X be a disjoint union of context-tagged source alphabets and let a recorded trace t carry P(t) in N[X]. A source-renaming map f:X->Y induces a semiring homomorphism h_f:N[X]->N[Y].

Declare one of three **different** interface promises:

**PF-0: Path existence only.** Given a declared active set A of source IDs, return whether ev_A(P)>0. This can often be maintained using less information than the full polynomial, provided availability events remain in scope.

**PF-1: Polynomial count and expression semantics.** Preserve the formal derivation polynomial via an expressly declared homomorphism. Source multiplicity is not evidence independence.

**PF-2: Exact source attribution.** Preserve the identity and version distinctions that a permitted source-identity query can ask about.

For rename-only fan-in with arbitrary exact source-ID queries, PF-2 requires the **combined** source map f to be injective on the protected source distinctions, rather than merely each sender's map separately (Chapter 24). A scoped or redacted view can use a noninjective mapping only if it promises a correspondingly weaker query family; protected exact attribution may remain elsewhere where retention is authorized.

### Proposition 32.2 — Attribution is a query-family obligation

If two admissible internal states s,t have the same abstract code alpha(s)=alpha(t), yet an explicitly permitted attribution query q returns different source IDs or versions, alpha is **not** exact for that contract.

**Proof.** If q factored through alpha, equal codes would imply equal outputs. Contradiction. QED.

Thus exact attribution is neither guaranteed by a source-count field nor by an algebraic statement that a recorded derivation path survives.

## 5. Why agent-wise privacy is not automatically coalition privacy

Consider a secret bit h and an independent masking bit r in {0,1}. Two principals are each exposed to one synthetic view:

    beta_A(h,r)=r,
    beta_B(h,r)=h XOR r.

For each possible value of a *single* exposed view, both secrets h=0 and h=1 remain possible by choosing an appropriate r. Therefore **neither view alone determines h** over the set of possible states.

But the coalition holding both views computes

    h = beta_A(h,r) XOR beta_B(h,r).

Thus individual inability to determine h does not imply inability for a coalition. This is a deterministic relational example; it is **not** a proof of cryptographic secrecy and does not require sampling or experimentation.

**Contract obligation:** If collusion or joint observation is within the threat model, include that joint view in the authorized/forbidden information-flow specification. Merely checking each principal's read API separately cannot justify a coalition non-disclosure claim.

An explicit confidentiality guarantee must define which pairs of complete states should remain indistinguishable and whether sharing between principals is authorized. The PCMM exactness theorem preserves specified results but does not itself establish confidentiality.

## 6. Authority changes and time

Policy and data need distinct logical histories:

    DataHistory_t, CurrentPolicy_t.

Consider a grant epoch g which current authoritative policy has revoked. Restoring old **data** state must not reset CurrentPolicy_t to the historical version in which g was active. Otherwise an old capability can regain access, even when its historical signature or digest is intact.

This is the **separate, conditional** anti-rollback obligation from Chapters 10 and 23. It depends on authentic policy decisions, replay resistance, key management and read-path enforcement in a real system. Provenance equations cannot derive it.

An ErasePayload event can render an exact prior read Unavailable, even if older historical versions formerly answered Value. Declaring that outcome is consistent with task-limited memory and privacy; claiming everlasting recoverability of the erased bytes would conflict with the erasure contract.

A source withdrawal can deactivate a derivation path without revoking the requester's account credentials. Conversely, revoking a credential does not make a stored mathematical statement false. These are different state transformations with different query effects.

## 7. A conditional theorem combining the layers

### Theorem 32.3 — Scoped observations under a correct internal abstraction

Assume:

1. a finite, total, deterministic model of S, E, Q_p and events including each admitted authority change;
2. an internal map alpha satisfying PCMM-Q/E of Chapter 30 for every q in union_p Q_p and every e in E;
3. that every modeled q_p applies the required **independent current policy decision** before returning a Value result;
4. that any source-attribution response is computed using the explicitly promised PF level and correct context/source types.

Then for every principal p, any admitted event word w, and any declared q in Q_p, the abstract model returns exactly the same tagged result as the raw *mathematical model*:

    q(U_w(s)) = q_hat(V_w(alpha(s))).

**Proof.** Assumptions 1 and 2 satisfy Corollary 30.2 and the temporal update conditions, so equality follows by induction on w. Assumptions 3–4 specify the meanings of the raw q functions and do not follow from the equality itself. QED.

**Scope:** This is *behavioral agreement with the specified access-control model*, not validation that the real model has safe policies, authenticated users, no side channels or legally compliant erasure. An abstraction can reproduce an **insecure** raw policy exactly.

## 8. Mandatory failure cases

- Same literal source label from two contexts is mistaken for one authenticated record.
- A generated citation path is marked Proof instead of Trace.
- A principal's Denied query is implemented as Value(hidden).
- Grant is omitted from E although the future exact-read promise includes it.
- A restored old data snapshot reactivates previously revoked current authority.
- Two distinct sources are merged by fan-in while PF-2 attribution is claimed.
- Two individually limited views combine to disclose forbidden information.
- An erased exact payload remains recoverable from backups, caches or a source index despite a deletion claim.

Each should be excluded by a hypothesis, represented as an explicit counterexample, or flagged as outside the theorem's model. A written exactness contract alone does not solve these problems operationally.

## 9. What remains original work to seek

A substantive PCMM contribution would make **policy-scoped local contracts composable**, with correctly declared failure, partiality and source-identity semantics, while also constructing a small representation for a nontrivial coupled graph class.

The present statements use established provenance, dynamic information-flow and information-theoretic reasoning. Their integration into a coherent theory may be valuable, but **a new theorem remains unproved**.

## 10. Literature and safeguards

- Peixuan Li and Danfeng Zhang (2022), *Towards a General-Purpose Dynamic Information Flow Policy*: https://doi.org/10.1109/CSF54842.2022.9919639
- Stephen Chong and Andrew C. Myers (2008), *End-to-End Enforcement of Erasure and Declassification*: https://doi.org/10.1109/CSF.2008.12
- Green, Karvounarakis, Tannen (2007), *Provenance Semirings*: https://www.cs.ucdavis.edu/~green/papers/pods07.pdf
- HUMA Chapters 08, 18, 19, 23, 24 and 30.

**Public scope and resource freeze:** No unrelated private project names, source material, identities, credentials, experimental outputs or third-party private code are included. No Python, Lean, test, simulation, benchmark, holdout or GitHub Actions is executed.
