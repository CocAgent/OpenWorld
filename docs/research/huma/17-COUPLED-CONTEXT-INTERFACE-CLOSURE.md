# 17 — HUMA-N1: Interface-Closed Composition of Dependent Memory Contexts

**Status:** Written-only theoretical construction and conditional theorem. No execution, benchmarking, machine-checking or claim of mathematical novelty.  
**Depends on:** Chapters 12–16 (especially the full-product baseline in Chapter 16).

## 1. The new obstacle: contexts may be coupled

Let I = {1,...,n} index finite, typed local contexts. Each has a finite raw state space S_i and a surjective *interface abstraction*

    alpha_i : S_i -> Z_i,

where Z_i contains only distinctions promised by a declared interface contract, not necessarily the complete local raw record. Define

    S = Product_i S_i, Z = Product_i Z_i,
    alpha(s) = (alpha_1(s_1),...,alpha_n(s_n)).

Unlike Chapter 16, the set G of admissible *global* states may be a proper subset of S. It can express cross-context coherence (e.g., a shared logical constraint), not empirical truth.

Set B := alpha(G), the *reachable interface codes*. The map alpha|_G:G->B is surjective by definition. One may impose **interface-saturated compatibility**,

    G = {s in S | alpha(s) in B},

as a sufficient local design requirement. Saturation is useful because admissibility then depends only on declared interfaces; it is *not necessary* for the theorem below.

Let E_G be a finite alphabet of admitted global updates. Each event e has a total deterministic transition U_e:G->G. Let Q_G be a finite set of total queries q:G->A_q with tagged results, including Denied and Unavailable as distinct outcomes where relevant. An abstract authorization check must exist separately if queries involve private sources.

## 2. Local, reviewable interface certificate

A candidate *interface-closure certificate* for each global query q consists of:

- A neighborhood N(q) subset I of contexts that query q is permitted to inspect.
- A declared total function q_hat: Product_{j in N(q)} Z_j -> A_q.
- A written obligation that, for every s in G,

    q(s) = q_hat((alpha_j(s_j))_{j in N(q)}).       [QC]

For each event e and each context i, the certificate contains:

- A neighborhood N(e,i) subset I of contexts on which the resulting *i-th interface* is allowed to depend.
- A declared total function v_(e,i): Product_{j in N(e,i)} Z_j -> Z_i.
- A written obligation that, for every s in G,

    alpha_i(U_e(s)_i)
      = v_(e,i)((alpha_j(s_j))_{j in N(e,i)}).      [EC]

These obligations are **assumptions** until checked. A source-level provenance annotation, data ownership label or similar name in two contexts does not by itself produce a valid QC or EC certificate.

The component functions v_(e,i) define a map V_e:Z->Z by collecting all coordinate outputs. The certificate additionally requires

    V_e(B) subset B.                                [CC]

CC follows if EC is true over all of G and B=alpha(G), but it is stated explicitly to prevent a specifier from accidentally creating an invalid abstract update on a proposed B.

## 3. Theorem 17.1 — Exact dynamic preservation under interface closure

**Statement.** Under the assumptions of Sections 1–2, alpha|_G is a *sound exact dynamic summary* for the declared updates and queries: there are total abstract transitions V_e:B->B and query decoders Q_hat:B->A_q satisfying

    alpha(U_e(s)) = V_e(alpha(s)),
    q(s) = Q_hat(alpha(s))

for every s in G, e in E_G and q in Q_G.

Consequently, for any finite event word w in E_G* and any q in Q_G,

    q(U_w(s)) = Q_hat(V_w(alpha(s))).

In particular, if alpha(s)=alpha(t) then s and t are dynamically observationally equivalent for E_G,Q_G. The number of dynamic equivalence classes is therefore at most |B|, and the abstract representation uses at most ceil(log_2 |B|) bits of fixed-length *state code*, not counting its transition/query tables or ancillary metadata.

**Proof.** Construct V_e coordinatewise from the declared v_(e,i), which is well defined on all of B by CC. EC applied at each coordinate gives alpha(U_e(s))=V_e(alpha(s)). QC similarly gives q(s)=Q_hat(alpha(s)), where Q_hat projects to the stated neighborhood and evaluates q_hat. Induct on event-word length: the empty word is immediate; if the relation holds after w, applying EC to U_w(s) and the corresponding V_e gives it after we. Apply QC to U_w(s) for the final observable equality. If alpha(s)=alpha(t), the equal abstract codes stay equal after each abstract word, so every declared future query agrees. Thus each alpha fiber is contained in one dynamic equivalence class; the dynamic quotient has at most as many classes as there are reachable alpha codes. The code-length statement follows from finite cardinality. QED.

