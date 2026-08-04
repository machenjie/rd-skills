# Jetpack Compose Contracts

Load this Reference only when Jetpack Compose changes Android state, navigation,
lifecycle, side effects, or rendering behavior. Compose remains Reference-level
detail; it is not a top-level Skill.

Official Android Developers pages below were accessed on 2026-07-24.

## Compose Decision

- Hoist state to the narrowest owner that needs to read or mutate it.
- Keep durable data ownership outside the composable.
- Separate recomposition-safe rendering from one-time effects, lifecycle work,
  navigation, and external entry handling.
- Choose saveable state only for bounded restorable values; keep durable data in
  its repository owner and bind restoration to current identity.
- Preserve stable item identity for changed collections.
- Measure recomposition or layout cost on affected hot UI paths.

## Failure Proof

- Exercise recomposition, configuration recreation, process-death restoration,
  back navigation, deep-link entry, lifecycle stop/start, and repeated effects.
- Prove stale navigation arguments and account-scoped saved state are rejected.

## Required Record

Return the state owner, event/effect boundary, restoration rule, navigation and
back behavior, lifecycle collection rule, performance evidence, Compose/library
version, proof limits, and residual risk.

## Primary Sources

- [State and Jetpack Compose](https://developer.android.com/develop/ui/compose/state)
- [Lifecycle of composables](https://developer.android.com/develop/ui/compose/lifecycle)
- [Navigation with Compose](https://developer.android.com/develop/ui/compose/navigation)
- [Compose performance best practices](https://developer.android.com/develop/ui/compose/performance/bestpractices)

## Source Limits

These rolling pages do not establish the repository's Compose, Kotlin, lifecycle,
or navigation versions, compiler settings, application architecture, measured
device performance, or non-Compose behavior. Kotlin syntax alone must not load
this Reference.
