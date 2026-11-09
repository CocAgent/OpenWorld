# 14 — Guarded Cross-Context Translation and Non-Collapse

**Status:** Written conditional theorem, not independent peer review or formal proof-assistant verification. This is a standard simulation/observability argument specialized to HUMA terminology; do **not** claim it is novel.

## 1. The problem: equal symbols need not mean equal knowledge

A single term can be meaningful in two contexts but denote different objects. A textual mapping between them is not necessarily faithful. Likewise, converting a source trace into a different provenance alphabet may collapse distinct citations.

HUMA should require *witnesses with explicit preservation properties*, rather than asserting all knowledge systems embed naturally into one untyped universal space.

The aim here is narrow: state conditions under which a target representation **cannot merge two source states that the declared source observations and future events can distinguish**.

## 2. Two finite deterministic contexts

Let

    A = (S_A, E_A, Q_A, {U_e}, {q})
    B = (S_B, E_B, Q_B, {V_f}, {r})

be finite deterministic observation/transition systems as in Chapter 13. Query outputs are tagged, so Denied, Unavailable and Value(v) are distinguishable, and no unauthorized payload is assumed observable.

Choose a nonempty subset D subset S_A that is **forward invariant** under every declared source transition:

    s in D implies U_e(s) in D, for all e in E_A.

A **strong simulation witness** consists of:

- F:D -> S_B, a total state mapping on the domain D;
- k:E_A -> E_B, a mapping of source events to target events;
- eta:Q_A -> Q_B, a mapping of source queries to compatible target queries;

such that, for all s in D, e in E_A and q in Q_A,

    F(U_e(s)) = V_(k(e))(F(s))              (transition compatibility)
    q(s) = eta(q)(F(s))                     (observation compatibility).

Results may be mapped through an explicit type-preserving output adapter; for this theorem, equal result codomains are assumed.

No assumption is made about how the mapping was discovered or about its scientific value. In a real permissioned system, admissible data disclosure remains an additional external gate.

## 3. Lemma 14.1 — Simulation over an event word

Extend k letterwise to k*:E_A* -> E_B*. For every s in D and word w in E_A*,

    F(U_w(s)) = V_(k*(w))(F(s)).

**Proof.** By induction on the length of w. For the empty word, both sides are F(s). Assume the claim holds for w and append event e. Since D is forward invariant,

    F(U_(we)(s))
      = F(U_e(U_w(s)))
      = V_(k(e))(F(U_w(s)))
      = V_(k(e))(V_(k*(w))(F(s)))
      = V_(k*(we))(F(s)).

QED.

**Failure if domain invariance is omitted:** U_w(s) may leave D, rendering F(U_w(s)) undefined. A statement quantified over all event words would then be ill-formed.

## 4. Theorem 14.2 — Non-collapse of source-distinguishable states

Let ~=_A denote dynamic observational equivalence on D induced by E_A and Q_A, and ~=_B the equivalence on S_B induced by E_B and Q_B.

**Statement:** If F,k,eta form a strong simulation witness, then for all s,t in D,

    F(s) ~=_B F(t)  implies  s ~=_A t.

Equivalently, if a declared source query can distinguish s from t after some declared source event sequence, the translated target states must also be distinguishable by the mapped target query and event sequence.

### Proof

Assume F(s) ~=_B F(t). Fix any source event word w and any source query q.

By observation compatibility applied to U_w(s) and U_w(t), and Lemma 14.1:

    q(U_w(s))
      = eta(q)(F(U_w(s)))
      = eta(q)(V_(k*(w))(F(s))).

Since F(s) ~=_B F(t), the target observation after the particular target word k*(w) agrees:

    eta(q)(V_(k*(w))(F(s)))
      = eta(q)(V_(k*(w))(F(t))).

Reversing the same two compatibility equalities for t gives the result q(U_w(s))=q(U_w(t)). This holds for all w and q, hence s ~=_A t. QED.

