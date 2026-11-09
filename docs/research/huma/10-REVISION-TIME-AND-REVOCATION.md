# 10 — Temporal Memory, Revision and Revocation: A Bounded Theory

**Status:** Written-only formal model with conditional propositions. It is not a deployed security protocol, authorization system, audit log or backup implementation.

## 1. Three distinct clocks or versions

A memory item often involves:

- **Valid time:** an interval during which the underlying claim or event purports to apply.
- **Recorded time:** when a system committed the record.
- **Policy version:** which current authority/consent decision permits use of the record.

These must not be silently identified. In particular, a source text's original publication year is not necessarily the date the system recorded it, and a snapshot's timestamp is not evidence that its former access permissions are still valid.

## 2. Historical data state

Let the historical event sequence at logical time t be

    H_t = (e_1, ..., e_t).

For an explicitly defined transition function Apply and initial data state D_0, define

    D_t = Fold(Apply, D_0, H_t).

A snapshot at index k stores a representation of D_k together with an exact reference to its applied event prefix and format version.

### Proposition 10.1 (deterministic replay under complete inputs)

Assume Apply is deterministic, every event is represented exactly, format/version semantics are fixed and the same initial state D_0 is used. Then replaying the same ordered event prefix H_t gives the same D_t.

**Proof:** Induction on prefix length. Length zero yields D_0. If equal states are obtained after i events, applying the same deterministic function with the same event e_(i+1) produces equal states after i+1 events. QED.

**Limitations:** This is a mathematical statement about deterministic replay, not a proof of an authentic event history or durable storage. Nondeterministic model calls, wall clocks, omitted external inputs, hidden random seeds and different versions break the assumptions.

## 3. Current provenance availability

Let A_t be the set of currently available and admissible source identifiers for a particular authorized scope at time t.

For a claim with provenance P in N[X], define

    Supports_t(P) := (ev_(A_t)(P) > 0).

After a source withdrawal, A_(t+1) can be smaller than A_t. Historical lineage P can remain attributable for permitted retention while the *current support predicate* changes. This separates:

1. a historical record that a source was used;
2. the current availability of that source;
3. whether a semantic inference is valid;
4. whether the requesting principal has access to see it.

In particular, source withdrawal is **not the same operation** as a user's revocation of a reading capability. They have different policy implications.

### Example

For P=ab+c, availability A_t={a,b,c} gives support. Withdrawal of a leaves A_(t+1)={b,c}; the c route still survives. But the claim is not thereby proven true.

## 4. Policy epoch model for authorization

Consider a simplified principal p, resource r and grant epoch g. A grant is uniquely identified by (p,r,g); epochs are not reused. Let G_t be a **current, authoritative policy history**, maintained independently from restorable data snapshots.

Assume:

- every grant epoch is created by a validly authenticated authority (an external requirement);
- revocation permanently disables that epoch; re-grant requires a fresh epoch;
- the authority system refuses rollback of its committed revocations (an external requirement);
- reads always query the current policy state G_t rather than the policy state embedded in a data snapshot.

Define

    Authorized_t(p,r,g)
      iff Issued_t(p,r,g) and not Revoked_t(p,r,g)

subject to the policy's additional scopes, consent and expiry rules. If multiple grant epochs exist, the access decision is a separate existential or policy expression over **current** valid epochs.

### Proposition 10.2 (no stale-grant resurrection: conditional)

If an epoch g was validly revoked by time t and revocation is monotone in the authoritative G_t, restoring any older *data-only* snapshot D_k with k<t cannot make Authorized_t(p,r,g) true.

**Proof:** Restoring D_k does not modify authoritative policy G_t by assumption. Since g is revoked in G_t and cannot be reused, its revocation predicate remains true. The authorization expression is therefore false regardless of D_k. QED.

**Exactly what this does NOT prove:** It does not show that G_t is really tamper-proof, keys are genuine, a deployment has implemented those checks, other epochs cannot authorize the read, or a human has withdrawn consent according to applicable law. These are separate security and governance gates.

## 5. Counterexample when policy rollback is not separated

At time k, a grant g is active and a snapshot records it. At time t>k, g is revoked. If restoring snapshot k also restores *authoritative policy* to its older state, a read can again pass. The data history is correct **relative to that old snapshot** but the security result is wrong.

Therefore "has snapshots", "has hashes" and "has event sourcing" are insufficient specifications for rollback-safe authorization.

The OpenWorld gate should explicitly test/verify anti-rollback design only when experimental work is separately authorized. No test is executed now.

## 6. Two-dimensional time and contradictory records

For statements that change, a memory record may have:

    (statement, valid_from, valid_to, recorded_at, superseded_at).

Suppose an original text asserts proposition phi at an earlier date and a later editor disputes its translation. The new annotation should create a new interpretation record connected to the earlier one; it must not rewrite an old citation into an unqualified fact.

Different contexts and interpretations can coexist. A current knowledge view may filter versions according to a declared conflict-resolution policy, but the underlying raw sources remain traceable for permitted retention.

This is a design approach influenced by bitemporal database modeling; no particular history schema or conflict semantics is claimed as universally correct.

## 7. Commutativity of updates: sufficient conditions only

Let U_a, U_b be deterministic event transformations on a state consisting of independent components A and B.

If:
- U_a reads/writes only component A;
- U_b reads/writes only component B;
- neither modifies shared authorization, dependencies or version counters that affect the other;

then

    U_a(U_b(M)) = U_b(U_a(M))

for the **data projection** whose components they operate on.

This is a product-state commutation argument, not permission to reorder append-only audit logs. Even independent data updates can have different timestamped event-history order, so full historical records need not be equal.

### Counterexample

A source withdrawal changes which citations are currently admissible, while a derived-claim update reads the previous availability. Their order can change the result. These events must not be treated as independent without a transactional or versioned dependency rule.

## 8. The right to erasure vs exact memory

A strict invariant "retain everything forever" is incompatible with some valid deletion obligations.

A safer layered model distinguishes:
- protected records retained only for their authorized lifecycle;
- archival metadata and redacted provenance where lawful;
- encrypted payloads with keys subject to owner and retention controls;
- deletable source content, indexes, replicas and backups under documented policy.

**Caution:** cryptographic erasure is conditional on correct key lifecycle, exclusive ciphertext dependency and backup policies. Hashes of low-entropy personal data can themselves leak information, so retaining a digest does not automatically solve privacy compliance.

No lawful-retention determination or personal-data deletion mechanism is implemented in this theoretical chapter.

## 9. Open theorem and security obligations

- Specify an access-control logic whose proof obligations include owner scope and consent, not just source availability.
- Model concurrent updates, partial failures and stale replicas.
- Define snapshots that can be restored without reauthorizing revoked capabilities.
- Characterize what metadata must be removed when an authorized erasure request is processed.
- State precise consistency and ordering semantics for concurrent revisions.
- Prove which query projections can be reconstructed after a payload is removed and which must correctly return unavailable.

The theory-only phase can document these conditions and counterexamples. Implementing or testing them remains outside the current scope.

## References

- OpenWorld [architecture invariants](../../ARCHITECTURE.md) and [governance policy](../../GOVERNANCE-REVIEW-POLICY.md).
- W3C [PROV-O](https://www.w3.org/TR/prov-o/) for descriptive provenance vocabulary.
- Snodgrass, *Developing Time-Oriented Database Applications in SQL*, for valid-time and transaction-time modeling.
- Standard event sourcing, capability-security and anti-rollback literature: future detailed verification required before choosing a concrete protocol.