**Important qualification:** An abstract code needs a finite alphabet of size at least |B|. A simple concatenation of individually coded interfaces instead uses at most sum_i ceil(log_2|Z_i|) bits. Efficient encoding/decoding of B is a separate question and may negate practical storage savings.

## 4. Theorem 17.2 — When the abstraction is *minimal*

Add a *separation* assumption:

    [SEP] for any distinct z,z' in B, there exist
          w in E_G* and q in Q_G such that
          Q_hat(V_w(z)) != Q_hat(V_w(z')).

Then dynamic equivalence on G is *exactly* equality of alpha codes:

    s ~=_(E_G,Q_G) t  iff  alpha(s)=alpha(t),

and the dynamic quotient has precisely |B| classes.

**Proof.** The forward implication from code equality to observational equivalence is Theorem 17.1. For the reverse, assume codes differ; SEP yields a future abstract query distinguishing them. Theorem 17.1 lifts the differing answers to the respective concrete states, hence the concrete states are not dynamically equivalent. Surjectivity of alpha|_G onto B gives the class count. QED.

This is a conditional result, **not** a claim that an arbitrary proposed interface is complete or minimal.

## 5. A *dependent* finite family with a strict representation reduction

Consider n >= 2 contexts connected by a path graph, indexed 1,...,n. Every local raw state consists of two bits:

    S_i = {(a_i,b_i) | a_i,b_i in {0,1}},
    alpha_i(a_i,b_i) = a_i XOR b_i = z_i.

Define the admissible coupled state space

    G = {s | z_1 XOR z_2 XOR ... XOR z_n = 0}.

Thus B is the even-parity subspace of {0,1}^n, containing 2^(n-1) codes. This G is interface-saturated.

Declared global queries are q_i(s)=z_i for all i. Declared events are e_(i,i+1), for 1 <= i < n, that toggle **a_i and a_(i+1)**, leaving all other raw bits unchanged.

Each event toggles exactly two interface bits z_i,z_(i+1), preserving their total parity, so it maps G to G. Every query and abstract update is a function of the interface codes alone: QC, EC and CC all hold.

Because q_i reports each z_i, any two distinct codes in B are immediately distinguished by some query, so SEP holds.

**Consequences (mathematical, not measured):**

- Raw state cardinality is |G| = 2^(2n-1): among 2n raw bits, one parity equation removes one degree of freedom.
- Exact dynamic observational quotient cardinality is |B| = 2^(n-1).
- A fixed-length abstract state code can use **n-1 bits**, versus **2n-1 bits** for a fixed-length code of arbitrary raw admissible states.
- The raw state and provenance of protected data must still exist if the permitted query family includes exact source restoration or attribution. The n-1-bit code answers only the declared parity queries and event updates.

An encoding of B can store z_1,...,z_(n-1) and reconstruct z_n as their XOR. The full raw state cannot generally be reconstructed from this code, which is consistent with Chapter 09.

This example is **a written finite construction**, not a simulation, runtime result or physical claim about Kinh Dịch.

## 6. Counterexamples: exactly where the conditions break

**Hidden input to an event (EC fails).** Add an event setting the parity of context j from the raw first bit a_i of another context. Two raw states can have identical z_i but different a_i. The same interface code then leads to different updated interface codes, so no well-defined V_e exists.

**Hidden query (QC fails).** Add q_raw(s)=a_i while keeping only z_i. Raw states (a_i,b_i)=(0,0) and (1,1) have the same parity but different q_raw responses; the summary is no longer exact for the expanded family.

**Context compatibility not described by the interface.** If G additionally requires a_i=0 for some i, its membership is not generally determined by z_i alone; an interface-saturation assumption would fail. Theorem 17.1 may still apply on that restricted G if QC/EC/CC hold and B is correctly defined, but a claim of local compatibility checking from z alone would not.

**Authorization not represented.** If query q_i is available for owner A but Denied for owner B, the observation family must carry principal/policy scope. Treating both as the same public query could leak data. Chapter 18 makes the scope explicit.

## 7. What this contributes and what it does not

The conditional theorems are instances of known quotient-congruence and transition-system simulation arguments. The coupled even-parity construction demonstrates **a mathematical possibility**, not a novel general compression algorithm.

HUMA-N1 is still open in its interesting form: obtain QC/EC/CC/SEP from **independently checkable local certificates** on a graph of partial, provenance-aware and authorized context transitions, with useful complexity guarantees, without first enumerating all G. Acyclicity alone does not guarantee closure; the certificate must account for every cross-context observable dependency.

No runtime source code, private datasets, test/benchmark, Lean or CI were used in this chapter.
