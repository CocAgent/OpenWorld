# 15 — Beyond Repackaging: The Originality Frontier for HUMA

**Status:** Critical research agenda with precise negative baselines and unproved candidate problems. **No novel HUMA theorem is asserted.** No experiments or proof assistant execution have taken place.

## 1. What we have established so far

The preceding mathematical chapters now define:

- typed trace constructors and a separate formal-proof judgment;
- a polynomial source-provenance semantics over N[X];
- partial, witnessed, observation-preserving context transformations;
- an exact-query lower bound for a *static* declared query family;
- a stronger **future-event observational equivalence** and a minimal exact state quotient;
- a non-collapse theorem for context translations that simulate events and preserve source queries;
- conditional replay and anti-rollback obligations, explicitly separate from source algebra.

The exact results in Chapters 08–14 are carefully scoped applications of prior art: semiring provenance, deterministic automata/behavioral equivalence, elementary information bounds and simulation/refinement. Calling their juxtaposition a "new super-mathematics" would be premature.

## 2. A no-go boundary: universal exact bounded memory

Consider a family of source state spaces S_n={0,1}^n for arbitrarily large n, where a future query can request any individual bit of the original n-bit source. Alternatively, allow an event sequence to reveal any bit in a later observation.

**Proposition 15.1 (no universal fixed-bit exact summary).** There is no fixed integer b such that every S_n admits a summary with at most b bits that answers all declared individual-bit queries exactly for every n.

**Proof.** The queries separate all 2^n states of S_n. The static equivalence classes (hence also the dynamic ones) are all singletons. Any exact fixed-length summary therefore requires at least log_2(2^n)=n bits. Choosing n>b contradicts the putative bound. QED.

This is an elementary information-theoretic consequence, **not a novel impossibility theorem**.

**Interpretation:** An information bottleneck can be task sufficient only relative to a restricted question and update contract. Exact arbitrary source recovery requires retained exact source information or an authorized external store. It cannot emerge from a constant-size learned vector with no additional data.

## 3. A stronger originality target

Instead of asking whether every knowledge system can be encoded in one syntax, ask:

> Can a context-indexed memory calculus admit a **compositional abstraction procedure** that is simultaneously exact for a declared family of authorized future observations, preserves typed source provenance under partial translations, respects revision and revocation, and avoids global state-space enumeration under nontrivial structural conditions?

This is a **research problem**, not a theorem we have solved.

A precise instance would supply:

1. A finite family of contexts indexed by a graph G.
2. For each context i, a finite state system S_i, events E_i, queries Q_i and source alphabet X_i.
3. Partial witnessed translations F_ij on the graph edges, with explicit domain, source substitution and observation conditions.
4. An exact global state space S_G consisting of tuples of local states satisfying declared compatibility constraints.
5. A global event alphabet E_G, including carefully scoped local updates, valid translations and policy events.
6. A declared set Q_G of **authorized** global observations, including any permitted source-attribution and version queries.
7. A representational cost model (bits, nodes, shared DAG size, update complexity) without assuming the same cost for different storage backends.

Only then can we define the global dynamic quotient

    S_G / ~=_(E_G,Q_G)

and ask whether it can be computed from local quotients and interfaces without constructing all of S_G.

## 4. Why naively combining local minimal memories can fail

Let S_A=S_B={0,1} and suppose locally each context has no distinguishing public query. Each local minimal behavioral quotient has one class.

Now introduce a global query that asks whether the two bits agree:

    q_global(a,b) = 1 iff a=b.

The pair states (0,0) and (0,1) are distinguished globally, even though each local public quotient collapsed its input.

Therefore **the product of the two local minimal summaries is not sufficient for a newly introduced cross-context query.**

To get a valid compositional construction, the local interface contract must expose all distinctions needed by global observations and future transfers. A vague promise that "knowledge graphs compose" is not enough.

## 5. Candidate research condition: interface completeness

For each context i, define a family I_i of **interface observations** representing all information about that context that cross-context queries or updates are permitted to inspect.

A proposed adequacy condition is:

    If s_i and t_i are equivalent under local (E_i, Q_i union I_i),
    then replacing s_i by t_i in any compatible global state
    cannot change the answer to any admitted global query
    after any admitted global event sequence.

