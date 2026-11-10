# 33 — PCMM-C: Bounded-Grammar Synthesis, Treewidth and a Non-Monotonicity Boundary

**Status:** Constructive decision theorem for a deliberately restricted finite model, plus a negative counterexample. The mathematical ingredients are standard finite search, CSP treewidth algorithms and quotient congruences. **No novel complexity classification or measured performance claim.**

## 1. What has actually been decided so far?

Chapter 31 characterizes whether a **given** interface alpha is exactly correct on an admissible, coupled state set G. The answer is yes exactly when all its closure, query and event obstruction CSPs are unsatisfiable.

This is not yet a synthesis algorithm: an arbitrary optimal interface might not be given, might involve an enormous grammar, or might require knowing which events and policy checks really occur in deployed code.

The aim here is narrower and auditable:

> Given a **finite, explicitly listed grammar** of permitted local interface maps and exact finite-domain counterexample encodings, decide whether at least one grammar candidate satisfies the declared contract and identify the one with minimum declared local code cost.

Every qualifier is important.

## 2. Model and candidate grammar

Fix a finite set of agents V with finite local raw state sets D_i and a nonempty coupled admissible set G defined by finite constraints.

For each agent i, the designer provides a finite, nonempty family

    Gamma_i = {alpha_i^1, ..., alpha_i^(r_i)}

of allowed total maps D_i -> Z_i^(j). For concreteness, each interface's codomain is its actual image; use surjective maps onto its reachable local codes where that is the intended storage measure.

Let

    Gamma = Product_i Gamma_i,
    R = Product_i r_i.

A complete candidate alpha in Gamma chooses one map per agent. Its fixed-length **concatenated local-code cost** is

    Cost(alpha) = Sum_i ceil(log_2 |Z_i^(alpha)|).

This deliberately counts only abstract code bits, not protected exact source archives, provenance, policy, version logs, query decoders, interface maps, CSP descriptions or cryptographic metadata.

If a designer instead wants the minimum globally encoded bits for the reachable code set B=alpha(G), the objective is ceil(log_2 |B|) and requires additional counting/symbolic analysis; the following theorem does **not** assert it computes that alternative cost.

## 3. Verification oracle with certified scope

For each alpha, generate the obstruction CSP family of Chapter 31:

    G-CLOSE(e,a), G-QUERY(q), G-EVENT(e,j).

Require exact encodings, including the two-copy construction of interface equality. Each witness CSP must be accompanied by a valid tree decomposition whose **augmented** primal graph has width <= w. Its variables have domain size <= D, including auxiliary variables, and constraint membership is explicitly bounded by the input representation.

Let M bound the total number of obstruction instances per candidate and let L bound their combined explicit encoding size. A classical tree-decomposition decision method can test an instance for satisfiability with poly(L) D^(w+1) arithmetic/table operations, under the standard supplied-decomposition model and accounting for relation-evaluation cost. An unsatisfiable instance certifies that the corresponding obstruction does not exist; a satisfiable instance yields a counterexample.

**Do not silently assume the original agent-dependency graph has the same width w.** Query inequality, output comparison, duplicated state variables, policy-state references and source-identity joins can enlarge the primal graph of the obstruction encoding.

## 4. Theorem 33.1 — Decidable best candidate in a finite grammar

**Statement.** Under Sections 2–3, and assuming each candidate's obstruction encodings and suitable decompositions are given or successfully constructed within the accounted resource bound, one can:

1. decide whether any alpha in Gamma is G-exact for all declared queries and events;
2. return one with minimum Cost(alpha) among such candidates, if any exists; or
3. return that **no candidate in Gamma** satisfies the contract.

The number of local tree-decomposition obstruction checks is at most

    R * M,

and an upper bound on their total mathematical table-operation work is

    O(R * M * poly(L) * D^(w+1)),

plus the explicit cost of candidate/decomposition generation, local cost comparison and witness reconstruction. The formula is *not* a universal worst-case runtime bound for arbitrary compressed software descriptions.

### Proof

Enumerate each of the finite R candidate tuples. For each, evaluate every G-CLOSE, G-QUERY and G-EVENT obstruction CSP using the given exact finite decision method. By Theorem 31.1, the candidate satisfies the declared contract if and only if all its obstructions are unsatisfiable. Retain every such candidate or update the currently best Cost record.

If none passes, every grammar candidate fails the necessary-and-sufficient criterion; consequently the grammar contains no admissible solution. Otherwise select a passing candidate with the smallest computed Cost. Finite enumeration is exhaustive, so no grammar solution has smaller Cost.

There are R candidates and at most M obstruction instances per candidate, giving at most R M checks and the stated conditional verification bound. QED.

