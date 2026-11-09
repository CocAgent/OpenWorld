# 04 — Finite Symbolic Case Studies Without Predictive Claims

**Status:** Pure mathematical examples and research interpretation; not empirical validation of divination.

## 1. I Ching hexagrams as a six-bit state space

Let F_2 = {0,1} with addition modulo 2. Define

    Q = F_2^6.

A hexagram is a six-coordinate vector q. Its size is |Q|=2^6=64. Let e_i be the i-th basis vector, with i=1 representing the bottom line. The elementary line flip is

    T_i(q) = q + e_i in F_2^6.

### Established propositions

1. **Involution:** T_i(T_i(q))=q since e_i+e_i=0.
2. **Commutation:** T_i∘T_j = T_j∘T_i by commutative vector addition.
3. **Reachability:** The maps T_1,...,T_6 generate a transitive action of (Z/2Z)^6 on Q.
4. **Graph structure:** Connecting states differing in exactly one bit yields the six-dimensional hypercube, with 64 vertices, each degree 6, and (64·6)/2=192 undirected edges.
5. **Hamming distance:** d(q,r) = number of coordinates on which q,r differ, giving the shortest path length in that graph.
6. **Spectrum, for the unnormalized graph Laplacian:** eigenvalues 2k, k=0,...,6, with multiplicity binomial(6,k), by the standard character basis of the hypercube.

These are ordinary finite algebra/graph results. They may support a software test fixture. None is evidence that a hexagram predicts any event.

## 2. Ten heavenly stems and twelve earthly branches

A simplified mathematical clock is a simultaneous step on Z_10 × Z_12:

    S(a,b) = (a+1 mod 10, b+1 mod 12).

The return period of S is

    lcm(10,12)=60.

The orbit starting at an admissible synchronized pair has 60 states; the full Cartesian product has 120 pairs. In a traditional 60-pair synchronized cycle, the parity of the two coordinates is correlated: only one of the two parity classes appears in the chosen cycle.

This is a modular-arithmetic statement about a particular encoding of a cycle. It is not a demonstration that the cycle causes personality, health or economic outcomes. Translating between actual civil dates and historical calendar systems needs explicit conventions for timezone, epoch, leap month and regional calendar rules; these are not all contained in this simplified clock.

## 3. Numerology as a deterministic information-reduction map

Let X be a raw birth-date representation with a documented calendar normalization, and let

    Z = f(X)

be a deterministic digit-reduction rule. If Y is any observable outcome, and all random variables are defined on the same probability space, then the data-processing inequality implies

    I(Z;Y) ≤ I(X;Y).

The inequality is established information theory. It says that a deterministic numerical transform cannot increase the mutual information contained in the original representation about the target. It **does not** assert that birth dates contain useful information about a target; that is a separate empirical question.

If the transformation depends on a written digit system, changing date notation or base may change the result. A serious theory must specify which changes are merely representation changes and which alter the input definition. "Numerological invariance" would require a precise symmetry group and a declared invariant, not an anecdote.

## 4. Physiognomy: representation is not legitimacy

A textual claim of the form "tradition T associates feature F with trait R" can be represented as a historically attributed proposition with a provenance edge to a source text. The system should not promote this into an automated prediction that an actual person with F possesses R.

Human appearance data raises privacy, bias, discrimination, and consent risks. The program does **not** propose classification of real people by facial traits, race, health, employment suitability, moral character or alleged destiny.

## 5. Esotericism, philosophy and string diagrams

Concepts in Xuanxue and other philosophical/esoteric traditions can be indexed by specific authors, translations and schools. Relations such as "interpreted as", "contrasts with" and "historically associated with" must be distinguished from logical equivalence.

In a category-theoretic string diagram, wires and boxes represent composable mathematical morphisms. They do not physically identify information records with vibrating superstrings. Any physical interpretation would require a separate falsifiable physical model.

## 6. Shared-memory example with explicit epistemic types

Consider four records:

- R1: "A six-line binary state has 64 possibilities" — a combinatorial assertion under a defined encoding, potentially with formal proof.
- R2: "An old commentary interprets hexagram H as symbolizing quality Q" — an attributed cultural-textual statement.
- R3: "Birth-number N predicts outcome Y" — an empirical hypothesis requiring outside evidence.
- R4: "A machine-generated summary of R2" — an inferred, derived record with access back to R2.

A memory compiler may link R1 and R2 by their common symbol without rewriting R2 as a theorem or R3 as a verified fact. If R2 is translated, the translation metadata must preserve attribution and known semantic differences. If R4 is lossy, it must not replace the exact record R2 where exact quotations are required.

## 7. What we are deliberately not doing

- No horoscope generation for a real person.
- No evaluation of destiny predictions or personal attributes.
- No raw human biometric, birth, healthcare or financial datasets.
- No synthetic benchmark, holdout selection or model fitting.
- No physical string-theory validation.

These examples are intended to sharpen the logic and typing of the proposed HUMA language only.
