# Special Platform Boundaries

Load this Reference only for an explicit watchOS, tvOS, or visionOS target or
coverage claim adjacent to iOS/iPadOS work.

Official Apple Developer pages below were accessed on 2026-07-24.

## Coverage Boundary

- Record separate watchOS, tvOS, and visionOS states: supported-and-proven,
  supported-with-gaps, explicitly unsupported, or unknown.
- Do not inherit lifecycle, interaction, scene, display, input, background,
  entitlement, package, store, performance, or accessibility proof from iOS or
  iPadOS.
- Resolve the target's repository, build, artifact, deployment, capability, and
  device facts before selecting its platform rules.
- Keep shared-source evidence separate from platform-specific executable and
  device evidence.

## Failure Proof

- Reject claims based only on shared Swift, SwiftUI, bundle code, simulator
  compilation, iPhone behavior, or one App Store record.
- Mark coverage unproven when target-specific lifecycle, interaction, artifact,
  or representative device evidence is unavailable.

## Required Record

Return one row per special platform with support state, repository and artifact
owner, target-specific obligations, evidence, unavailable proof, and risk.

## Primary Sources

- [watchOS](https://developer.apple.com/watchos/)
- [tvOS](https://developer.apple.com/tvos/)
- [visionOS](https://developer.apple.com/visionos/)

## Source Limits

These rolling overview pages do not prove repository target declarations,
current SDK or store requirements, complete platform behavior, actual hardware,
reviewer qualification, or production support.
