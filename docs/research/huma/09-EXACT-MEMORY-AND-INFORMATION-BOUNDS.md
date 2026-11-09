# 09 — Exact Memory, Query Sufficiency and Information Bounds

**Status:** Theory-only manuscript. Established elementary lower bounds are proved within the stated finite model. There are no performance measurements.

## 1. Three different guarantees

A memory system must not blur:

1. **Exact source reconstruction:** recover the original retained bytes on demand.
2. **Exact query sufficiency:** answer all queries in a *declared* family Q, though the original bytes may no longer be recoverable from the summary alone.
3. **Lossy task utility:** produce approximately useful answers for a particular task distribution and loss.

The first implies the second for queries computable from the original content, *if retrieval is authorized*. The second does not generally imply the first. The third implies neither.

Any practical memory storage cost must count payload, identifiers, provenance, indices, log records, snapshots and metadata, not merely a small embedding or compressed prediction vector.

## 2. Exactness impossibility on arbitrary bytes

Fix n >= 1. Let X_n = {0,1}^n be all n-bit strings.

**Proposition 9.1 (no uniform strict compression).** There is no lossless encoder E mapping *every* n-bit input to a binary string of length strictly less than n with a decoder D satisfying D(E(x))=x for every x in X_n.

**Proof.** Exact restoration forces E to be injective: E(x)=E(y) implies x=D(E(x))=D(E(y))=y. But the collection of all shorter binary strings has cardinality

    sum_{k=0}^{n-1} 2^k = 2^n - 1,

which is smaller than |X_n|=2^n. By the pigeonhole principle, no injection exists. QED.

The result concerns all arbitrary n-bit inputs. It does not deny that structured documents, finite grammars, repeated data, source-sharing or compressible input distributions can be encoded more economically.

**Corollary (fixed-size lower bound).** An exact fixed-length binary code for all X_n needs at least n bits per source input.

## 3. Query sufficiency as an equivalence relation

Let X be a **finite** set of possible retained source states and Q a family of deterministic queries, each q:X->A_q.

Define x ~_Q y if and only if

    q(x) = q(y)  for every q in Q.

This is an equivalence relation. Let X/~_Q denote its equivalence classes.

A summary S:X->Z is called **Q-exact** if for every q in Q there exists an answer decoder a_q:Z->A_q satisfying

    a_q(S(x)) = q(x)  for all x in X.

### Proposition 9.2 (minimal exact summary cardinality)

Any Q-exact summary S has at least |X/~_Q| distinct reachable outputs. Conversely, the quotient mapping

    S_Q(x) = [x]_Q

is Q-exact and has exactly |X/~_Q| reachable outputs.

**Proof.** Suppose S(x)=S(y). For every q, q(x)=a_q(S(x))=a_q(S(y))=q(y); hence x~_Q y. Thus distinct equivalence classes cannot be mapped to the same summary value, and the number of reachable summary states is at least the number of equivalence classes. Conversely, define a_q([x])=q(x). It is well defined because all members of an equivalence class agree on every q. The quotient mapping with these decoders answers all queries exactly. QED.

### Corollary 9.3 (fixed-length memory bound)

If K = |X/~_Q|, any *fixed-length* binary encoding of a Q-exact summary requires at least

    ceil(log_2 K)

bits. This counts representational states only and excludes metadata, indexing and the specification of Q or the decoder.

### Consequence: no universally constant exact memory

If Q separates every pair of distinct source states, then |X/~_Q|=|X|. One must retain a distinct code for every possible input. In particular, if Q contains a query that recovers the entire original source, the quotient has one class per source state.

This directly explains why an agent's small statistical sketch can be useful for some predictions without constituting a universal exact-history substitute.

## 4. Worked example: six-line hexagram encoding

Let X = {0,1}^6.

**Query family Q_full:** all six coordinate queries q_i(x)=x_i. Every two distinct states differ in some coordinate, so K=64 and an exact fixed-length encoding needs at least six bits.

**Query family Q_parity:** the one query q(x)=x_1 XOR ... XOR x_6. Exactly two equivalence classes exist (even and odd parity), so one bit is enough for that single query.

