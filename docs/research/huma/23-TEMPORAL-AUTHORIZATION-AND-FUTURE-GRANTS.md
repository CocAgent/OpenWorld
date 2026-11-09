# 23 — Temporal Authorization, Future Grants and Exact Memory Lower Bounds

**Status:** Mathematical privacy and memory-bound discussion; no implementation, legal compliance certification, protocol deployment, experiment or machine-checked proof. Review together with Chapters 10, 13, 18 and 22.

## 1. Model what may change in time

A multi-agent memory system should distinguish:

- exact internal payload x, subject to lawful retention;
- current authenticated grant/revocation policy pi;
- source citation availability a;
- the principal p requesting access;
- a version or policy epoch e;
- which future policy and source events have been admitted to the model.

A source being present in a derivation is not proof that p can read it. A valid grant to read a source is not proof that the source's content is correct.

For an abstract state (x,pi), a tagged read result is

    Read_p(x,pi) = Denied            if authorization fails
                   Unavailable      if no retained authorized payload exists
                   Value(x)         if authorized and retained.

A real protocol must specify what is revealed by a Denied versus Unavailable result; these can have existence side channels. Our mathematical result assumes these distinct outcomes are explicitly part of the declared observation model.

## 2. The central future-grant obstruction

Fix a finite nonempty payload alphabet X with |X|>=2. Let the abstract state space be

    S = X x {Denied,Granted}.

Let the observation q be an exact authorized read:

    q(x,Denied) = Denied,
    q(x,Granted) = Value(x).

Let the admissible event Grant be the deterministic transition

    U_Grant(x,permission) = (x,Granted).

This is **not** permission for a user to self-authorize: Grant is a model event assumed to have already passed an independent authority check.

### Proposition 23.1 — Exact future grants require retained distinctions

Suppose a summary alpha:S->Z supports the current q and the future Grant event *exactly*, with an abstract update V_Grant and query decoder q_hat:

    alpha(U_Grant(s)) = V_Grant(alpha(s)),
    q(s) = q_hat(alpha(s))

for every s in S. Then the restriction

    x |-> alpha(x,Denied)

is injective on X. Hence the reachable summary codes for initially denied states number at least |X|; a fixed-length internal summary requires at least ceil(log_2 |X|) bits to distinguish them, excluding metadata and the decoder.

**Proof.** Suppose alpha(x,Denied)=alpha(y,Denied). Apply V_Grant to both, obtaining equal abstract post-grant states. Query exactness then gives

    Value(x)=q(x,Granted)=q_hat(V_Grant(alpha(x,Denied)))
            =q_hat(V_Grant(alpha(y,Denied)))=q(y,Granted)=Value(y).

Tagged Value is injective in its payload, so x=y. Thus the restriction is injective, giving the cardinality and fixed-bit bound. QED.

This is a direct application of dynamic observational equivalence, not a novel information-theoretic result. It demonstrates why a tiny public Denied-only cache cannot also serve as the **complete authoritative internal memory** for future authorized exact reads of arbitrary retained data.

## 3. A protected exact store is not free compression

One can retain exact payloads in a protected archival lane while exposing an agent a smaller public view. After a valid Grant, an authorized read can consult that lane and construct a new view.

This does not contradict Proposition 23.1: the *combined state* of the protected archive and public view still contains the distinctions among x. Counting only the public embedding or vector is not a fair measure of total memory storage.

The source archive must also support authorized deletion; future exact-read guarantees apply only when the declared retention and access policies permit recovery.

## 4. Revocation and anti-rollback depend on a separate authority

Assume each grant capability is indexed by a unique epoch g and the authoritative policy state is not restored from old data-only snapshots.

### Proposition 23.2 — Conditional non-resurrection

If capability g is revoked in the current authoritative policy, revocation of g is monotone, g is never reused, and every authorized read consults that current policy, then restoring any earlier data-only snapshot cannot reactivate g.

**Proof.** By assumption, data restoration leaves the authoritative policy and its revocation record unchanged. The current read check rejects g, regardless of which payload version the data snapshot holds. QED.

**Not proved:** that any database, credential system, host, backup, crash recovery, cryptographic key or agent actually enforces these assumptions. A stale policy database restored alongside the data can violate them.

This is a standard design invariant, not an original HUMA security theorem.

## 5. How permission changes enter a local graph certificate

To apply Chapter 22, a principal-specific read must declare every dependency:

    N_read includes the data owner state, current policy state,
    retained/unavailable status and any authorization epoch.

A grant/revoke event must declare which policy vertices it reads and writes. Its abstract event transition must satisfy the local EC equation for all declared inputs and its result must preserve the exact tagged read output under QC.

This has three important consequences:

1. A central policy service connected to every agent can create a high-degree dependency hypergraph; the bounded-neighborhood resource theorem of Chapter 22 may no longer apply.
2. A revocation is an **observable event** when it changes whether reads yield Value or Denied; hiding it from the event vocabulary makes an earlier exactness proof irrelevant.
3. Any replay or snapshot event touching authoritative policy must be explicitly modeled. Otherwise there is no anti-rollback theorem for that implementation.

## 6. A scoped noninterference condition

For principal p, choose an abstract low-view function L_p:S->Z_p that exposes only permitted observations, including required tagged Denied or Unavailable outcomes.

If every query q in Q_p factors through L_p and every event e in the declared future horizon E_p satisfies

    L_p(U_e(s))=V_(p,e)(L_p(s)),

then two full states with the same low view are observationally indistinguishable to p for every admitted event word. This is a standard induction on event words as shown in Chapter 18.

**Limit:** A future declassification (a newly authorized grant) can violate the low-view closure condition unless the model re-specifies its query/event contract or retains sufficient internal information. This is not a contradiction of information-flow security, because controlled declassification must be specified as an exception with authority and extent.

The result does not cover timing channels, adversarial observation scheduling, concurrency, external network traffic, retained logs or noisy outputs. Those need different threat models.

## 7. Counterexamples reviewers should test conceptually

| Incorrect claim | Counterexample |
| --- | --- |
| Denied now means two payloads can be merged forever | Grant later distinguishes their exact contents |
| A retained SHA digest makes reading safe | The digest is not an authorization grant |
| A source withdrawal automatically revokes a user's credential | Source validity and principal authority are different relations |
| Replaying an older authenticated data snapshot preserves current access | The snapshot may contain an obsolete policy unless current authority is independent |
| A private view's small vector is total memory cost | Protected source bytes, keys, references and backups still consume storage |
| A local certificate proves secrecy against every attacker | Undeclared side channels, faults or events are outside the certificate |

## 8. Research positioning

Established work on information-flow security, robust declassification and erasure policy shows that controlled disclosure needs more than a bare noninterference statement:

- https://www.cs.cornell.edu/zdance/robust_declassification.htm
- https://dash.harvard.edu/entities/publication/73120378-85ba-6bd4-e053-0100007fdf3b

HUMA's open research challenge is **not** to rediscover access-control theory. It is to define a certificate that combines typed source attribution, authorized future observations, dependency-local updates and erasure-aware exact memory under explicit small neighborhoods, with meaningful *new* claims beyond the established literature.

**Research freeze:** All reasoning here is on paper. No real account records, personal documents, runtime permissions, benchmarks, simulations, Python, Lean or hosted Actions are used.
