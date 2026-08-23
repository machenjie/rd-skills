# Framework Target Evidence Contracts

Load this Reference only when framework capability, repository targets, build
configuration, release configuration, or published artifacts determine scope.

Official framework documentation below was accessed on 2026-07-24.

## Evidence Order

- Prove targets from repository, build targets, release configuration, or published artifacts without framework inference.
- Inspect repository manifests, source sets, platform directories, build
  targets, CI jobs, release configuration, and published artifacts.
- Record only targets supported by task evidence; distinguish compilable,
  tested, packaged, published, and supported states.
- Use framework documentation to test feasibility and version compatibility,
  never to infer that the repository ships every framework-supported target.
- Keep this modifier unloaded while the concrete set remains unknown.
- After inspection, ask one bounded question naming the unresolved targets.

## Routing Boundary

- When task evidence confirms an affected concrete target, load its registered
  platform Domain with this modifier under `installed-client-change-builder`.
- Keep confirmed targets in a cohesive executable slice when dependency,
  ownership, write, validation, release, rollback, and integration-risk
  boundaries stay cohesive.
- Use analysis-first splitting when those boundaries create separately
  executable work.
- A framework name without a confirmed platform target loads no Domain.

## Required Record

Return the inspected evidence, concrete target matrix, publication status,
routing decision, one unresolved question if needed, and proof limits.

## Primary Sources

- [Flutter supported deployment platforms](https://docs.flutter.dev/reference/supported-platforms)
- [Qt supported platforms](https://doc.qt.io/qt-6/supported-platforms.html)
- [.NET MAUI supported platforms](https://learn.microsoft.com/en-us/dotnet/maui/supported-platforms)
- [Kotlin Multiplatform supported platforms](https://kotlinlang.org/docs/multiplatform/supported-platforms.html)
- [Tauri distribution](https://v2.tauri.app/distribute/)

## Source Limits

These pages are rolling or version-specific support statements. They do not
prove repository target selection, artifact publication, release support,
account ownership, or the installed toolchain. Recheck exact versions.

## High-Value Gotchas

- Shared or compile-time success can hide target-specific lifecycle, permission, accessibility, packaging, or runtime failure.

## Execution Checklist

- Verify ownership, compatibility, normal, failure, upgrade, and artifact behavior per affected target.
- Report the target matrix, source freshness, untested targets, non-inferences, and residual risk.
