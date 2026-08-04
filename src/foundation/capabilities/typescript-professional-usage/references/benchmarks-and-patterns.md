# TypeScript Runtime And Module Contract

This contract focuses TypeScript review on erased types, structural assignability, JavaScript runtime semantics, and emitted package behavior.

## TypeScript Decision Matrix

| TypeScript facet | Facts to establish | Accident signal |
| --- | --- | --- |
| Runtime boundary | Producer, trust/version boundary, parser/schema owner, accepted and rejected shapes, error mapping, and persisted/historic data | A type annotation or generated interface is treated as validation |
| Structural typing | Required capabilities, excess properties, optional-property presence, undefined, variance, nominal identity, discriminant, and exactness need | Assignability accepts an authority-bearing or semantically different value that happens to share fields |
| Unsafe escape | Location and scope of `any`, assertion, non-null, suppression, unchecked index, or catch value plus safer alternative and cleanup trigger | The escape crosses API, storage, message, generated, or public boundaries and silently propagates |
| Async and cancellation | Promise owner, rejection observation, AbortSignal/deadline propagation, stale completion, cleanup, and state transition | Floating or late work mutates state after cancellation or a broad catch hides failure |
| Numeric and value semantics | Safe-integer need, fraction and decimal policy, `NaN`/infinity, `bigint`, units, JSON/storage encoding, and comparison rules | Identifier, money, time, counter, or quantity loses precision or changes representation |
| Module and emission | Type-only/runtime imports, side effects, ESM/CJS, conditional exports, resolution mode, target, declaration emission, and entrypoints | Typecheck passes while the emitted loader, export condition, tree-shaking, or side effect fails |
| Public and generated types | Source authority, declaration and schema versions, named consumers, compatibility class, generated output, and runtime skew | Consumer types compile against a shape that the deployed runtime does not produce or accept |
| Proof boundary | tsconfig and file set, runtime/bundler versions, typecheck/lint, malformed fixture, consumer build, emitted-artifact test, and not-run limits | One editor or compiler configuration is generalized beyond its inspected packages to browsers, runtimes, or consumers it did not exercise |

## Decision Limits

- The current tsconfig inheritance, runtime, bundler, package exports, generated authority, and supported consumers determine the applicable semantics.
- Typecheck establishes the selected program and configuration; it does not establish runtime input safety, emitted-module behavior, numeric suitability, or consumer deployment.
- Route state, public contracts, security, packages/builds, performance, and test-portfolio conclusions to their specialist owners.
