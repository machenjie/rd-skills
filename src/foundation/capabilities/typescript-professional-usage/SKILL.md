---
name: typescript-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use when TypeScript runtime validation, structural typing, async, numeric, or module semantics change; skip generic work."
---

# typescript-professional-usage

## Registry Trigger

**Use when**

- Inspect or change TypeScript trust-boundary validation, structural assignability, unsafe escapes, async cancellation, numeric meaning, emitted modules, or public declarations.
- Browser, Node, SDK, generated-client, storage, message, or package-export behavior can differ from what the type checker accepts.

**Do not use when**

- The open question is generic frontend state, API policy, package/build configuration, performance, testing, or language style without a TypeScript-specific semantic risk.
- No task-local TypeScript source, declaration, generated surface, compiler boundary, or emitted runtime behavior requires inspection or change.

## Skill Role

Protect TypeScript runtime semantics.

## High-Value Rules

- Derive runtime shape/compatibility from producer, trust/version and generation/storage/parsing guarantees. Gaps require owned validation/invalid-input outcomes; declarations prove no runtime shape/safety.
- Structural assignability can admit extra capabilities, erase nominal identity, or conflate absent/present-undefined. Add discriminants, exact parsers, brands, or `satisfies` only for concrete invariants.
- `any`, assertions, non-null operators, and suppressions need inspected evidence; boundary escapes (trust/storage/generated/public) need owners and cleanup triggers.
- Require observation of owned promises/background tasks; propagate supported cancellation (`AbortSignal` or equivalent); settle cleanup/state on rejection, timeout or stale completion.
- Classify safe integers, fractions, `NaN`, infinities, decimal money, `bigint`, serialized numbers, and units at behavior-changing conversions/comparisons.
- Check emitted imports (type-only/runtime), side effects, ESM/CJS/conditional exports, module resolution, declarations, and generated entrypoints on every supported runtime/build target.
- Verify public/generated types through named consumer compilation using selected config/files/module graph.
- Test version skew for contracts affecting or mismatching supported runtime behavior; source/emission evidence can prove unchanged boundaries.

## Anti-Patterns

- Types/compilation substitute for runtime validation.
- Structural compatibility moves domain/database objects or authority across DTO/SDK/storage/message boundaries.
- Unobserved promises, broad catches/defaults, or stale completion hide rejection, cancellation, or user-visible state.
- Type tests miss emitted-module/numeric-serialization failures.

## Stop Conditions

- Absent decisive runtime/consumer/emission/validation evidence, fail closed; types/assumptions cannot select behavior.
- Route API/SDK, product-state, money/timezone, security, package/build/bundler, runtime-performance/testing to their owners.

## Output Contract

- TypeScript semantic decision with runtime boundary, structural-type limits, and bounded escapes; async, cancellation, and numeric behavior; module emission and public/generated compatibility; proof limits and specialist routes.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | A TypeScript change affects runtime validation structural typing unsafe escapes async numeric module-emission or public-type semantics | The TypeScript edit preserves these boundaries and established compiler plus runtime behavior resolves the mechanism | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