Both statements are elementary. Neither says that a hexagram has measurable predictive influence on external events. The interpretation of the bits is a separate, attributed layer.

## 5. Source-level exactness vs query-level minimality

For a claim memory, the query family might include:

- restore the precise original text, citations and wording;
- find an attributed interpretation;
- ask which claim depends on source x;
- find any still-active derivation trace;
- report a version current as of a recorded time;
- retrieve a formal proof term under a named logic.

These queries typically require **different distinctions** among input states. If exact textual restoration is in Q, no lossy semantic sketch alone is Q-exact. A proposed compiler must declare Q per storage lane and preserve a path to exact retained records where authorized.

An embedding may be a search index. It should not claim to be a faithful reversible encoder for unconstrained source text.

## 6. Probabilistic information inequality

Let X,Y be jointly distributed discrete random variables and let Z=f(X) be a deterministic summary. Then the Markov relation Y--X--Z holds and the data-processing inequality gives

    I(Z;Y) <= I(X;Y).

By the mutual-information chain rule and deterministic Z=f(X),

    I(X;Y) - I(Z;Y) = I(X;Y | Z) >= 0.

Therefore equality occurs exactly when I(X;Y|Z)=0, i.e. Z is statistically sufficient for Y relative to X in this particular sense.

This theorem does not say that Y is predictable from X, nor that a deterministic birth-date reduction is useful for predicting a person's fate. A simpler representation can still improve finite-sample estimation under algorithmic constraints without creating new intrinsic mutual information.

**Important scope condition:** This is stated for a *fixed joint distribution* of X,Y and the summary f. It is not a claim of cross-population generalization or stable causal relationships.

## 7. Lossy compression: a bounded research objective, not a theorem of performance

For a specified query distribution mu over Q and an answer loss ell_q, define

    D_mu(S) =
        E_{x~P_X, q~mu}[ell_q(q(x), a_q(S(x)))].

A candidate design may seek

    minimize_S  Cost(S) + lambda * D_mu(S).

Cost(S) must state whether it means code bits, process peak RAM, index bytes, disk including WAL, compute time, latency, or a multi-objective budget. Different cost models can select different summaries.

No claim is made that this proposed optimization is globally solvable, unique, or superior to simple baselines. A rate–distortion or information-bottleneck formalism can sometimes yield principled bounds, but only after the distribution, alphabet, admissible encoders and distortion measure are specified.

## 8. Memory impossibility counterexamples

**A. Full history from one parity bit.** If S(x)=parity(x) on six-bit inputs, choose x and y with the same parity but different coordinates. S(x)=S(y), so no decoder can recover both raw states correctly.

**B. A compact summary that forgets attribution.** A summary "two texts agree" does not answer which author, version, page or translation each text came from if those fields were discarded.

**C. A wrong claim about repeated evidence.** Compressing ten citations from one original source into "ten independent confirmations" changes the proposition and provenance rather than merely compressing them.

**D. Authorization absent from the encoding.** Even an information-theoretically lossless store must reject unauthorized reads. Correct encoding is not access control.

## 9. Research value and boundaries

Propositions 9.1 and 9.2 are established counting and partition arguments applied to memory; they are **not novel HUMA discoveries**. A future contribution may involve finding an interesting family Q linked to typed provenance and revision whose equivalence classes admit useful and efficiently maintained encodings, together with proofs and independent comparisons. That stronger objective remains open.

The current GitHub Actions freeze prohibits benchmarking or empirical tuning. This chapter contains no runtime-cost claim.

## References

- C. E. Shannon, [A Mathematical Theory of Communication](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf), 1948.
- T. Cover and J. Thomas, *Elements of Information Theory* (2nd ed.), chapters on data processing and rate–distortion.
- N. Tishby, F. Pereira and W. Bialek, *The Information Bottleneck Method* (1999), for task-relevant information compression.
- OpenWorld [HyperMemory constraints](../../ARCHITECTURE.md) and [review policy](../../GOVERNANCE-REVIEW-POLICY.md).
