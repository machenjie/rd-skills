# Compatibility, Signing, and Distribution Implementation and Review Evidence

Load this Reference only after the accepted compatibility and artifact
`decision-record` must be implemented or reviewed.

## Required Decision Input

Use the carried version matrix, artifact identity, and channel decision. Stop
when a claimed app/API combination or signing source is not current.

## Implementation and Review Evidence

- Bind the archive to scheme, configuration, bundle ID, version/build,
  deployment target, entitlements, provisioning profile, and signing identity.
- Keep local/device, archive validation, TestFlight, and App Store evidence
  separate; exercise upgrades from supported installed versions.
- Require client plus API/provider evidence for every claimed old/new
  combination. Packaging or store evidence proves no backend compatibility.
- Keep certificate/profile authority, submission, rollout, release approval,
  and rollback under `delivery-release-gate`.

## Required Record

Return the exercised version matrix, immutable artifact identity,
signing/provisioning-source limits, device/OS evidence, unavailable store/API
proof, and residual risk.
