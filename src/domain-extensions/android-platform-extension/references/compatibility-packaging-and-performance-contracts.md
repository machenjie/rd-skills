# Compatibility, Packaging, and Performance Contracts

Load this Reference only when Android version compatibility, final artifacts,
signing inputs, Play packaging, ANR, startup, or device proof changes.

Official Android Developers and Google Play pages below were accessed on
2026-07-24.

## Compatibility and Artifact Decision

- Read minimum, target, and compile SDKs, manifest merges, package/application
  identity, ABI/resource splits, variant, and dependency versions from the tree.
- Guard platform behavior by the affected runtime API and supported devices;
  compilation success is not compatibility proof.
- Inspect the final APK/AAB and signing identity for the selected variant.
- Keep upload-key handling, app-signing authority, Play submission, rollout,
  approval, and rollback under `delivery-release-gate`.

## Responsiveness and Device Proof

- Define ANR and startup acceptance from current product baselines and affected
  cold, warm, restored, and externally launched paths.
- Remove blocking work from the main thread.
- Measure on representative supported hardware, API levels, memory classes,
  and architectures.
- Keep emulator, local APK, release AAB, Play-generated artifact, and field-vitals
  evidence as separate proof classes.

## Required Record

Return SDK and compatibility guards, variant/package/artifact identity, signing
source without secrets, current Play-policy check, ANR/startup measurements,
device matrix, unavailable proof, authorization owner, and residual risk.

## Primary Sources

- [App compatibility](https://developer.android.com/guide/app-compatibility)
- [Android App Bundles](https://developer.android.com/guide/app-bundle)
- [Sign your app](https://developer.android.com/studio/publish/app-signing)
- [Target API level requirements](https://support.google.com/googleplay/android-developer/answer/11926878)
- [ANRs](https://developer.android.com/topic/performance/vitals/anr)
- [App startup time](https://developer.android.com/topic/performance/vitals/launch-time)
- [Test on Android](https://developer.android.com/training/testing/fundamentals/strategies)

## Source Limits

Android and Play pages are rolling contracts. They do not establish this
repository's SDKs, current policy deadline, signing authority, generated splits,
vendor behavior, production vitals, or device/form-factor coverage. Recheck
current sources; do not infer release approval from source validation.
