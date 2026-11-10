# 26 — HUMA-N1: Constructing the Coarsest Locally Exact Memory Interfaces

**Status:** Theory-only finite-state construction and written proof. The procedure is not executed. It is an instance of classical partition refinement/congruence methods, **not a demonstrated new mathematical theorem**.  
**Depends on:** Chapters 13, 17, 22 and 25.

## 1. The precise synthesis problem

Earlier chapters assumed that a designer provides local interface maps. Here the interface itself is **derived** from a finite, explicitly declared contract.

Let V be a finite set of agent/context indices. Each local raw state set S_i is nonempty and finite. Define the full product state space

    S = product_(i in V) S_i.

Every query q has a declared read neighborhood N_q subset V and a deterministic total function

    q_loc : product_(i in N_q) S_i -> A_q.

Every event e has a declared read neighborhood N_e and write neighborhood T_e subset N_e, with deterministic total function

    u_e : product_(i in N_e) S_i -> product_(j in T_e) S_j.

The global event changes only coordinates in T_e. Error, rejection and Denied outcomes are assumed to have been **totalized into explicit state and result types** where needed. Undeclared effects, clocks, external sources, randomness or access-control calls are out of scope.

We seek a tuple of local equivalence relations

    R = (R_i subset S_i x S_i)_(i in V)

such that the product quotient maps alpha_i:S_i -> S_i/R_i yield *exact* query and event interfaces, in the sense of Chapter 22.

Equivalence classes represent which **local raw distinctions** may be forgotten for precisely the declared queries and events. A coarser relation (larger set of equivalent pairs) forgets more. The optimality in this chapter is **only within product-of-local-quotients abstractions** and is not a globally minimal shared encoding.

## 2. Two elementary feasibility conditions

Call a tuple R **contract-admissible** if:

**Q-compatibility:** for every query q and two local-neighborhood assignments x,y, whenever x_i R_i y_i for all i in N_q,

    q_loc(x) = q_loc(y).                                [Q]

**E-compatibility:** for every event e, all x,y in its read neighborhood with x_i R_i y_i for all i in N_e, and every written component j in T_e,

    (u_e(x))_j R_j (u_e(y))_j.                          [E]

These conditions are equivalent to the existence of well-defined deterministic functions on the corresponding quotient neighborhoods:

    q_hat_q(product_i [x_i]) = q_loc(x),
    v_e(product_i [x_i]) = product_(j in T_e) [(u_e(x))_j].

The conditions make the right sides independent of the representatives selected. This is exactly the local-factorization guarantee needed for Theorem 22.1.

**Important:** The stated necessity is relative to the **full Cartesian product** of local states and total local rules. Under coupled admissibility guards, some assignments may be unreachable. Requiring [Q] and [E] for all local assignments remains sufficient but can be conservative.

## 3. A monotone refinement operator on local equivalence relations

Let top_i = S_i x S_i be the indiscrete equivalence relation. For a tuple R of equivalence relations define the following two relations on S_i.

**Direct query indistinguishability** Q_i:

    x Q_i y
    iff for every q with i in N_q, and for every fixed
        assignment z to N_q \ {i},
        q_loc(z with coordinate i=x)
        = q_loc(z with coordinate i=y).

If no declared query reads i, Q_i is the universal equivalence relation.

**One-coordinate event stability** E_i(R):

    x E_i(R) y
    iff for every e with i in N_e, every fixed
        assignment z to N_e \ {i}, and every j in T_e,
        (u_e(z,i=x))_j R_j (u_e(z,i=y))_j.

If no declared event reads i, E_i(R) is universal.

For each fixed R these are equivalence relations: Q_i is the intersection of kernels of deterministic functions; E_i(R) is an intersection of inverse images of equivalence relations under deterministic output maps.

Define

    T(R)_i = R_i intersection Q_i intersection E_i(R).

Start with R^0_i=top_i for every i and iterate

    R^(k+1) = T(R^k).                                   [26.1]

This is a *mathematical prescription*, not a request to run software.

## 4. Lemma 26.1 — Descending stabilization

The sequence R^0, R^1, ... consists of equivalence-relation tuples and is descending componentwise. It stabilizes after at most

    sum_(i in V)(|S_i|-1)

strict **global** refinement rounds (although a final equality check may add one iteration).

### Proof

Intersections of equivalence relations remain equivalence relations, and T(R)_i subset R_i, so each step refines or keeps the same partition.

If R^(k+1) differs from R^k, at least one local partition splits a block, increasing the total number of equivalence classes over all local partitions by at least one. The initial total is |V| and the maximum is sum_i |S_i|. Hence at most sum_i(|S_i|-1) strict rounds occur. Once an iterate is unchanged, all later iterates are unchanged because T is deterministic. QED.

The result assumes finite S_i; it is not a termination theorem for arbitrary continuous memory spaces.

## 5. Lemma 26.2 — A fixed point is contract-admissible

Suppose R*=T(R*). Then R* satisfies [Q] and [E].

### Proof

For a query q, take two neighborhood assignments x,y with x_i R*_i y_i at every read coordinate. Connect x to y by replacing one coordinate at a time. For any step replacing coordinate i, the unchanged other coordinates form a fixed assignment; because R*_i subset Q_i, the query value is unchanged. Chaining the finitely many equalities gives q_loc(x)=q_loc(y), proving [Q].

