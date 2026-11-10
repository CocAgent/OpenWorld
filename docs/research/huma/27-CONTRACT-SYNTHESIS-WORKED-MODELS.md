# 27 — Worked Finite Models of Local Memory-Contract Synthesis

**Status:** Hand-worked symbolic examples only; not simulations, software tests, validation of actual access control, or empirical predictions. Based on the refinement theorem in Chapter 26.

## 1. A two-agent memory exchange

Suppose Agent A has a two-bit local raw state

    S_A = {(x,y) : x,y in {0,1}}

and Agent B stores a one-bit publicly declared answer

    S_B = {0,1}, state b.

The only declared query reads B:

    q_B(x,y,b)=b.

The only declared cross-agent event CopyX sends A's first bit into B:

    CopyX(x,y,b) = (x,y,x).

Its read neighborhood may be declared N_CopyX={A,B} and write neighborhood T_CopyX={B}, although B's old bit is ignored. Its event function is total, deterministic and synthetic.

### Applying the refinement rule on paper

Start with universal equivalence on S_A and S_B.

**First refinement:** The immediate query q_B distinguishes b=0 from b=1. Therefore R_B becomes equality on the two values, while R_A can remain indiscrete at the first round: the CopyX target was compared against the old universal R_B when E_A(R^0) was calculated.

**Second refinement:** Since R_B now distinguishes values, CopyX requires that A-states with different x values cannot be equivalent. The new R_A partitions A's four states by x:

    class x=0: {(0,0),(0,1)}
    class x=1: {(1,0),(1,1)}.

The second raw bit y is not needed for q_B or CopyX. Both event closure and query exactness hold on this pair of partitions, so the refinement stabilizes.

**Exact interface codes:**

    alpha_A(x,y)=x
    alpha_B(b)=b.

Only two distinct A interface codes are necessary, even though A has four raw states. The public interface is not a reversible archive for A's complete two-bit record.

### Why the x-distinction is necessary

If A-states with different x were merged, the abstract CopyX event would need to write both 0 and 1 into B from the same source interface code. No deterministic abstract transition could satisfy the exact event-compatibility equation. This is a minimal counterexample to indiscriminate memory merging.

## 2. A harmless local update versus an important new update

Introduce an additional local A event FlipY:

    FlipY(x,y,b)=(x,1-y,b).

Because alpha_A depends only on x, FlipY leaves the interface unchanged. The coarsest locally admissible quotient remains the same.

Now introduce SwapA:

    SwapA(x,y,b)=(y,x,b),

which exchanges A's two raw bits.

The old abstraction alpha_A(x,y)=x is no longer exact for this expanded contract. Consider

    s=(x=0,y=0,b=0)
    t=(x=0,y=1,b=0).

They have the same old interface code. But after the same sequence SwapA, CopyX, q_B, the observed B result is 0 from s and 1 from t. Thus these states are distinguishable by an admitted future event word.

Chapter 26's refinement must therefore split the x=0 block according to y. The same argument applies to the x=1 block. The new coarsest admissible A partition is equality on all four raw states.

**Lesson:** The minimal exact memory representation depends on the future-update language, not just the current questions.

## 3. A multi-agent fan-in example

Introduce Agents A1 and A2, each citing one opaque, context-tagged source identifier:

    source(A1)=a, source(A2)=b, where a != b.

The receiver's exact attribution query distinguishes:

    "Was source a cited?" and "Was source b cited?"

If both senders rename their separate identifiers to a single receiver alias z, each singleton rename is individually injective, but the merged rename is not.

The receiver can no longer answer the two exact attribution queries from z alone. Chapter 24's fan-in criterion requires injectivity on the distinctions covered by those queries (or an independent authorized exact reference).

A narrower query, such as "Does some recorded source path exist?", may allow a less informative summary. That is a **different contract**, not a proof that exact attribution is preserved by z.

The existence of a citation does not imply the truth of the cited claim, so nothing here upgrades a Trace to a verified proof.

## 4. Principal-specific views and a later grant

Let Agent A hold a raw protected bit h and let Policy P store access flag g in {Denied,Granted}. Define

    Read(h,Denied)=Denied
    Read(h,Granted)=Value(h).

Suppose Grant changes P's flag to Granted after an independently valid authority decision.

**Insufficient candidate:** alpha_A(h)=* (forgets h), alpha_P(g)=g.

This fails the query exactness obligation for granted states: (h=0,g=Granted) and (h=1,g=Granted) have identical interface codes but different Value responses.

Even if only denied states exist initially, a future admitted Grant event can distinguish their hidden payloads. A small public agent cache may omit h, but then the **combined system** must include a protected, authorized exact-data lane for later reads if that behavior is in scope. The cost of that lane cannot be counted as zero.

The mathematics does **not** grant an agent permission to execute Grant or read a source. It only models outcomes after a specified authorized event.

## 5. Coupled compatibility restricts minimality claims

Suppose two agents each have one bit, a,b in {0,1}, with a global admissibility constraint

    G = {(0,0),(1,1)}.

Queries are q(a,b)=a XOR b, which is always zero on G, and there are no updates.

On the actual admissible states, a **single constant code** suffices for q. However, Chapter 26's algorithm checks all assignments in the full product, including the forbidden pairs (0,1) and (1,0). Under unrestricted product semantics, q distinguishes bits of both agents, so the resulting local relations are equality.

Thus the full-product synthesis result can be conservative for a coupled admissible subspace. One must not call its product quotient globally minimal on G unless additional reachability/compatibility theory is supplied.

This is why HUMA-N1 still has a nontrivial open problem for **dependent** agents.

## 6. A simple symbolic provenance availability example

A claim has provenance

    P(K)=a*b+c.

Source availability is an independent predicate, not a user read grant.

- Available {a,b,c} yields two algebraic derivation paths.
- With a withdrawn but c available, the c path survives.
- With a withdrawn and c unavailable, no complete path survives.

These statements concern recorded paths. They do not determine whether K is a mathematical theorem, a factual observation or a culturally attributed interpretation.

If a receiving agent merges a and c under the same alias, independent withdrawal may no longer be representable. This is a source-identity contract failure, not an ordinary compression success.

## 7. Counterexample register

| Candidate shortcut | Why it is invalid |
| --- | --- |
| Keep only currently visible B outputs | CopyX requires A's hidden x for a future write |
| Keep only A's current x forever | SwapA makes y observable after future events |
| One unique alias per sending agent is sufficient | Aliases can collide at receiver fan-in |
| Current Denied permits permanent loss of protected content | An authorized future Grant may require exact payload recovery |
| Full-product local quotient is globally minimal on a restricted coupled state space | Some Cartesian assignments used in refinement may never be admissible |
| Surviving provenance proves a claim | A valid path can use unreliable or misinterpreted citations |

## 8. How to interpret the examples

These are **worked mathematical models**, not evidence about particular deployed agents, personal histories, astrological traditions, human behavior or the performance of any compression algorithm.

They support a narrow statement: under explicitly declared finite, deterministic, total, local events and queries, a local interface can be synthesized using a finite partition-refinement procedure. The result is exact *for that contract*, and can change when queries, events, privacy policies or source-identity requirements change.

No code, benchmark, test, Python, Lean, GitHub Actions, raw data or simulation was executed.
