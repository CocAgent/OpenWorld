# 28 — Human-Reviewable Certificates for Local Memory-Contract Synthesis

**Status:** Written-only proof-obligation format and finite certificate arguments. This is an adaptation of standard partition refinement and proof-trace techniques, **not an implemented or independently verified proof-carrying system**.

## 1. Distinguish an abstraction from the proof that it is adequate

Chapter 26 constructs the coarsest locally admissible tuple of equivalence relations R*. Simply publishing an interface code or a provenance polynomial does not prove that it preserves a declared contract.

A reviewer should receive *two logically separate kinds of evidence*:

1. **Positive certificate:** every admitted local query and event respects the candidate equivalence classes.
2. **Negative refinement trace:** whenever a local state pair was separated, a finite chain of declared contract obligations explains why the pair cannot remain equivalent in any admissible product-of-local-quotients abstraction.

Neither certificate establishes external source authenticity, user permission, a sound formal theorem prover, or any performance result.

## 2. Positive certificate format

Fix the finite total local model of Chapter 26, with raw state sets S_i, queries q and event rules u_e.

For each vertex i the certificate includes a finite partition R_i of S_i. For each query q and each vector z of quotient classes on its read neighborhood N_q, include a proposed decoded answer q_hat(z).

For each event e and each vector z of quotient classes on N_e, include proposed output classes v_e(z) for every component j in T_e.

A human reviewer checks that:

    q_loc(x) = q_hat([x]_(R,Nq))                      [QC]

and

    [(u_e(x))_j]_(R,j) = (v_e([x]_(R,Ne)))_j          [EC]

for every listed raw neighborhood assignment x and written j.

For a finite model this is a complete certificate of local query/event factorization. By Theorem 22.1, a correct certificate implies equality of every declared future observable answer after any finite admitted event word.

**What the certificate does not check:** that the event/read neighborhoods match real code, that an authorization policy has approved a transfer, that a stochastic system is deterministic, or that an external claim is empirically true.

## 3. Negative refinement trace format

Let R^0,R^1,...,R^K=R* be the decreasing sequence from Chapter 26. A pair (i,x,y) is **first separated at round k>=1** when

    x R^(k-1)_i y, but not x R^k_i y.

At that round, one of two reasons applies:

**Q-witness:** a declared query q reading i and a fixed assignment z to its other read coordinates such that

    q_loc(z,i=x) != q_loc(z,i=y).

**E-witness:** a declared event e reading i, a fixed assignment z to its other read coordinates, and a written coordinate j in T_e such that the two event outputs are not R^(k-1)_j-equivalent:

    (u_e(z,i=x))_j  not R^(k-1)_j  (u_e(z,i=y))_j.

Because the outputs are not equivalent at round k-1, their pair was separated in an *earlier* round. A negative trace may therefore point to the earlier pair as its prerequisite.

There is no cyclic prerequisite: along an E-witness, the round number strictly decreases. Every finite trace terminates at a Q-witness.

This is a **record of a local congruence obligation**, not automatically a single global event sequence that distinguishes the two full states under all possible companion states. Other event outputs may also change, and global observational equivalence is a distinct notion.

## 4. Proposition 28.1 — Every excluded local pair has a finite refutation chain

**Statement.** For any local state pair x,y not equivalent under R*_i, there exists a finite tree or DAG of Q-witnesses and E-witnesses, each referencing lower refinement rounds, that demonstrates why no contract-admissible product-equivalence tuple may identify that pair.

### Proof

Choose the first round k when x,y are separated. Since the pair belonged to R^(k-1)_i but not R^k_i, it must fail at least one of the two intersected conditions Q_i or E_i(R^(k-1)) defining T(R^(k-1)).

If it fails Q_i, a Q-witness exists by the finite negation of the universal query condition. Any contract-admissible H identifying x and y would violate [Q] of Chapter 26. This is a base refutation.

Otherwise it fails E_i(R^(k-1)), yielding a finite event witness and output pair (j,a,b) not in R^(k-1)_j. That output pair was separated at some earlier round l<k. By strong induction on k, it has a finite refutation chain and cannot be identified by any contract-admissible H.

