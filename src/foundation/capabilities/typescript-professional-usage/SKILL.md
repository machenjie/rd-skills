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

Protect TypeScript runtime narrowing, structural-type limits, unsafe escapes, promise and cancellation behavior, JavaScript numeric semantics, and emitted-module compatibility. Exclude product-state, API, package, and bundler decisions.

## High-Value Rules

- Establish accepted runtime shape and compatibility from the actual producer, trust/version boundary, and current generation, storage, or prior parsing guarantees. Add owned runtime validation with an explicit invalid-input outcome where those guarantees leave a gap; TypeScript declarations alone prove neither safety nor runtime shape.
- Structural assignability can admit extra capabilities, lose nominal identity, or collapse absent and present-undefined; use discriminants, exact parsers, brands, or `satisfies` when a concrete invariant requires them, not as universal decoration.
- Scope `any`, assertions, non-null operators, and suppressions to inspected evidence; an escape at a trust, storage, generated, or public boundary has an owner and cleanup trigger.
- Observe every owned promise and background task, propagate `AbortSignal` or equivalent cancellation where the boundary supports it, and settle cleanup and state transitions for rejection, timeout, and stale completion.
- Classify safe integers, fractions, `NaN`, infinities, decimal money, `bigint`, serialized numbers, and units wherever conversion or comparison changes behavior.
- Review type-only versus runtime imports, side effects, ESM/CJS and conditional exports, module resolution, declaration emission, and generated entrypoints against each supported runtime and build target.
- Verify public-type and generated-contract changes with named consumer compilation scoped to the selected config, files, and module graph.
- Add runtime version-skew cases when the changed contract affects or can mismatch supported runtime behavior; source/emission evidence may establish an unchanged runtime boundary.

## Anti-Patterns

- A type annotation, assertion, schema type, or successful compilation is treated as runtime validation.
- Structural compatibility lets a database/domain object or authority-bearing value cross a DTO, SDK, storage, or message boundary unchanged.
- A floating promise, broad catch, default value, or stale completion hides rejection, cancellation, or user-visible state.
- Type tests pass while emitted imports, package exports, side effects, declarations, or numeric serialization fail at runtime.

## Stop Conditions

- Stop fail-closed when decisive runtime, consumer, module-emission, or validation evidence is unknown or unavailable.
- Do not select behavior from typecheck-only or assumed evidence.
- Route API/SDK, product-state, money/timezone, security, package, build, runtime-performance, and testing decisions to their named owners.

## Output Contract

- TypeScript semantic decision with runtime boundary, structural-type limits, and bounded escapes; async, cancellation, and numeric behavior; module emission and public/generated compatibility; proof limits and specialist routes.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | A TypeScript change affects runtime validation structural typing unsafe escapes async numeric module-emission or public-type semantics | The TypeScript edit preserves these boundaries and established compiler plus runtime behavior resolves the mechanism | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
