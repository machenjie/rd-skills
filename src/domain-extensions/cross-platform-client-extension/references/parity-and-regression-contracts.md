# Parity and Regression Contracts

Load this Reference only when cross-target behavior, UI, accessibility,
lifecycle, failure, or regression parity affects acceptance.

Official framework documentation below was accessed on 2026-07-24.

## Decision Boundary

- Define behavior parity separately from UI parity.
- Define behavior parity as equivalent user outcome, state transition,
  authorization, recovery, and failure semantics for the supported target set.
- Define UI parity separately; allow platform-native layout, input, window,
  navigation, and accessibility behavior when the outcome remains accepted.
- Partition shared, adapter-contract, platform integration, and release-artifact
  tests; bind each assertion to the layer it can prove.
- Preserve explicit target exclusions and platform deltas instead of weakening
  the common oracle.

## Failure Proof

- Run shared contract tests and target-specific lifecycle, input, accessibility,
  permission, offline, upgrade, and recovery cases.
- Compare negative and boundary outcomes across targets, not screenshots alone.
- Reproduce a platform-only regression through its native boundary and final
  artifact.

## Required Record

Return the behavior and UI parity definitions, target matrix, oracle by layer,
accepted deltas, regression evidence, untested paths, and residual risk.

## Primary Sources

- [Flutter testing overview](https://docs.flutter.dev/testing/overview)
- [React Native testing overview](https://reactnative.dev/docs/testing-overview)
- [Electron testing](https://www.electronjs.org/docs/latest/development/testing)
- [Kotlin Multiplatform run tests](https://kotlinlang.org/docs/multiplatform/multiplatform-run-tests.html)

## Source Limits

Framework test documentation does not prove application behavior, platform
parity, accessibility, artifact coverage, or supported targets. A shared test,
snapshot, or one-target run cannot establish cross-platform equivalence.
