# 31 — PCMM-A: Exactness Certificates on Coupled, Reachable Agent States

**Status:** Written mathematical theorem and proof for a finite deterministic fragment; not mechanically checked, not a security audit and not a novel CSP result. This chapter refines the open coupled-state problem from Chapters 17, 26, 29 and 30.

## 1. Why we need a reachable-state contract

The product-local synthesis in Chapter 26 assumes every combination of agent states is admissible. A system with synchronization, shared ownership or inter-agent invariants may admit only a subset of these combinations.

Let V be a finite set of agent/context variables. Each local state has a finite domain D_i, with |D_i| <= d. Let a finite collection of extensional, typed constraints R_a on variable neighborhoods C_a define

    G = {s in Product_(i in V) D_i :
         R_a(s|C_a)=true for every a}.

Assume G is nonempty. Constraints may reference synthetic source-identity, policy-epoch and version labels, but only when those labels are explicitly part of the finite state model. The abstract constraint model **does not** establish real authentication or authorization.

For every agent i, choose an explicitly provided abstraction

    alpha_i : D_i -> Z_i,

and alpha(s) = (alpha_i(s_i))_i. Let B=alpha(G), the set of *reachable* interface codes. The target B need not be a Cartesian product, and enumerating B is neither required nor assumed in the certificate decision procedure below.

## 2. Declared observation and update vocabulary

Each declared query q is a total function q:G -> A_q with tagged answers when needed: Value(v), Denied, Unavailable or a declared error. Queries have explicit input neighborhoods, or are represented by a bounded finite-domain circuit with auxiliary variables.

Each declared event e has a deterministic total raw-state transition

    U_e : Product_i D_i -> Product_i D_i

represented by local read and write relations and a fixed event interpretation. Whether it preserves the admissible set G must be **checked**: an inadmissible transition cannot be treated as a harmless post-state.

Queries and events must include every future operation that the certificate promises to cover. A grant, source withdrawal or erasure that later changes permitted observations belongs in the event vocabulary unless the certificate explicitly restricts its valid horizon.

The interface is **G-exact** if there exist total abstract functions on B such that for every s in G,

    q(s) = q_hat(alpha(s))                    (QC-G)
    alpha(U_e(s)) = V_e(alpha(s)),           (EC-G)

and every U_e(s) belongs to G. Outside G the abstract functions need not have defined semantics.

## 3. The three witness-obstruction families

For a fixed candidate alpha, define three kinds of finite **counterexample search**.

**G-CLOSE(e,a):** An admissible starting state violating a post-state constraint:

    s in G,   R_a(U_e(s)|C_a)=false.

If any such state exists, event e fails closure on G. Checking all individual constraints a suffices.

**G-QUERY(q):** Two admissible states with the same interface code but different declared query outputs:

    s,t in G,
    alpha(s)=alpha(t),
    q(s) != q(t).

**G-EVENT(e,j):** Two admissible states with the same interface code whose post-event interface codes differ at written coordinate j:

    s,t in G,
    alpha(s)=alpha(t),
    alpha_j(U_e(s)_j) != alpha_j(U_e(t)_j).

For an event that leaves other coordinates unchanged, it is sufficient to check each written coordinate j. In the general case check every output coordinate. A full two-state witness may have identical source interface codes but differ on hidden raw details; such a witness is exactly the reason the proposed abstraction is not update-compatible.

Represent each obstruction as a finite constraint-satisfaction problem (CSP). A G-QUERY or G-EVENT problem uses *two copies* of the raw variables, with equality constraints on their abstract codes; a G-CLOSE problem uses one copy and the event's post-state relations. Additional variables may encode function outputs and tagged query outcomes.

**Important:** Construction of the CSP must faithfully encode the exact local functions. A loose approximation that admits spurious witnesses is not a valid positive certificate.

## 4. Theorem 31.1 — Necessary and sufficient reachability-aware exactness

**Statement.** Assume G is nonempty, all declared functions are total and deterministic in the given finite-domain model, and all obstruction CSP encodings are exact. The candidate interface alpha is G-exact for every declared query and event **if and only if** every G-CLOSE, G-QUERY and G-EVENT obstruction instance is unsatisfiable.

### Proof

(**Only if**) Suppose alpha is G-exact. Event closure excludes any G-CLOSE witness. If G-QUERY had a witness s,t, the equal interface codes would imply equal q_hat outputs, contradicting q(s) != q(t). If G-EVENT had a witness, the equal codes would imply equal V_e outputs, contradicting their differing post-interface coordinate. Thus no obstruction is satisfiable.

(**If**) Suppose all obstructions are unsatisfiable. The G-CLOSE family ensures U_e(G) subset G for every e. Fix any z in B and choose s in G with alpha(s)=z; this is possible by the definition of B. Define

    q_hat(z) = q(s)
    V_e(z) = alpha(U_e(s)).