### What the theorem does not say

- It does not prove global optimality among all possible abstractions.
- R=product_i r_i may be exponential in the number of agents. A bounded CSP treewidth does not eliminate this candidate-search cost.
- Width w need not stay bounded when the candidate interface or query vocabulary changes.
- The theorem does not certify whether source identity, security policy and event lists faithfully model a real service.
- Counting abstract bits is not counting actual storage or running cost.

## 5. A genuinely tractable but narrow subcase

Suppose only b of the agent interfaces may vary, with each of those agents having at most r alternatives; all remaining agent interfaces are fixed. Then

    R <= r^b.

For fixed b, r, w and D, and a polynomial number of explicitly sized events/queries/constraints with polynomial-time local evaluation, the enumerative synthesis decision is polynomial in the network description size.

This is a **parameter-restricted positive result**, not an automatic bound for arbitrary large networks. The assumption of a small adjustable set can be appropriate for a research-design iteration where most agent interfaces are already fixed and only a few are under review.

A larger research ambition would eliminate or improve the exponential r^b term for a nontrivial, precisely defined dependency class using compositional constraints or dynamic programming. That remains unresolved here.

## 6. Proposition 33.2 — Exactness is not upward-monotone under arbitrary interface refinement

It is tempting to claim that an interface that remembers more information is always safe if a coarser one was safe. That is **false** when future events must also act exactly on the representation.

**Counterexample/proof.** Let S={(x,y):x,y in {0,1}}. Take a single declared query q(s)=0, which is constant, and a deterministic total event

    U(x,y)=(y,y).

The constant abstraction

    alpha_0(x,y)=*

is exact: its query result is always 0, and its abstract transition is the identity on the singleton.

Now choose a *finer* abstraction

    beta(x,y)=x.

Beta distinguishes states that alpha_0 merges. Yet take s=(0,0) and t=(0,1). We have beta(s)=beta(t)=0, but

    beta(U(s))=0,
    beta(U(t))=1.

Thus ker(beta) is not stable under U, no function V satisfying beta o U = V o beta exists, and beta is **not exact** for the update contract.

Therefore arbitrary refinement of an exact quotient can break event compatibility. QED.

**Consequence for synthesis:** A naive search that only "adds remembered bits" and assumes every refinement remains safe is unsound. The terminating refinement algorithm of Chapter 26 succeeds because it enforces event congruence at each iteration; it does not rely on this false monotonicity assumption.

This counterexample is an elementary observation about congruences, not an original impossibility result.

## 7. Source and policy dimensions can increase both state cost and graph width

If a source-identity query distinguishes a and b, any exact candidate must retain their distinction in its reachable internal state or through a declared protected exact-reference lane. A fan-in alias that merges them may make G-QUERY satisfiable.

If a future Grant changes the read result from Denied to Value(payload), two currently identical public views may correspond to different internally required states, as in Chapter 23. Exactness of an internal candidate must include those events and outputs.

Adding a shared policy service or attribution join can produce a high-width augmented CSP even when each user-facing agent has only a few neighbors. This is a mathematical reason to include authority/provenance in the **dependency structure**, not to hide them as external cost-free conditions.

An authentic authorization check, privacy assessment and lawful erasure procedure cannot be inferred from a small treewidth.

## 8. Next theorem target (not solved)

**PCMM-N1-OPT:** Identify a nontrivial subclass of coupled, typed and time-scoped networks in which the **synthesis search**, not only the verification of one supplied interface, can be carried out in

    poly(input_size) * f(width, alphabet_size, policy_scope_width)

time for a stated objective, with a sound and complete certificate and an explicit lower-bound or optimality proof.

The missing step is a *compositional interface-search construction* that avoids enumerating the Cartesian grammar Gamma, or a formal impossibility barrier showing why such avoidance requires stronger assumptions.

Even a proof of a restricted negative complexity result would be more scientifically valuable than asserting an unmeasured compression advantage.

## 9. Required prior art

- Eugene Freuder (1990), finite CSPs of bounded treewidth: https://research.ucc.ie/en/publications/complexity-of-k-tree-structured-constraint-satisfaction-problems/
- Dániel Marx, graph-structural complexity tutorial: https://www.cs.bme.hu/~dmarx/papers/marx-stacs2013-tutorial.pdf
- Existing work on CSP width and parameterized complexity: https://www.sciencedirect.com/science/article/pii/S0022000009000300
- Classical partition refinement, finite automata minimization and quotient congruences, as discussed in HUMA Chapters 13, 26 and 30.

**Execution and privacy gate:** The results are hand-written arguments only. No experiments, code, benchmark, test, formal proof assistant, data transfer, hosted runner or unrelated private project details.
