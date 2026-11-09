# 18 — Principal-Scoped Memory Views, Policy Events and Noninterference

**Status:** Theory-only deterministic model. Security statements are **conditional mathematical properties**, not proof of an implemented access-control system. No experiments, CI, proof assistant or private data use.

## 1. Separate source history, policy and observable response

A source record is not itself an authorization grant. Let

    S = D x A

where D is an abstract data state and A is an abstract current-policy state. A real implementation may be distributed, but no assumption is made that old data snapshots can authoritatively restore A.

Fix a principal p and an exact query name q. The corresponding observable query is

    Read_(p,q) : S -> {Denied, Unavailable} + Value(Result_q).

These results are *tagged and distinct*. In particular:

- Denied: p currently lacks authority for this read.
- Unavailable: the requested data no longer exists in the allowed retention domain, or is not recoverable under the declared contract.
- Value(v): the authority check permitted the data view and the retained data could be read.

Not distinguishing Denied and Unavailable could disclose or conceal existence in unanticipated ways; the exact public policy for errors should be deliberately specified. This model treats them as different observables only where the chosen query contract does so.

Every principal has a declared query family Q_p and a declared event family E_p for actions that principal can cause or observe. Other principals' actions and environment changes need to appear as explicit exogenous events in the model if they can change what p can later observe. Absent events cannot be silently assumed harmless.

## 2. The future-grant pitfall

Take a secret bit b in {0,1} and a policy flag a in {denied,allowed}:

    S = {(b,a)}.

Define the only read query as

    q(b,denied) = Denied,
    q(b,allowed) = Value(b).

Let Grant(b,a)=(b,allowed) and Revoke(b,a)=(b,denied) be abstract policy transitions. These are **model operations**, not permissions for an actual principal to grant itself access.

At the present state, (0,denied) and (1,denied) return the same Denied result. If a future Grant event belongs to the declared event alphabet, the same two states become distinguishable:

    q(Grant(0,denied))=Value(0),
    q(Grant(1,denied))=Value(1).

Therefore their current-observation equivalence does not imply their *future-event observational equivalence*.

**Consequence:** A principal-facing cache may omit presently hidden detail, but the protected authoritative data store must not assume that omission preserves exact reads after a future legal grant. The raw data can be fetched from a separately authorized exact lane at the time of the grant, if it has not been lawfully erased.

## 3. Theorem 18.1 — More admitted queries cannot reduce distinctions

Let S and a fixed deterministic event family E be as in Chapter 13. If Q_0 subset Q_1, let ~_0, ~_1 be their respective dynamic observational equivalence relations.

Then

    ~_1 subset ~_0

as relations on S. For finite S,

    |S/~_1| >= |S/~_0|.

**Proof.** If all future answers agree for every query in Q_1, they necessarily agree for every query in its subset Q_0. Thus each ~_1 class is contained in a ~_0 class. The quotient cardinality inequality follows. QED.

This is the familiar partition-refinement property. It is not a new theory of security or proof that increasing permissions always makes real human users safer.

A comparison of two principals' observational power needs an explicit common event alphabet and a genuine inclusion of **observable query functions**, not merely an informal ranking of roles. Different permission policies can be incomparable.

## 4. A low-view simulation condition

For a fixed principal p, choose a declared low/authorized abstraction

    ell_p:S -> L_p.

Suppose that:

**LQ:** every query q in Q_p factors through ell_p; there exists q_hat with q=q_hat o ell_p.

**LE:** every event e in the *chosen future event alphabet* E_p factors through ell_p; there exists V_e:L_p->L_p with

    ell_p(U_e(s))=V_e(ell_p(s)).

These are strong obligations. They must be checked for policy events, failure statuses and authorized source reads just as for ordinary data updates.

### Proposition 18.2 — Conditional observational noninterference

If ell_p(s)=ell_p(t), then for every word w in E_p* and every query q in Q_p,

    q(U_w(s))=q(U_w(t)).

