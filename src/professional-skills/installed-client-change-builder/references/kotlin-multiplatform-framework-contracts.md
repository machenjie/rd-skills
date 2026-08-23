# Kotlin Multiplatform Framework Contracts

Use this Reference only for the named kotlin-multiplatform-framework-contracts decision.

## Decision Rules

- Put shared behavior only in source sets whose declared targets support it.
- Validate each target compilation and final binary or host-application integration.

## Sources And Version Limit

Sources: [project structure](https://kotlinlang.org/docs/multiplatform/multiplatform-discover-project.html), [expected and actual declarations](https://kotlinlang.org/docs/multiplatform/multiplatform-expect-actual.html), and [native binaries](https://kotlinlang.org/docs/multiplatform/multiplatform-build-native-binaries.html).
Version limit: Kotlin and target stability are time-varying. Do not infer supported targets, Compose Multiplatform use, binary production, or host packaging from KMP alone.
