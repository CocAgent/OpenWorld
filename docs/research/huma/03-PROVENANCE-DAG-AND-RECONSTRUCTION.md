# 03 — Provenance Semirings, Shared DAGs and Reconstruction

**Status:** Mathematical account based on established ideas; no benchmark or performance assertion.

## 1. Source polynomials

Take a set of symbolic source names X. The free commutative semiring N[X] is the set of finite polynomials with coefficients in the non-negative integers. Its constants 0 and 1, sum + and product · obey the semiring axioms.

For source symbols a, b, c, the expression

    P = a·b + c

represents two *recorded derivation paths*: one needs both a and b; another needs c alone. P does **not** represent the probability that a conclusion is true. A second copy of a source does not create an independent witness; in N[X], a+a = 2a.

When comparing independently sourced evidence, actual dependency structure and validity must be checked by a separate evidential process.

## 2. Availability valuation and its limitation

For a set A subset X of currently available identifiers, define the unique semiring evaluation

    ev_A : N[X] -> N
    ev_A(x) = 1 if x in A; otherwise 0.

Then ev_A(P)>0 means **some recorded path uses only available source identifiers**. It does not guarantee any source is genuine or any inference rule is sound.

For P = ab+c:

| Available sources | ev_A(P) | Recorded derivation survives? |
| --- | ---: | --- |
| none | 0 | no |
| {a} | 0 | no |
| {a,b} | 1 | yes |
| {c} | 1 | yes |
| {a,b,c} | 2 | yes (two algebraic paths) |

"Two" means two algebraic paths, not two independent pieces of empirical evidence.

## 3. A shared provenance DAG

A symbolic circuit node is one of

    Zero | One | Source(x) | Sum(n_1,...,n_k) | Product(n_1,...,n_k).

Nodes refer only to previously defined nodes (an acyclic topological order). Equivalent subexpressions can share physical nodes (hash-consing).

Define the interpretation bracket function over N[X]:

    [[Zero]]=0, [[One]]=1, [[Source(x)]]=x,
    [[Sum(children)]]=sum_i [[child_i]],
    [[Product(children)]]=product_i [[child_i]].

The **representation** is a DAG; its **semantics** is a polynomial. DAG identity is not polynomial equivalence, since distributivity can produce equivalent expressions with different structure.

### Established lemma A — Structural evaluation

For every well-formed finite DAG D with root r and source valuation v:X->N,

    eval_D(r,v) = eval_N[X]([[r]],v).

*Proof sketch:* Induct on the topological order of nodes. Constants and source nodes are immediate; Sum and Product follow the respective induction hypotheses and semiring operations. This is standard expression-circuit semantics, **not a novel HUMA theorem**.

### Established lemma B — Boolean support

For a valuation v_A:X->{0,1}, all intermediate values are non-negative. Therefore

    eval_D(r,v_A)>0
       iff BooleanSupport_D(r,A) is true,

where Sum maps to OR and Product to AND, with Zero=false and One=true.

*Proof sketch:* For nonnegative integers, a sum is positive iff some summand is positive; a product is positive iff every factor is positive. Prove by structural induction. This guarantees a presence-of-path decision, not truth.

## 4. Why a DAG matters

The factorized expression

    P_n = Product_{i=1..n}(x_i + y_i)

can be stored with O(n) symbolic nodes and edges when fan-in and symbol indexing are bounded appropriately; expanding it yields 2^n distinct monomials. This is an algebraic **size separation**, not a measured runtime improvement of any implementation.

Worst-case circuit size, traversal, normalization, polynomial equivalence and arbitrary exact arithmetic all require explicit resource bounds. Evaluation can still produce an exponentially large integer (in bit-length relative to encoded input if exponents are compressed), so state the arithmetic cost model.

A proposed bounded interface must fail explicitly on node-count, fan-in, depth, expansion-term and evaluated-count limits. Silent truncation must not be called exact evaluation.

## 5. Revision and withdrawal

If a source is revoked, do not erase all algebraic references to it as though it never appeared. Instead distinguish:

- **Historical lineage:** the original record of how a claim was constructed, governed by retention and deletion constraints.
- **Current admissibility:** whether a recorded path is authorized and available today.
- **Validity:** whether the inference connecting a source to its conclusion is sound.

Dropping a from the available set makes the ab route unavailable, while the c route can remain. It does not prove c authentic, and does not itself implement secure access revocation.

## 6. Exact storage vs approximate recall

Let E be a lossless serializer on the declared input set and D its inverse-on-image:

    for all x in Domain(E): D(E(x)) = x.

This can preserve bytes, ASTs or a canonical symbolic graph. By contrast, a semantic compressor C_Q may minimize a task-dependent distortion

    min_C  L(C(M)) + lambda · Distortion_Q(M, Decode(C(M))).

This is a **research objective**, not an established universal memory-compression theorem. If exact source evidence is required, the approximate form is an additional index, not the original record.

Use distinct layers for content-addressed objects, versioned manifests, source attribution and fast approximate retrieval.

## 7. Persistent storage and historical time

A candidate store separates:

- immutable-or-versioned symbolic definition records,
- payload bytes subject to retention and deletion,
- source identifiers and provenance edges,
- valid time (when a claim purports to apply),
- transaction time (when a system recorded it),
- a sequence of revisions and active authorizations.

A content hash provides integrity *relative to an expected digest*; it is not an authentic signature or evidence of a real-world event.

A versioned database may maintain append-only references while permitting lawful erasure of personal payloads. Operational correctness also needs atomicity, migrations, backups, principal isolation and audit; none is proved by the present algebra.

## 8. Proposed future contracts (not implemented here)

1. A canonical typed serialization grammar with an explicit version.
2. A checked context-boundary translation before combining derivations.
3. A proof checker that distinguishes derivation validity from source presence.
4. A resource-bounded evaluator with an explicitly stated integer arithmetic model.
5. A deletion/retention model that does not silently reconstitute revoked data from snapshots.
6. A reproducible comparison against simpler relational-provenance approaches, **only after the experimental freeze is separately lifted**.

## 9. Theory provenance

The semiring model and factorized provenance circuit ideas are known prior art. The future HUMA contribution must be specified beyond them (e.g., a type-correct joint theory of context translation, revision and evidence separation, with real new results).