For an event e use the same coordinate-replacement chain. A step replacing coordinate i has inputs x_i R*_i y_i, and because R*_i subset E_i(R*), its corresponding written outputs are R*_j-equivalent for each j in T_e. By transitivity of R*_j over all steps, the outputs of u_e(x) and u_e(y) are equivalent for each written component. This proves [E]. QED.

Consequently, the quotient interfaces exist and Theorem 22.1 applies to **every finite event word and query** from the declared contract.

## 6. Theorem 26.3 — Coarsest locally admissible product quotient

**Statement.** The stabilized tuple R* from (26.1) is contract-admissible and is **the greatest tuple under componentwise relation inclusion** among all contract-admissible local equivalence-relation tuples. In other words, for every contract-admissible H,

    H_i subset R*_i for all i in V.

Thus R* merges at least as many local state pairs as any other product-of-local-equivalence quotient satisfying the same declared contract.

### Proof

Admissibility follows from Lemma 26.2.

For maximality, fix any contract-admissible tuple H. We prove by induction on k that H_i subset R^k_i for all i.

At k=0 this is immediate because R^0_i is universal.

Suppose H_i subset R^k_i for every i. Take any x H_i y.

- Because H satisfies [Q], replacing x by y at coordinate i while all other query inputs are fixed cannot change any query's value. Hence x Q_i y.
- Because H satisfies [E], replacing x by y at input coordinate i while all other event inputs are identical makes the written outputs H_j-equivalent. By the induction hypothesis H_j subset R^k_j, those outputs are also R^k_j-equivalent. Hence x E_i(R^k) y.
- The induction hypothesis also gives x R^k_i y.

Therefore x belongs to all three relations defining T(R^k)_i=R^(k+1)_i. So H_i subset R^(k+1)_i. The induction is complete.

When the sequence stabilizes, H_i subset R*_i for every i. QED.

### Corollary 26.4 — Minimal local memory cardinalities (restricted class)

Let Z_i=S_i/R*_i. Any other admissible local product quotient with equivalence relations H_i has

    |S_i/H_i| >= |Z_i|  for each i,

and therefore at least product_i |Z_i| global **product codes** when all tuples are admitted.

This is a **cardinality** minimality result within the product-of-local-quotients class, not a universal theorem about shortest serialized files, encrypted archives, metadata, shared dictionaries, network messages or task-based loss. Under coupled constraints, the reachable global code cardinality can be smaller than the full product, and further global encoding may be possible.

## 7. A bounded-neighborhood analysis of synthesis effort

Assume |S_i|<=m, and each query/event has at most d read coordinates. Directly checking the Q_i and E_i(R) relations for all ordered local pairs and assignments to other read coordinates requires at most a constant-factor multiple of

    C = sum_q |N_q| m^(|N_q|+1)
        + sum_e |N_e| |T_e| m^(|N_e|+1)

local evaluation comparisons per refinement round.

The descending iteration has no more than

    K = sum_i (|S_i|-1)

strict rounds, plus one termination check. With constant-time tabular state access and equivalence-class comparison, the number of local comparisons is bounded by

    O((K+1) C).

For fixed m,d and polynomially many declared local events and queries, this is polynomial in the explicitly enumerated local contract description, without enumerating the full global state space of size product_i |S_i|.

This complexity measure excludes materializing a huge query or event circuit, discovering true read neighborhoods, proving an arbitrary program has no hidden effects, bytes for exact source archives, and operational costs. It is not an experimentally measured speedup.

## 8. Three conditions that must not be hidden

**Unrestricted product:** The maximality claim is for full product local states and total declared local rules. For a coupled admissible subset G, the same R* remains a conservative sufficient abstraction when admitted events preserve G, but can merge fewer states than an abstraction specialized to reachable G.

**Fixed contract vocabulary:** A new source-identity query, grant event, revocation event or raw-content request may split previously merged classes. An old R* is not automatically correct for an expanded query or event vocabulary.

**No source authentication theorem:** A query returning an attributed citation may be preserved exactly without the citation itself being genuine, authorized or logically sufficient. Source-provenance semantics and permission enforcement are independent obligations.

## 9. Counterexamples

1. **Future hidden read:** If an event reads a hidden local bit and writes it into another agent's observable memory, E_i(R) eventually distinguishes that hidden bit, even if no present query reads it.
2. **Alias collision:** If two distinct source identities become the same target alias and attribution is a declared query, Q_i forces them apart (unless the query contract intentionally and legally discards the distinction).
3. **Undeclared policy event:** If a Grant event is omitted but later occurs, an earlier minimality proof says nothing about its effects.
4. **Coupled only:** If global compatibility forbids almost all Cartesian tuples, local exhaustive refinement can over-refine relative to what is actually reachable. Do not call it a universally minimal global memory.

## 10. Prior art and next research step

Theorem 26.3 is a constructive *greatest congruence* / partition-refinement result. Related fields include automata minimization, abstract interpretation, bisimulation congruences, compositional model checking and finite relation refinement.

**Research task:** study a restricted class of *coupled, partial and principal-scoped* agent networks in which one can derive a coarsest **reachable-state** interface from separately checkable local certificates, retaining source identity only for authorized provenance questions. That more difficult task remains open; HUMA does not yet own a new mathematical theorem.

**Freeze:** This chapter was written as Markdown only. No algorithm was executed, no tests or simulations were run, and no GitHub Actions workflow was invoked.
