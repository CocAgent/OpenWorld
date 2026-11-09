# 22 — HUMA-N1: Graph-Local Certificates for Multi-Agent Memory

**Status:** Written-only finite deterministic theorem, proof and counterexamples. The proof uses established compositional abstraction and assume–guarantee techniques; it does not establish mathematical novelty. No executable software, proof checker or experiment is involved.

## 1. Problem and distinction

A collection of agents can retain different private histories, exchange selected claims and jointly update conclusions. The *information transferred* may be a compressed view, while the authoritative source record and the authorization to read it remain elsewhere.

We ask for a **certificate of exactness for a declared contract**: which future observable answers can be recovered from these views after all admitted local events? The answer must not silently promote an unverified attribution into a proof, disclose an unauthorized source, or assume that a source hash constitutes a grant.

The following result is deliberately restricted to finite deterministic local transition systems. Its value is a checkable baseline, not a proof that arbitrary multi-agent memory or trust is safe.

## 2. Typed dependency hypergraph and local states

Let V be a finite set of agent/context vertices. For each i in V choose:

- a finite, nonempty local raw state set S_i;
- a finite interface code set Z_i;
- a **surjective** abstraction alpha_i:S_i -> Z_i (otherwise replace Z_i by the image of alpha_i; the theorem concerns reachable interface codes).

Let S=product_(i in V) S_i, Z=product_(i in V) Z_i and alpha=product_i alpha_i. Agent identifiers and source identifiers are explicitly different sorts. Principal identity, current grants and source-availability markers can be components of local states **only when declared**; they are never inferred from a provenance polynomial.

Every declared global query q has a read neighborhood N_q subset V and is given by a total local function

    q_loc: product_(i in N_q) S_i -> Result_q.

The global query is q(s)=q_loc(s|N_q). The result type includes tagged Denied/Unavailable if the specified authorized observation requires them.

Every declared global event e has a read neighborhood N_e subset V and a write neighborhood T_e subset N_e; it is specified by a total local rule

    u_e: product_(i in N_e) S_i -> product_(j in T_e) S_j.

It replaces exactly the coordinates in T_e and leaves all other coordinates unchanged. Rejections must be represented explicitly in the local transition contract. An event that reads a remote policy service, clock, random seed, unregistered source, or external tool without declaring it is **outside the model**.

The graph is a directed hypergraph: each event is a typed hyperedge from N_e to T_e, while each query observes N_q. Locality is a substantive assumption about a specified transition system, not something proved merely by drawing a diagram.

## 3. The local interface certificate

For each query q, supply a total decoder

    q_hat: product_(i in N_q) Z_i -> Result_q

and require **query exactness** for every local raw input x in product_(i in N_q) S_i:

    QC(q): q_loc(x) = q_hat(alpha_Nq(x)).                     (22.1)

For each event e, supply a total abstract local transition

    v_e: product_(i in N_e) Z_i -> product_(j in T_e) Z_j

and require **event closure** for every local raw input x in product_(i in N_e) S_i:

    EC(e): alpha_Te(u_e(x)) = v_e(alpha_Ne(x)).                (22.2)

These are equalities on *declared* local domains, not evidence that the real agent's behavior or permissions match them. If partial rules are needed, a typed Rejected/Denied result must be included consistently or the theorem must explicitly restrict to a forward-invariant domain.

Define the global abstract event V_e on Z by replacing T_e with v_e(z|N_e) and leaving all other interface coordinates unchanged.

### Theorem 22.1 — Future-observation preservation from local contracts

If QC and EC hold for every declared query and event, then for every raw global state s in S, every finite event word w and every declared query q,

    q(U_w(s)) = q_hat((V_w(alpha(s)))|N_q).                    (22.3)

In particular, if alpha(s)=alpha(t), then **all** declared future observation results agree after any common admitted event sequence.

#### Proof

For one event e, coordinates outside T_e remain unchanged both in the raw and abstract transitions. On each changed coordinate, (22.2) gives the equality between the interface of the raw update and the abstract local update. Thus

    alpha(U_e(s)) = V_e(alpha(s))

for all s, regardless of the total size of V. By induction on the number of events, the relation extends to each word w:

    alpha(U_w(s)) = V_w(alpha(s)).

Apply QC(q), (22.1), to the raw neighborhood of U_w(s). Its abstract inputs equal those in V_w(alpha(s)); this yields (22.3). If alpha(s)=alpha(t), their abstract trajectories are identical under the same abstract event word, so all admitted query results agree. QED.

This is a standard homomorphism/simulation induction, **not an original theorem**.

## 4. A stronger, coupled-state variant with interface-local guards

Many multi-agent states obey cross-context consistency constraints. Let each constraint a have scope C_a subset V and a predicate

    g_a: product_(i in C_a) Z_i -> {true,false}.

Define the admissible raw state set

    G = {s in S | for every a, g_a(alpha(s)|C_a)=true}.

The admissibility constraints depend only on the interfaces (an **interface-saturation** assumption). Set B=alpha(G).

For each event e and every constraint a whose scope C_a intersects T_e, require that the guard is preserved under the abstract update **for every interface assignment on N_e union C_a for which that guard holds**:

    g_a(z|C_a)=true
       ==> g_a(V_e(z)|C_a)=true.                             (22.4)

