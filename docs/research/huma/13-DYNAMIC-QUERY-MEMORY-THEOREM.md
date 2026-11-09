# 13 — Minimal Memory for Queries Under Future Revisions

**Status:** Written finite-state theorem with proof and counterexamples. This is a specialization of established behavioral equivalence and automata minimization (Myhill–Nerode style), **not an original HUMA theorem**.

## 1. Why the current-query quotient is not enough

Chapter 09 defines exact summaries for a fixed family of queries at one point in time. A persistent memory system also responds to updates. Two records may have identical answers *today* but lead to distinguishable answers after some future event.

An agent memory compiler must therefore specify what future transformations a summary claims to support. Without this commitment, "minimal memory" is underspecified.

## 2. Finite deterministic setting

Fix one context c. Let:

- S be a nonempty **finite** set of abstract memory states;
- E be a finite alphabet of event requests, where each event e has a total deterministic transition U_e:S -> S;
- Q be a finite family of total observation functions q:S -> A_q, with Value/Denied/Unavailable already distinguished in their codomains.

The definition can be extended beyond finite sets at the cost of losing a finite cardinality bound. We use the finite setting to make a precise storage theorem.

For a word w=e1 e2 ... ek in E*, define U_empty=id_S and U_(we)(s)=U_e(U_w(s)). Thus events are applied from left to right.

Define the **dynamic observational equivalence**:

    s ~=_(E,Q) t
       iff  for all w in E* and q in Q:
                 q(U_w(s)) = q(U_w(t)).

The empty word is included, so dynamically equivalent states also answer every present query identically.

This relation depends on the selected event alphabet and selected query family. Expanding either may split equivalence classes and increase required memory.

## 3. Theorem 13.1 — Quotient stability and minimality

**Statement.** Under the assumptions of Section 2:

1. The relation ~=_(E,Q) is an equivalence relation.
2. It is stable under each event:
   
       s ~= t  implies  U_e(s) ~= U_e(t) for all e in E.
   
3. Consequently, Q and E induce well-defined query and transition functions on the quotient S/~=:

       q_bar([s]) = q(s)
       U_bar_e([s]) = [U_e(s)].

4. For *any* summary representation F:S -> Z equipped with deterministic summary transitions V_e:Z -> Z and query decoders a_q:Z -> A_q satisfying

       F(U_e(s)) = V_e(F(s))
       q(s) = a_q(F(s))

   for every state s, event e and query q, the number of reachable summary codes obeys

       |F(S)| >= |S/~=_(E,Q)|.

5. Conversely, the quotient encoding F_min(s)=[s] satisfies both equations and achieves equality.

If K=|S/~=_(E,Q)|, a fixed-length binary code for the reachable summary states therefore needs at least

       ceil(log_2 K)

bits in the worst case, excluding encoding tables, decoders, metadata and implementation overhead.

### Proof

**(1)** Equality of each future observable answer is reflexive, symmetric and transitive. Universal quantification over w and q preserves these three properties.

**(2)** Suppose s~=t. Fix an event e, any word w and any query q. The composition definition gives

       q(U_w(U_e(s))) = q(U_(ew)(s))
                       = q(U_(ew)(t))
                       = q(U_w(U_e(t))).

Thus U_e(s)~=U_e(t).

**(3)** For q_bar, use the empty word in the equivalence definition: if s~=t then q(s)=q(t). For U_bar_e, apply (2). Hence neither formula depends on the representative of the class.

**(4)** Suppose F(s)=F(t). By induction on word length and transition compatibility,

       F(U_w(s)) = V_w(F(s)) = V_w(F(t)) = F(U_w(t)).

Applying query decoder a_q gives q(U_w(s))=q(U_w(t)) for every w,q. Therefore s~=t.

The contrapositive says distinct behavioral equivalence classes **must** map to different summary codes. This proves the cardinality bound.

**(5)** Assign F_min(s)=[s], V_e=U_bar_e, and a_q=q_bar. Part (3) shows these functions are well defined and satisfy the required equations. Exactly K quotient classes are reachable. QED.

