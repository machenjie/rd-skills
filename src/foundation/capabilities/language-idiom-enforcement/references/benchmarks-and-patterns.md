# Language Idiom Benchmarks And Patterns

Use this reference when `language-idiom-enforcement` needs deeper cross-language or repository-convention review than the root `SKILL.md` should carry. Keep the root focused on selection, non-negotiables, and evidence; use this file for repeated idiom traps and deviation records.

## Cross-Language Contamination Matrix

| Signal | Hidden risk | Safer treatment |
| --- | --- | --- |
| Java-style factories and interfaces appear in Go, Rust, or TypeScript without multiple implementations. | Abstraction cost hides simple ownership and makes tests mock internals. | Prefer concrete type or local function until variation is real. |
| Python-style dynamic maps appear in TypeScript, Java, or Rust public surfaces. | Runtime boundary and null/default semantics bypass the type system. | Use typed schema, value object, enum, or discriminated union. |
| Callback or promise style is mixed with structured concurrency idioms. | Cancellation, cleanup, and error propagation become unclear. | Use the runtime-native concurrency model and record cleanup path. |
| Shell strings, SQL strings, or path joins are hand-built in typed languages. | Injection and platform bugs survive static typing. | Use parameterized APIs, path libraries, and hostile-input tests. |
| Test helper exports private code to make assertions easy. | Tests freeze implementation and miss public behavior. | Assert through public behavior or declare a narrow test seam. |

## Public Surface Idiom Checklist

- Naming, visibility, module path, and package layout follow nearby repository examples before generic style guides.
- Public doc comments use the language-standard format and state behavior, inputs, outputs, errors/results, side effects, concurrency, and examples when non-trivial.
- Error/result/nullability contracts are language-native and stable for consumers.
- Generated surfaces stay generated; handwritten adapters own idiom and compatibility decisions.
- Deviations include owner, scope, expiration, and validation proof.

## Standard-Library Preference

- Prefer the standard library or already-approved dependency for parsing, paths, dates, HTTP, concurrency, logging, and serialization when it satisfies the current requirement.
- Add a dependency only when current behavior needs capability the local stack cannot provide, and record license, security, maintenance, and bundle/runtime cost.
- Reject generic helper packages that duplicate language-native primitives or local conventions.

## Deviation Record

```markdown
Language Idiom Deviation
- Language and local convention:
- Rule:
- Reason:
- Scope:
- Owner:
- Expiration or cleanup trigger:
- Validation proving the exception is bounded:
- What remains unproven:
```