Other guards are unaffected because the event does not change their coordinates.

### Corollary 22.2 — Closure on coupled admissible states

If (22.1), (22.2) and (22.4) hold, then every declared event maps G to itself and equation (22.3) holds for all s in G.

**Proof.** Under (22.2), the abstract view after a raw event is V_e(alpha(s)). Each constraint intersecting T_e remains true by (22.4); every nonintersecting constraint sees unchanged coordinates. Thus U_e(G) subset G. Theorem 22.1 applies to all consecutive states. QED.

Condition (22.4) is deliberately **stronger** than merely requiring preservation over globally extendible assignments. It avoids a hidden global-state search, at the possible cost of rejecting some valid systems.

## 5. Local verification cost in a specified input model

Suppose:

- |S_i| <= m for every vertex;
- each query neighborhood has size at most d;
- each event neighborhood has size at most d;
- each union N_e union C_a, for every constraint a meeting T_e, has size at most b;
- local rules, abstract views and guards are explicitly given as bounded-cost evaluable tables or circuits and **their true dependency scopes are trusted or separately proved**.

Exhaustively checking QC(q) needs at most m^d local raw assignments. Checking EC(e) needs at most m^d assignments. Checking each relevant guard-preservation condition needs at most m^b interface assignments (or m^b as a conservative bound since |Z_i|<=m when each alpha_i is onto its chosen image).

A simple upper bound on the **number of local certificate cases** is

    O( (|Q| + |E|) m^d
        + |{(e,a): T_e intersects C_a}| m^b ).               (22.5)

A per-case evaluation cost and certificate-description size must be multiplied separately; this is **not a RAM, latency or monetary cost claim**.

For fixed m, d and b with polynomially many declared queries, events and guards, this bound is polynomial in the input listing size and avoids enumerating every member of a global raw product of size up to m^|V|.

**Critical caveat:** Discovering the interface maps, proving an arbitrary program's read/write locality, checking that all relevant real-world actions were included, or finding minimal d,b may be computationally hard or undecidable. The bound is for **verifying explicitly supplied finite local contracts**, not for arbitrary software certification.

## 6. Exactly which source and policy queries can be preserved?

A source-identity query (e.g. "was citation a used?") may be included in Q. Then QC requires that the interface or a separately authorized source-ref mechanism distinguish the source identities needed for that query. It is invalid to replace two distinguishable citations with a single alias and still claim exact attribution.

A policy decision is **not** a polynomial provenance valuation. To model principal-specific reads, add policy data as an explicit state component with read neighborhoods; model grant/revoke as declared events. The theorem will then preserve the declared tagged outcomes if QC and EC actually hold for those additional events and queries. It does not imply that a deployment has authentic principal identities or anti-rollback authority.

A private exact source archive can exist outside the public agent view. The abstract code is only sufficient for the chosen query/event contract. It must not claim lossless restoration of raw bytes unless exact restoration is also an admitted query and the model includes an authorized path to those bytes.

## 7. Failure cases

**Hidden remote read.** An event is declared to inspect only agent A but its implementation also reads agent B's hidden state. The N_e locality assumption is false, so no sound local certificate has been established.

**Insufficient future authorization.** Two states produce Denied now. A later grant reveals different hidden texts, but the abstract state merged their values without a protected exact store. The grant/read event contract cannot satisfy EC and QC simultaneously; Chapter 18 gives the two-state counterexample.

**Guard outside the interface.** A global constraint depends on the raw source byte rather than any alpha_i. The assumption G=alpha^{-1}(B) is false. The local guard proof no longer establishes closure.

**Identity alias collision.** A and B cite different source records with the same target alias. Positive path availability might survive, while exact attribution queries cannot be answered. Chapter 19 shows why an injective rename or explicit privileged reference is required for such a query contract.

**Confusing a trace with a theorem.** A source path recorded by an agent has type Trace, not Proof, regardless of which other agent received it. The type-separation rule of Chapter 08 remains mandatory.

## 8. Research contribution still missing

Theorem 22.1 and Corollary 22.2 formalize a **known** compositional abstraction pattern. A genuinely interesting HUMA-N1 result would require new constraints that give a useful, independently checkable and provably efficient combination of:

- locally typed provenance and its source identity requirements;
- principal/epoch-specific authority and legal erasure;
- heterogeneous partial cross-context transformations;
- a graph-local certificate construction, not merely verification of a supplied witness.

Do not claim that this chapter resolves the general problem or that experimental resource savings have been demonstrated.

## 9. Prior art and external verification

- Compositional verification and assume–guarantee reasoning: https://www.cambridge.org/core/journals/theory-and-practice-of-logic-programming/article/compositional-verification-in-rewriting-logic/BB7AC42A9DA43517A3D1C5BE0AE40F0C
- Provenance semirings (Green, Karvounarakis, Tannen): https://www.cs.ucdavis.edu/~green/papers/pods07.pdf
- OpenWorld HUMA Chapters 13, 17, 18 and 19.

No source code, CI, simulation, benchmark, proof assistant or private research material is added by this chapter.
