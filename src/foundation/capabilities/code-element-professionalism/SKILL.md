---
name: code-element-professionalism
description: "`analysis-agent`/`task-agent`/`review-agent`: use when variables, expressions, or statements can alter local semantics; skip structure, API, language, or runtime ownership."
---

# code-element-professionalism

## Registry Trigger

**Use when**

- A variable has ambiguous initialization, sentinel meaning, scope, lifetime, mutation, capture, alias, or shadowing.
- An expression or statement can hide defaulting, coercion, evaluation order, fallthrough, cleanup, termination, or local effect order.

**Do not use when**

- The unresolved decision is function, class, file, directory, module, signature, or public-API ownership.
- The issue depends on language/runtime semantics, performance, concurrency, transaction boundaries, or cross-system side effects beyond the local element.

## Skill Role

Protect local value-state distinctions, evaluation behavior, and exit obligations. Exclude broader flow, placement, public contracts, language/runtime rules, performance, and distributed effect coordination.

## High-Value Rules

- A material variable has a first valid value, one semantic concept, bounded scope and lifetime, and an owner for mutation, aliases, captures, cleanup, and reset.
- Missing, false, zero, empty, unknown, denied, expired, partial, error, and not-loaded remain distinct wherever behavior differs; convenience defaults do not become policy.
- Shadowing or reuse cannot hide a material error, tenant, permission, transaction, resource, cursor, or lifecycle phase from the later read, commit, close, or return.
- A material expression exposes coercion, narrowing, precedence, short-circuit, and evaluation-order assumptions; apparently pure reads do not hide mutation, I/O, time, randomness, environment, or secrets.
- Branch, loop, retry, return, throw, and fallthrough statements preserve termination, partial progress, caller-visible failure, and cleanup across success, error, cancellation, and timeout exits.
- Ignored results, empty branches, no-op catches, and detached work carry an explicit semantic reason and cannot suppress an obligation or failure.
- When local order reaches commit, event, cache, notification, external I/O, lock, or async lifecycle boundaries, stop local review.
- Route the owning transaction, side-effect, concurrency, or reliability decision.

## Anti-Patterns

- One sentinel or falsey fallback collapses states that drive different authorization, persistence, or response behavior.
- A concise expression hides assignment, mutation, lossy conversion, side effects, or runtime-dependent evaluation.
- An early return, broad catch, or fallthrough skips resource release, audit, rollback, error translation, or response work.
- A local fix invents a global constant, public helper, new object, or file to avoid resolving the real owner.

## Stop Conditions

- Route broader readability to `code-clarity-maintainability`, placement or signatures to `implementation-structure-design`, public shape to the relevant API capability, and behavior-preserving movement to `refactoring`.
- Route language rules to `language-idiom-enforcement`, runtime cost or safety to `language-performance-safety`, and commit/effect order to `transaction-consistency` or `data-side-effect-flow-tracing`.

## Output Contract

- local code-element decision with affected element and inspected scope, preserved value-state and exit obligations, semantic risk and selected change, current evidence, proof limits, residual risk, and required specialist handoffs

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [variables](references/variables.md) | targeted | A code-element decision depends on variable initialization sentinel scope mutation capture alias or lifetime semantics | The variable is an immutable local with an immediate unambiguous initializer and no escaped alias | task-agent, review-agent, analysis-agent | decision-record, evidence-gap |
| [expressions](references/expressions.md) | targeted | A material expression can change defaulting coercion evaluation order conversion or hidden effects | The expression is a language-conventional value computation with obvious semantics and no material side effect | task-agent, review-agent, analysis-agent | validation-plan, proof-limit |
| [statements](references/statements.md) | targeted | A statement can change termination cleanup error translation fallthrough commit-effect order lock scope or async lifecycle | The statement sequence is straight-line local code with no material exit resource transaction concurrency or async boundary | task-agent, review-agent, analysis-agent | failure-decision, residual-risk |
