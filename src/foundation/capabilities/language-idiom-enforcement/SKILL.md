---
name: language-idiom-enforcement
description: "`analysis-agent`/`task-agent`/`review-agent`: use when idioms for errors, types, resources, modules, naming, concurrency, or APIs need enforcement; skip when idioms are unaffected."
---

# language-idiom-enforcement

## Registry Trigger

**Use when**

- language idioms error handling type modeling resource management module boundaries naming casing visibility exports public API naming predicate boolean names collection names concurrency formatting standard library hallucinated APIs non idiomatic code

**Do not use when**

- no task-local language idiom enforcement decision is required

## Skill Role

Select language-native expressions that affect correctness, ownership, failure handling, public contracts, or maintainability. Exclude formatting-only enforcement, runtime selection, and performance proof.

## High-Value Rules

- **Start from current repository and language authority.** Inspect nearby accepted code, configured compiler or linter rules, supported language version, public conventions, and framework constraints before proposing an idiom.
- **Use types to make invalid states harder to represent.** Prefer the language's established nullability, sum or sealed type, value object, ownership, result, and collection semantics when they clarify the task-local invariant.
- **Preserve failure and resource semantics.** Choose error propagation, wrapping, cleanup, cancellation, and lifetime patterns that retain actionable context without leaking resources or swallowing control flow.
- **Respect concurrency conventions with semantic evidence.** Match the runtime's synchronization, task, cancellation, and shared-state model; route measured scheduling or memory-safety questions to the performance-safety owner.
- **Treat public naming and module shape as contracts.** Check exported symbols, predicates, callbacks, generic constraints, extension points, serialization-visible names, and generated surfaces before normalizing style.
- **Keep documentation syntax within its owner.** Limit this Skill to repository-backed language syntax and public-surface requirements, leaving semantic-explanation decisions to `code-clarity-maintainability`.
- **Justify deviations by constraint.** Keep a non-idiomatic form only when compatibility, generated code, framework protocol, performance evidence, or repository policy requires it, and record the boundary that prevents normalization.
- **Validate changed semantics, not stylistic conformity alone.** Use compile, static analysis, focused tests, and public-surface comparison appropriate to the affected ownership, error, or API behavior.

## Anti-Patterns

- Apply a generic language style guide over stronger repository, framework, generated-code, or compatibility evidence.
- Replace explicit domain meaning with clever syntax, compressed control flow, or an abstraction unfamiliar to the owning codebase.
- Label code non-idiomatic without naming the semantic risk, authoritative convention, and behavior-preserving alternative.

## Stop Conditions

Escalate when repository and language authorities conflict, public compatibility is uncertain, or the proposed idiom changes ownership or concurrency behavior. Also escalate when generated or framework code controls the surface, or validation cannot distinguish style from semantic change.

## Output Contract

- language-idiom decision with current authority, affected semantic boundary, chosen pattern, justified deviations, compatibility effects, and validation evidence

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | local convention and language idiom suggest competing public-surface choices | one established repository idiom determines the changed surface | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | changed code affects public contracts errors resources concurrency or boundaries | formatter and adjacent conventions cover the local-only change | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | idiom API stability or AI-symbol claims need current validation | post-edit checks and inspected local examples prove each claim | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