Call this condition **substitution stability** for the interface specification.

The condition is strong. It may be hard to check, may require exploring global behavior, and could force I_i to reveal most of the local state. If so, the putative compression advantage vanishes. That negative outcome would itself be scientifically informative.

## 6. Conditional theorem target, not yet proved

**Problem HUMA-N1 (compositional observational quotient).**

Find structural assumptions A on the compatibility relations, event locality, translation witnesses, query interfaces and authorization changes such that

    global dynamic equivalence
       can be decided from bounded local/interface summaries,

and derive a rigorous storage/construction complexity upper bound that is **strictly better in a stated family of instances** than naive full product-state enumeration.

An acceptable result must include:

- the exact class of input systems;
- a constructive summary and its decoder/update operators;
- a complete preservation proof for every admitted global event and observation;
- counterexamples when each critical assumption is removed;
- a resource-bound argument in a precise complexity model;
- a prior-art comparison with compositional bisimulation minimization, assume-guarantee reasoning, automata products, coalgebraic methods and database-view maintenance.

There may be no generally useful positive theorem at this generality; a precise negative result or a restricted class could still be worthwhile.

## 7. Separate theorem target for provenance and access

**Problem HUMA-N2 (lineage-safe guarded translation).**

Consider a family of typed source transformations with partial domains and separate current authorization. Characterize when a translation can preserve both:

- the observable answers to all **authorized provenance queries** after permitted source withdrawal events; and
- the distinguished identity of source records required by those queries,

without retaining globally unique raw identifiers beyond their authorized lifespan.

This is not solved by a mere semiring homomorphism: a mapping a -> z, b -> z preserves some positive-support tests while losing the ability to distinguish original source identities. Nor can an immutable content hash alone satisfy lawful deletion and current access control.

A prospective solution could involve scoped identifiers, restricted observation families and erasure-aware interfaces. Its security assumptions and legal scope must be explicit. No deployment or correctness claim is made.

## 8. Interaction with information geometry and "hyperstrings"

The user's original longer-term inspirations—spectral memory, Fourier representations, string diagrams, higher-category models, sheaves and physical string theory—can be treated as **candidate modeling languages**, not predetermined solutions.

- **String diagrams/category theory:** potentially illuminate composition of typed partial witnesses once identities and laws are established.
- **Sheaf-like gluing:** could describe compatible local readings, but only after a precise site and restriction maps are defined.
- **Graph spectral methods/Fourier:** may give compact approximate features, but the representation, loss and resource advantage need future evidence.
- **Physical superstrings:** no scientific mapping from these symbolic memories to physical strings has been proposed or validated.

The immediate paper should emphasize verified preservation conditions and impossibility boundaries rather than an ungrounded universal physics claim.

## 9. Research review decision table

| Candidate contribution | Current classification | Necessary next work |
| --- | --- | --- |
| N[X] source annotation | Established prior art | Correct citation and precise typing |
| Dynamic minimal-memory quotient | Established automata-style argument | Identify query/update obligations |
| Witnessed non-collapse | Established simulation/refinement proof pattern | Review side conditions |
| HUMA-N1 compositional quotient with provable structural efficiency | Open research problem | Precise assumptions, constructive algorithm, proofs, counterexamples |
| HUMA-N2 scoped provenance under revocation and erasure | Open research problem | Formal authorization and retention semantics |
| Use of HUMA to predict human destiny | Unsupported empirical claim | Not part of this research program |
| Deployment in OpenWorld agent runtime | Not authorized by theoretical work | Separate owner, privacy, licensing, review and evaluation gates |

## 10. Immediate writing-only next steps

A focused manuscript can be organized as:

1. Definitions: typed contexts, source alphabets, query and event signatures.
2. Calculus: trace construction and guarded translations.
3. Known baseline theorems: dynamic quotient and non-collapse.
4. New challenge: sufficient interface completeness for compositional quotient.
5. Countermodels and limits on arbitrary exact compression.
6. Prior-art analysis and narrower candidate conjecture.

**Scientific integrity gate:** Do not claim a new theorem until the proof has been written, checked against prior art and criticized independently. Running benchmarks would require a separate authorization to lift the existing freeze. This document adds neither experimental work nor hosted CI use.
