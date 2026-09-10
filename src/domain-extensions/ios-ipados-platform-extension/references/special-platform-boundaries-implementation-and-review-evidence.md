# Special Platform Boundaries Implementation and Review Evidence

Load this Reference only after the accepted special-platform
`boundary-decision` must be implemented or reviewed.

## Required Decision Input

Use the carried per-platform support state and target-specific obligations.
Stop when watchOS, tvOS, or visionOS scope is implicit or inherited from iOS.

## Implementation and Review Evidence

- Keep shared-source evidence separate from platform-specific executable and
  device evidence.
- Reject coverage based only on shared Swift/SwiftUI, simulator compilation,
  iPhone behavior, bundle code, or one App Store record.
- Mark coverage unproven when target-specific lifecycle, interaction, artifact,
  or representative-device evidence is unavailable.

## Required Record

Return one row per special platform with support state, repository/artifact
owner, exercised obligations, unavailable proof, proof limits, and risk.
