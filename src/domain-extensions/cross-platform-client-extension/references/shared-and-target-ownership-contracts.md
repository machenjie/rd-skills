# Shared and Target Ownership Contracts

Load this Reference only when shared code, adapters, or native platform behavior
can change ownership of an installed-client decision.

Official framework documentation below was accessed on 2026-07-24.

## Decision Boundary

- Map shared domain, presentation, persistence, adapter, and native integration
  owners for every confirmed target.
- Keep lifecycle, permission, accessibility, packaging, signing-input, and OS
  integration decisions with each concrete platform Domain.
- Define which platform differences remain explicit rather than hidden behind a
  least-common-denominator interface.
- Bind state restoration and account invalidation to the actual platform event,
  storage, and process model.

## Failure Proof

- Exercise a shared state transition through every affected target adapter.
- Prove platform-only lifecycle and permission failures do not corrupt shared
  state or repeat effects.
- Build the release-shaped artifact for each target and record excluded targets.

## Required Record

Return the ownership map, concrete platform Domains, accepted abstraction,
exposed platform deltas, artifact evidence, proof limits, and residual risk.

## Primary Sources

- [Flutter supported deployment platforms](https://docs.flutter.dev/reference/supported-platforms)
- [React Native platform-specific code](https://reactnative.dev/docs/platform-specific-code)
- [Kotlin Multiplatform project structure](https://kotlinlang.org/docs/multiplatform/multiplatform-discover-project.html)
- [.NET MAUI invoke platform code](https://learn.microsoft.com/en-us/dotnet/maui/platform-integration/invoke-platform-code)

## Source Limits

These rolling and versioned pages describe framework mechanisms and support,
not this repository's target, owner, release, lifecycle, or artifact matrix.
Framework availability never proves a published or supported target.