**Proof.** Induction on the event word using LE yields equality of the low views after every admitted event sequence. Apply the decoder q_hat from LQ to both. QED.

This is a standard deterministic information-flow / noninterference argument **relative to the declared observations and events**. It does *not* establish protection against timing, cache, error-channel, concurrency, cryptographic or infrastructure leaks.

## 5. Why a future grant breaks an underspecified low view

In the secret-bit model above, suppose ell_p(b,denied) records only Denied while hiding b. LQ holds for denied states at that moment, but LE cannot hold globally if Grant is an admitted event and the future read returns Value(b): two states with the same low view would yield different post-grant low views.

There are at least three honest ways to resolve this:

1. **Restricted horizon:** exclude Grant and declare that the summary is valid only while the policy epoch and permitted event vocabulary remain unchanged.
2. **Protected exact store:** maintain b in a separate authorized lane and rebuild a new principal-specific view on legal grant; the *old low-view abstraction by itself* is no longer a sufficient state for that expanded transition system.
3. **Refined mathematical state:** retain additional hidden distinctions in an internal state while exposing only authorized low queries. Distinguish internal storage requirements from what p can observe.

None permits revealing b while the policy says Denied.

## 6. Provenance withdrawal is different from access revocation

Let a claim have provenance polynomial P=a*b+c. The function

    SourceSupported(P,A_t) = [ev_(A_t)(P)>0]

is a record-path availability predicate. It does not answer

    MayRead(principal,source,policy_epoch).

An a-source withdrawal might invalidate the a*b derivation without revoking the principal's permission to read another item. Conversely, loss of a read grant must not silently delete or rewrite historical lineage where its limited retention remains authorized.

This separation is required before future HUMA-N1 interfaces can include source support and principal-specific reads in the same query family.

## 7. Policy epochs and historical snapshots

Suppose a grant is identified by (principal,resource,epoch), and current authoritative policy forbids reactivation of a revoked epoch. Restoring a *data-only* snapshot does not re-enable the old epoch, provided that the authoritative policy truly cannot roll back and every read consults it.

This is the conditional statement analyzed in Chapter 10. Its premises need real authentication, isolation, replay protection, key lifecycle and operational review in a deployment. HUMA does not implement those controls.

**Counterexample:** If a restored snapshot also restores the grant table and the read path trusts that old table, a revoked grant may be accepted again. A hash of the snapshot does not prevent this.

## 8. Exact memory and lawful deletion

A requirement to delete private data may intentionally change the future observation result from Value(b) to Unavailable. That change is **not** an accidental failure of exact memory; it is a change in the declared authorized-retention domain.

A secure erasure design must consider keys, replicas, caches, indices, logs, backups and retained metadata. Merely deleting a public pointer or a high-level embedding does not establish complete erasure.

No public user records or actual secrets are used in this theoretical chapter.

## 9. Guarded cross-context events

For a translation between contexts c and d, an **admissible event** must specify at least:

- source principal and destination owner/scope;
- an authorization/consent precondition checked by an external authority;
- a policy epoch or version fence preventing stale grants;
- precisely which visible query results or provenance references may cross;
- an explicit Denied/Unavailable path when an obligation fails.

Only admitted, totalized events may enter the E_G model of Chapter 17. If a translation silently bypasses a permission check, a mathematical quotient theorem cannot rescue the system from an invalid event semantics.

## 10. Open questions (not established)

- Can practical permission certificates be expressed as local contracts that compose without leaking source identity?
- Can one construct useful Q_p-limited summaries for many principals while retaining a single protected exact history at acceptable cost?
- Which independent policy event classes commute without violating audit order or consent?
- How should lawful erasure transform a trace algebra without retaining disallowed source identity or exposing it through hashes?

These questions require security and privacy review before any implementation. Benchmarking, proof-assistant execution and CI remain disabled under the owner's freeze.
