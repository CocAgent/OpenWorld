# 06 — Theory-Only Continuation Roadmap (Research Freeze)

**Status:** Proposed writing program; no experiments authorized or started.  
**Research intake:** OpenWorld R0 remains the execution priority; HUMA is an optional independent theory track, not a runtime dependency.

## M0 — Consolidate the conceptual record

**Deliverable:** the present directory with a traceable synopsis of the visible discussion from traditional systems through abstract information/memory representation.

Review conditions:
- all historical claims are source-attributed or explicitly provisional;
- no claim that mathematically representable symbolism is scientifically predictive;
- traditional philosophical, cultural and scientific meanings are not collapsed;
- private source, files, raw evidence and held-out seeds are not copied here.

## M1 — Complete a precise formal language

**Deliverable:** syntax of typed memory terms, well-formedness, contexts, evidence kinds, exact source objects and allowed partial translations.

Writing tasks:
- define the term grammar and its denotational interpretation;
- define typing and failure cases;
- specify when a relation is merely textual, evidential, logical or causal;
- provide at least one invalid example for each proposed transformation rule;
- distinguish formal proof, provenance and empirical status.

Exit condition: a competent independent reviewer can determine whether every sample term is valid, invalid or underspecified *from the document alone*.

## M2 — Prove foundational preservation laws on paper

**Deliverable:** fully stated propositions with proofs or correctly labelled conjectures on:

- source provenance semiring and positive-path interpretation;
- typed composition and context-boundary preservation;
- exact serializer round-trips in declared domains;
- proof-status preservation across constructors;
- revision monotonicity of history versus non-monotonicity of current access;
- limits of task-conditional lossy memory.

Exit condition: distinguish prior-art theorems from genuinely new results and link to sources.

## M3 — Identify an original research question

Potential candidate: a context-indexed, resource-bounded provenance calculus whose constructors guarantee **simultaneously**:
(1) no unauthorized evidence promotion,
(2) exact lineage where authorized and retained,
(3) explicitly partial cross-context translation,
(4) safe dependency revision.

The challenge is to state a theorem that is neither tautological nor already provided by existing typed provenance systems. If the proposed novelty collapses to a standard theorem, acknowledge that and revise the scope.

## M4 — Prepare formalization, without executing it

**Deliverable:** a written Lean 4 proof-plan, not an assertion of machine-checked theorems.

The plan should identify inductive types, totality conditions, explicit resource-budget representations, axioms, theorem signatures, dependence on libraries and potential nontermination/canonicalization issues.

Coding or proof execution, if later desired, is a **separate authorization step**; it must not automatically run experiments or CI.

## Deferred M5 — Experimental evaluation (NOT AUTHORIZED)

A future owner-reviewed protocol would need frozen versions, baseline models, matched resource budgets, independent seed splits, reproducible metrics, adversarial cases, safety/privacy review and an explicit cost ceiling. None of that evaluation is requested or performed now.

Do not present the absence of an experiment as a successful experiment.

## Resource conservation and workflow controls

- The merged [2026-11-09 Actions freeze](../../operations/RESEARCH-EXECUTION-FREEZE-20261109.md) removes automatic push/PR-triggered hosted test execution and makes W5's runner job unreachable.
- The remaining manual fast-only validation exists for explicit use but is not invoked by this theoretical work.
- No benchmark scripts, holdout seeds, private research archives, expensive tests, runners, cloud infrastructure or credentials are needed to edit these Markdown files.
- Avoid scheduling even zero-cost automatic review tasks without a new request.
- Any re-enable proposal must state a separate owner decision, budget and scope.
- CI not running must be recorded as **NOT RUN**, never PASS.

## Release and integration boundary

The folder is intended to be reviewable as public **conceptual documentation** only. Do not use this PR to add a HUMA runtime to OpenWorld, alter existing W0/W1/W2 contracts or transfer private research code. A separate public implementation requires explicit file-level approval, license/privacy review, reproducible evaluation and independent Gate #11 alignment.

## Writing-only immediate next section

Suggested next manuscript: "Typed Contextual Provenance Calculus: Syntax, Semantics and Preservation", starting with grammar rules, environment judgments and countermodels. We can author theorems and proof sketches without initiating any test or benchmark.
