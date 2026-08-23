# Compatibility, Packaging, and Performance Implementation and Review Evidence

Load this Reference only after the accepted compatibility/artifact
`decision-record` must be implemented or reviewed.

## Evidence

- Inspect the final APK/AAB, manifest merge, split identities, and signing
  identity for the selected variant.
- Remove affected blocking work from the main thread.
- Measure current ANR and startup acceptance on representative hardware, API
  levels, memory classes, and architectures.
- Keep emulator, local APK, release AAB, Play-generated artifact, and field
  vitals as separate proof classes.

## Required Record

Return artifact identity, measurements, device matrix, unavailable proof,
authorization owner, proof limits, and residual risk.