Unsatisfiability of G-QUERY ensures q_hat is independent of the choice of s. Unsatisfiability of G-EVENT, over all written/output coordinates, ensures V_e is independent of the choice of s. Event closure ensures V_e(z) belongs to B, so V_e:B->B is total. Both factorization equations hold by construction. Hence alpha is G-exact. QED.

### Corollary 31.2 — Exactness for any admitted finite future

For every declared query q, event word w and admissible initial state s,

    q(U_w(s)) = q_hat(V_w(alpha(s))).

**Proof.** Induction on w using the abstract event factorization, followed by query factorization. Every intermediate state remains in G by event closure. QED.

The theorem is **a standard finite-state quotient/factorization argument expressed as satisfiability of concrete counterexample formulas**. It does not establish a new universal memory algebra or security of a deployed system.

## 5. Why a bounded graph width matters (with the correct caveat)

Let L be the explicit size of a candidate's family of obstruction CSPs, and M the number of separate obstruction queries, counted across declared events, written coordinates, constraints and observations.

Assume a tree decomposition of each **augmented obstruction CSP primal graph** is supplied with width at most w. Also assume every CSP variable has at most D values and constraint membership can be checked with bounded input-size overhead.

Classical tree-decomposition dynamic programming decides satisfiability and, when satisfiable, can recover an actual witness using at most

    M * poly(L) * D^(w+1)

elementary table operations, with a comparable width-dependent space bound under a specified implementation model. Constant factors and the precise polynomial depend on the CSP encoding and decomposition.

This is a **conditional verification upper bound for a supplied candidate interface**, not the complexity of *discovering* a candidate interface. The witness CSP contains two copies of states and abstract-code equality constraints. Its width may exceed that of the original dependency graph. Bounding only the raw agent graph's treewidth is **not sufficient** for this complexity claim.

This method makes no measurements of actual disk, RAM, latency, energy or cloud cost.

## 6. The certificate should contain auditable evidence

A positive theoretical certificate includes:

1. the exact versioned local state domains, query/event functions, and constraint relations;
2. the candidate alpha_i maps and their authorized query scope;
3. the complete list of G-CLOSE, G-QUERY and G-EVENT obstruction formulas;
4. for each formula, a **valid unsatisfiability justification**, e.g. a complete tree-decomposition dynamic-programming table with checkable local transitions and separator consistency;
5. a proof that the generated formulas faithfully encode the intended raw functions;
6. an explicit fact that the current owner/policy obligations are **not** established by a symbolic CSP formula alone.

If an obstruction is satisfiable, a concrete finite pair of input states (and event or query) is a negative witness of interface inadequacy.

A program could later check certificates, but **no checker, executable or CI is authored or run in this document**.

## 7. Worked counterexamples

**Hidden source byte:** Two admissible states have the same compressed code but differ in a raw source byte. A future exact quote query distinguishes them; G-QUERY is satisfiable.

**Future grant:** Two currently denied reads return identical Denied. After an admitted Grant event, exact Value(payload) differs. If alpha merged the payloads, G-EVENT or G-QUERY must fail for the declared combined state.

**Coupled parity:** Let G={(0,0),(1,1)}, with q(a,b)=a XOR b and no events. A constant alpha is G-exact, since q is zero on all G. The same alpha would fail on the unrestricted Cartesian product. The G-aware certificate avoids claiming forbidden combinations are valid.

**Policy rollback:** If RestoreSnapshot is admitted but can overwrite the authoritative revocation state, the mathematical event semantics itself violates the intended security policy. An exactness certificate for that unsafe semantics cannot make it secure.

## 8. Boundaries and next theorem

Theorem 31.1 establishes a necessary-and-sufficient **verification criterion** for a *given* abstraction alpha, plus a tractability conditional on the **augmented obstruction CSPs**. It does not find an optimal alpha, decide arbitrary program equivalence, authenticate principal identity or prove legal data retention.

The next step is to study *synthesis* from a finite grammar of candidate interfaces and state exactly when a constructive search is tractable. In general, verifying one candidate is much easier than finding the best candidate.

## 9. Foundational literature (not a novelty claim)

- Eugene C. Freuder (1990), *Complexity of K-Tree Structured Constraint Satisfaction Problems*, AAAI: https://research.ucc.ie/en/publications/complexity-of-k-tree-structured-constraint-satisfaction-problems/
- Dániel Marx (2013), *Algorithmic Graph Structure Theory* (treewidth and CSP proof summary): https://www.cs.bme.hu/~dmarx/papers/marx-stacs2013-tutorial.pdf
- Chapters 13, 17, 22, 26 and 30 in this HUMA folder.

**Resource and privacy restriction:** Writing only. No private source data, unrelated project details, Python, Lean, tests, experiments, simulations, holdouts or hosted workflows.
