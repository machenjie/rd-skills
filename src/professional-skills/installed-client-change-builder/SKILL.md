---
name: installed-client-change-builder
description: "Use `task-agent` for accepted Android, iOS/iPadOS, desktop, or cross-platform installed-client source changes. Skip browser/PWA-only, backend, infrastructure, release approval, and independent review work."
---

# installed-client-change-builder

## Role

Support `task-agent` in changing installed application source while preserving
platform lifecycle, local state, operating-system integration, and packaging behavior.

## When To Use

- installed client implementation
- Android iOS iPadOS Windows macOS or Linux desktop application change
- Flutter React Native Electron Tauri Qt .NET MAUI or Kotlin Multiplatform client change

## Do Not Use

- browser or PWA-only change
- backend or infrastructure change
- documentation-only change or multi-task planning
- production release store approval rollback approval or independent review

## Required Inputs

- accepted design and observable client behavior
- exact target platforms, framework versions, and build variants
- UI, state, lifecycle, persistence, and platform-integration ownership
- API compatibility, permission, packaging, and non-production validation constraints

## Professional Decision Rules

- Keep presentation state in the narrowest current owner across shared and native layers.
- Model cold start, foreground, background, suspension, termination, and restoration separately when they are reachable.
- Preserve denial, revocation, deep-link, notification, local-data, offline, and operating-system integration outcomes when affected.
- Confirm API and stored-data compatibility across supported client versions before changing a shared contract.
- Validate shared behavior on every affected native target.
- Do not treat framework-only tests as platform-packaging proof.
- Treat build targets and release configuration as evidence; never infer target platforms from the framework name.

## High-Value Gotchas

- A framework lifecycle callback does not prove survival after operating-system process termination.
- Permissions can be denied or revoked outside the current screen flow.
- Deep links and notifications can enter through cold, warm, or already-running paths.
- Local data and queued offline work can outlive the client or server version that created them.
- A successful shared test can miss native manifest, entitlement, signing, or package defects.

## Execution Checklist

1. Inspect the accepted design, current owner, minimum consumer, tests, build targets, and release configuration.
2. Map normal, denied, invalid, interrupted, offline, restored, and version-skew outcomes that the change can reach.
3. Reuse the current platform seam and implement the smallest complete source change.
4. Run target-relevant unit, UI, lifecycle, persistence, permission, link, notification, offline, and compatibility checks.
5. Build or render affected packages when packaging metadata or native integration changes.
6. Stop closure when any affected path lacks fresh evidence.

## Stop / Escalation Conditions

- Stop implementation when target discovery remains inconclusive after repository inspection.
- Ask one bounded target question after that inspection remains inconclusive.
- Stop when UI/state ownership, lifecycle restoration, local-data migration, permission behavior, or API compatibility remains implicit.
- Stop when an affected native target, SDK, entitlement, manifest, signing identity, package format, or test environment cannot be inspected.
- Route production release, store submission or approval, staged rollout, and rollback decisions to `delivery-release-gate`.
- Do not claim full watchOS, tvOS, or visionOS coverage from this Skill.
- Do not perform or claim independent review.

## Output Contract

- changed files with target, owner, reuse, and placement decisions
- affected UI, lifecycle, local-data, permission, link, notification, offline, and API-version outcomes
- current target-specific tests, build or package evidence, and skipped or unavailable checks
- compatibility and migration decisions with proof limits
- residual client risk and release owner

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [native platform source contracts](references/native-platform-source-contracts.md) | targeted | Android iOS/iPadOS Windows macOS or Linux desktop lifecycle permission link OS integration or packaging behavior affects the change | Only shared framework behavior changes and native target contracts remain untouched | task-agent | boundary-decision, proof-limit, validation-plan |
| [framework contracts](references/framework-contracts.md) | targeted | Flutter React Native Electron Tauri Qt .NET MAUI or Kotlin Multiplatform ownership bridge lifecycle or packaging behavior affects the change | The client is native-only or the framework layer is not affected | task-agent | proof-limit, selected-approach, validation-plan |