## 4. Why the theorem is stronger than a current snapshot bound

The theorem's lower bound depends on **all permitted future words of events**, including policy-changing events *if* they are included in E, rather than on only present outputs. It gives a correct abstract criterion for deciding which distinctions can be forgotten safely under a declared future-operation contract.

It does **not** solve the computational problem of finding the quotient for a huge or infinite state space. Standard finite-state partition refinement is related prior art; no efficiency gain is asserted here.

## 5. Counterexample — same current answer, different future

Take S={00,01,10,11} and a single current query

    parity(b1,b2) = b1 XOR b2.

At present, 00 and 11 are equivalent because both have parity zero.

Now allow events reset_first and reset_second, which set the respective bit to zero. After reset_first:

    00 -> 00 -> parity 0
    11 -> 01 -> parity 1.

So 00 and 11 are **not** dynamically equivalent. In fact, the two reset events permit distinguishing all four states, so K=4 and two bits are needed. The present-query quotient has only K=2 (one bit).

This example refutes any general claim that a currently sufficient summary is automatically sufficient for all future mutations.

## 6. Hexagram examples without divination

Let S={0,1}^6 and E consist of six line flips U_i(q)=q XOR e_i. All 64 binary hexagram states are reachable from any other by flip words.

**Case A: Query only the parity of all six lines.**

Each flip toggles parity, irrespective of which line flips. States of equal parity remain observationally equivalent after every sequence. Therefore there are precisely **two** equivalence classes; one bit is a sufficient summary for the declared parity-only task and all line flips.

**Case B: Query only whether the configuration is all zero.**

Define q0(x)=1 when x=000000 and 0 otherwise. For any distinct x,y, choose the word of flips corresponding to all 1 bits of x. It maps x to zero and maps y to x XOR y, which is nonzero. Hence q0 distinguishes the two states after that word. There are **64** classes; no two distinct states can be compressed to the same exact dynamic-memory code. A fixed-length code requires at least six bits.

Thus even with the *same* state space and event transformations, changing the query family changes the exact minimum memory requirement.

These are formal examples of binary strings. They have no predictive meaning for real-world fate.

## 7. Security and privacy interpretation

A query result may be Denied or Unavailable. Such outcomes are part of q's *declared observable result*, not permission to reveal secret content.

If a future grant event allows access to data previously hidden, then the dynamic quotient may need to retain distinctions that are currently invisible. This is a representational lower bound, not an authorization policy: the store must still enforce current rights independently.

If lawful erasure is required, the future query family must reflect that the erased data are unavailable. HUMA cannot guarantee both permanent exact recovery of erased personal information and authentic deletion.

## 8. Conditions that would invalidate an application

- An undeclared external data feed changes state: it is outside E.
- An update uses nondeterministic randomness not included in state/event: U_e is not a deterministic function under this model.
- New unregistered queries arrive after the summary is fixed: the theorem gives no guarantee for them.
- A snapshot omits security-relevant policy state but an observer assumes it: the model is incomplete.
- Summaries contain side channels or authorize reads on their own: the theorem is not an access-control analysis.

## 9. Research implications

The theorem provides a **formal baseline** for a future HUMA memory compiler:

1. Declare which observations must remain exact.
2. Declare which updates the memory must support.
3. Determine the behavioral distinctions that cannot be forgotten.
4. Allow lossy projection only for a smaller, explicitly accepted task family.
5. Keep exact protected evidence in a separate authorized storage lane.

The true novelty challenge is to combine this known dynamic-state quotient with *typed provenance, partial cross-context translations, revision-time authority and bounded storage* in a way that yields a nontrivial, not already-known result. No such novelty is claimed here.

## Prior art

- Myhill–Nerode equivalence and minimization of deterministic automata.
- Behavioral equivalence and bisimulation in transition systems.
- Chapter 09 of this folder for current-query exact summary quotients.
- Classical finite information and state-encoding lower bounds.

**No Python, Lean, simulation, GitHub Actions, benchmark or holdout is used or authorized.**
