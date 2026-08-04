# Compatibility, Signing, and Distribution Contracts

Load this Reference only when supported OS/app/API versions, deployment target,
archives, signing, provisioning, TestFlight, or App Store proof changes.

Official Apple Developer pages below were accessed on 2026-07-24.

## Compatibility Decision

- Read SDK, deployment target, build number, app version, framework versions,
  architectures, capabilities, and API contract from repository and artifacts.
- Define supported old-app/new-API and new-app/old-API combinations, migrations,
  feature negotiation, rejection, recovery, and observation.
- Require client tests plus API/provider evidence at each claimed combination;
  an archive, TestFlight install, or App Store acceptance proves no backend
  compatibility.

## Artifact and Distribution Proof

- Bind the selected archive to scheme, configuration, bundle ID, version/build,
  deployment target, entitlements, provisioning profile, and signing identity.
- Keep local/device, archive validation, TestFlight, and App Store evidence
  separate; exercise upgrades from supported installed versions.
- Keep certificate/profile authority, store submission, rollout, release
  approval, and rollback under `delivery-release-gate`.

## Required Record

Return the compatibility matrix, artifact identity, signing/provisioning source
without secrets, device/OS evidence, unavailable store/API proof, and risk.

## Primary Sources

- [Distributing apps for beta testing and releases](https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases/)
- [Testing a release build](https://developer.apple.com/documentation/xcode/testing-a-release-build)
- [Using the latest code signature format](https://developer.apple.com/documentation/xcode/using-the-latest-code-signature-format)
- [TestFlight](https://developer.apple.com/testflight/)

## Source Limits

These rolling sources do not establish repository SDK/deployment targets,
current signing or provisioning authority, App Store policy, actual rollout,
installed-version population, server/API behavior, or release approval.
