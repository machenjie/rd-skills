# Kotlin Type, Interop, And DSL Contracts

Use this checklist when Kotlin type features or Java-facing boundaries can change caller-visible meaning.

## Boundary Checklist

- **Nullability:** record platform types, flexible generic arguments, collection elements, reflection, serialization, persistence, generated surfaces, and the runtime validation or narrowing location.
- **Java interop:** inspect emitted signatures, property/accessor names, checked exceptions, default arguments, wildcards, SAM use, nullability annotations, and Java call sites.
- **Sealed hierarchy:** establish the module/package closure, external implementor contract, serialization tags, and how new variants reach compiled consumers.
- **Reified and inline API:** prove call-site code growth, visibility restrictions, non-reified fallback, reflection need, and binary compatibility.
- **Data class:** verify identity meaning, generated equality/hash, component order, shallow `copy`, mutable members, and inheritance or persistence expectations.
- **Value class:** verify boxing locations, nullable/generic/interface use, name mangling, Java exposure, reflection/serialization representation, and underlying-value validation.
- **Variance:** trace producer/consumer direction and star projection through Java/raw/generated callers rather than relying on local compilation.
- **Delegated property:** define the property/delegate owner, `getValue`/`setValue` state semantics, delegate lifecycle/threading, Java/reflection exposure, invalid read/write behavior, and verification output.
- **DSL:** inspect receiver hierarchy, `@DslMarker`, labels, builder escape, mutation owner, validation timing, and side effects before commit.

## Failure Probes

- Pass a runtime null from a Java, reflection, generated, or persisted boundary.
- Compile or execute the relevant Java caller and inspect the emitted signature when ABI is affected.
- Add an allowed sealed subtype, box a value class through generic/interface/nullable use, and copy a data class with mutable nested state.
- Verify first/repeated reads, accepted/rejected writes, owner teardown, and Java/reflection access through recorded `getValue`/`setValue` and failure output.
- Nest DSL receivers with the same member name and exercise invalid partial construction.

## Primary Sources

- [Calling Java from Kotlin](https://kotlinlang.org/docs/java-interop.html)
- [Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html)
- [Null safety](https://kotlinlang.org/docs/null-safety.html)
- [Sealed classes and interfaces](https://kotlinlang.org/docs/sealed-classes.html)
- [Inline functions and reified parameters](https://kotlinlang.org/docs/inline-functions.html)
- [Inline value classes](https://kotlinlang.org/docs/inline-classes.html)
- [Data classes](https://kotlinlang.org/docs/data-classes.html)
- [Delegated properties](https://kotlinlang.org/docs/delegated-properties.html)
- [Type-safe builders](https://kotlinlang.org/docs/type-safe-builders.html)

Official pages in this reference were recorded as accessed on 2026-07-24.

## Version And Inference Limits

- Kotlin documentation/specifications are rolling; prove compiler, language/API, target backend, Java level, and plugin versions from current evidence.
- Documented source semantics do not prove the emitted ABI, delegate field/lifetime, reflection adapter, serializer, persistence provider, or generated caller used by the project.
- Do not infer Java-callable compatibility from Kotlin compilation or infer deep immutability from `data`, `val`, `sealed`, or value-class syntax.

## Required Record

- Record each changed type/delegate boundary, owner and get/set output, actual caller/runtime evidence, selected representation, invalid behavior, compatibility limit, and residual risk.

## Anti-Patterns

- `!!`, a platform type, or a generated annotation is treated as runtime null proof.
- Data-class `copy`, a value wrapper, sealed `when`, or `remember` is treated as deep immutability, stable ABI, future exhaustiveness, or durable state.