### Corollary 14.3 — An observable memory lower bound survives translation

Let K_A be the number of ~=_A equivalence classes in D. Let K_B(F(D)) be the number of **distinct target** ~=_B classes intersecting F(D).

Then

    K_B(F(D)) >= K_A.

**Proof.** Every target equivalence class that meets F(D) has preimages contained in **one** source equivalence class, by Theorem 14.2. Every source class has at least one representative, whose target image lies in some target class. Therefore there are at least as many target classes meeting F(D) as source classes. QED.

For fixed-length binary codes representing the target's relevant distinctions, at least

    ceil(log_2 K_A)

bits are required (ignoring metadata and decoder cost). This does not assert that the particular F is compressed or optimal.

## 5. What the theorem deliberately does not say

The reverse implication

    s ~=_A t implies F(s) ~=_B F(t)

**does not follow** from a one-way simulation. Target B may expose additional queries or events absent from A, and therefore distinguish source-equivalent states.

Thus there need not exist a well-defined function sending every source behavioral quotient class directly to one target behavioral quotient class. Claiming a canonical cross-context equivalence or an isomorphism would be incorrect without stronger two-sided conditions.

We also do not infer that either context's claims are true or that corresponding symbols refer to the same real-world entity.

## 6. Three counterexamples

### C1 — Unwitnessed semantic collision

Let S_A={0,1}, Q_A={identity bit query}, and S_B={*} a singleton with constant-zero query. An F mapping both source states to * cannot satisfy observation compatibility: the source observations differ. Therefore no strong witness exists for this query family.

A cultural translation that silently merges two distinct source concepts exhibits the same **formal failure mode** if there is a source query distinguishing them.

### C2 — A provenance substitution conflates citations

Map source identifiers a and b into the same target identifier z:

    h(a)=z, h(b)=z.

The semiring homomorphism is algebraically well defined. Yet it loses source identity: h(a)=h(b). If source queries include "was the cited source a rather than b?" and the target retains no other origin tag, observation compatibility fails. Consequently algebraic provenance coherence **alone** is not a strong simulation witness.

### C3 — A policy change not included in the event alphabet

Suppose current queries on a state are always Denied and a summary merges all states. Later a new authorized grant event reveals the original bytes, but this grant event was never declared in E_A. The earlier "sufficient summary" may now fail. Theorems 13.1 and 14.2 do not apply to undeclared events or queries.

## 7. Connection to traditional symbolic systems

The useful scientific question is **which explicitly declared formal relations** can survive a translation. For example:

- The mapping between a six-line Yin/Yang encoding and a six-bit vector can preserve line-flip composition when the encoding and line order are declared.
- A 60-step synchronized stem–branch cycle can be mapped to a modular-state representation preserving the step operator, with an explicit calendar convention.
- A numerical date reduction can preserve its specified arithmetic output while losing almost all other information about the original date.

None of these mappings is evidence of fortune-telling accuracy. A physical meaning, human trait or causal interpretation requires a separate evidential interface.

## 8. Generalization questions, not results

- What are the minimal additional conditions for **two-sided** behavioral equivalence under partial context translation?
- Can the witness domain be maximized without violating privacy or access rights?
- Can source identity and provenance multiplicity be protected while permitting useful semantic compression?
- What changes when updates are nondeterministic, probabilistic or concurrent?
- Which categorical formulation best captures observation-preserving **partial** maps with guarded disclosure?

The central open problem is to unite simulation witnesses with current policy, formal proofs, exact source lineage and reversible legal deletion, without merely restating known automata-theoretic or database theorems.

## Literature positioning

The proof pattern is standard simulation plus observational equivalence, closely related to data abstraction, automata and refinement theory. It has been re-stated here to provide a **correct baseline** and explicit counterexamples for a future HUMA manuscript.

No experiment, code execution, benchmark, test runner or GitHub Actions workflow is involved.