But if an admissible H did identify x,y, applying its event-compatibility requirement to the event witness with all other inputs fixed would force the output pair a,b to be H_j-equivalent, contradicting the inductive refutation. Therefore no admissible H can identify x,y. QED.

This proof is equivalent in substance to the maximality argument in Chapter 26. It supplies a **reviewable witness structure** rather than a new mathematical result.

## 5. Proposition 28.2 — Positive and negative certificates are sufficient for restricted optimality

Suppose a candidate tuple R is accompanied by:

1. complete positive QC/EC checking data for every declared local assignment; and
2. for every local state pair excluded by R, a valid finite refutation chain of the form in Section 3.

Then R is the coarsest contract-admissible product equivalence relation tuple.

### Proof

The positive checks establish that R is contract-admissible. For any other contract-admissible tuple H, the negative certificate for a pair excluded by R proves that H cannot identify that pair. Therefore H_i subset R_i for every i. As R itself is admissible, it is the greatest by relation inclusion. QED.

**Qualification:** The certificate must be *complete for every excluded pair* and the reviewer must check the indicated local comparisons. Publishing only selected examples cannot certify optimality.

## 6. Finite certificate size and review cost

For each vertex i there are at most |S_i|(|S_i|-1)/2 unordered distinct state pairs. A compact negative certificate can record **one** reason for each first-separated pair, pointing to an earlier already recorded pair if needed.

The number of negative reason records is therefore at most

    sum_i choose(|S_i|,2),

with additional space for state identifiers, round numbers, local assignments, references to events/queries and the fixed contract itself.

Positive QC/EC evidence may still require a number of local assignments exponential in the **maximum neighborhood width**, as analyzed in Chapter 26. Nothing here guarantees small certificates when local neighborhoods or raw state spaces grow without bound.

For a fixed maximum local alphabet size and neighborhood width, certificate generation and verification can be organized without enumerating all global raw states. This is a **mathematical case-count statement**, not measured latency, energy consumption or monetary cost.

## 7. Counterexamples to overclaiming

**A. An incomplete positive table.** If QC is checked on only one agent assignment while another legal assignment yields a different output, the certificate is invalid. The checker must quantify over every declared local input or prove a symbolic identity covering it.

**B. Wrong target equivalence.** An event witness compared outputs under the *new* rather than the stipulated previous-round relation. Its claimed decreasing dependency may be invalid; the round and relation must be explicit.

**C. Hidden global constraint.** Some purported local raw assignments are not extendible to valid global states. The full-product refinement remains safe as a conservative sufficient contract, but its negative witnesses do not demonstrate globally necessary distinctions on a restricted coupled state space.

**D. Unchecked authority.** A provenance or access label in a table is not a signed permission. If a real event bypasses policy checks, the mathematical certificate about a specified event contract cannot authorize that behavior.

**E. Unregistered new question.** Adding an exact source-identity or future-grant query expands the contract and can invalidate the old certificate. The certificate must be versioned with the query/event vocabulary.

## 8. Human scientific-review protocol (no execution required)

A written review should ask:

1. Are source and target sorts and result tags well defined?
2. Does every query have a declared read neighborhood?
3. Does every event declare its reads, writes and errors?
4. Are local transitions total in the stated deterministic model?
5. Are the partition blocks explicitly enumerated or symbolically defined without ambiguity?
6. Are positive QC/EC obligations checked for all declared local inputs?
7. Does each negative exclusion cite a finite decreasing witness chain?
8. Are coupled-state restrictions, current authority and exact source archives stated as external conditions where required?
9. Are proofs labeled as elementary prior-art-based arguments rather than independently verified novel theorems?
10. Are any private names, identities, access credentials, raw records or archived experimental evidence absent from the public manuscript?

The next research task is to replace the overly strong full-product premise with a *reachable coupled-state* contract whose local checks remain complete and whose cost can be bounded.

**Execution freeze:** This manuscript was drafted without code execution, proof-assistant runs, tests, simulation, GitHub Actions or benchmarks.
