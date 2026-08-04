---
name: ios-ipados-platform-extension
description: Use when an installed-client change has a confirmed iOS or iPadOS target and changes Apple mobile platform behavior.
---

# ios-ipados-platform-extension

## Role

This focused Layer 3 Domain Skill modifies `installed-client-change-builder` for `analysis-agent`, `task-agent`, and `review-agent`. It is never the primary Professional review owner. A `review-agent` must load it as a modifier when the selected review Professional evaluates iOS or iPadOS behavior. Add decision-owning client/Swift Foundations.

## When To Use

- Use for a confirmed iOS/iPadOS target whose lifecycle, scene, background, entry, entitlement, data, extension, UI, compatibility, or package behavior changes.
- For a shared client, also load `cross-platform-client-extension` when shared/native ownership changes.

## Do Not Use

- Do not use for Web/PWA, backend, infrastructure, non-iOS/iPadOS, Swift-only, or framework-only work without a confirmed target.
- Do not use for store rollout, signing authorization, release approval, or full watchOS, tvOS, or visionOS coverage.

## Required Inputs

- Record OS/SDK/deployment, device matrix, framework and lifecycle owners, entry/background contracts, capabilities/entitlements, data/extensions, artifact/channel, and app/API combinations.
- Record accessibility, signing/provisioning source without secrets, and unavailable device/store evidence.

## Professional Decision Rules

- Assign app and scene lifecycle, restoration identity, and multi-scene effects before changing shared state.
- Select background execution from work, expiration, cancellation, retry, and current OS limits.
- Reject exact background-execution timing promises.
- Validate URL schemes, Universal Links, notification payloads, and restored activities as untrusted external entry.
- Bind each capability and entitlement to its target, App ID, extension, provisioning, and least-privilege need.
- Bind Keychain, Data Protection, app-group, and extension data to account, protection class, migration, invalidation, and recovery behavior.
- Preserve UIKit/SwiftUI ownership and prove iPhone, iPad, VoiceOver, and Dynamic Type effects.
- Require app/API evidence for every claimed mixed installed-client version.
- Reject backend-compatibility inference from App Store or TestFlight mechanics.
- Keep archive, deployment, signing, provisioning, TestFlight, and App Store evidence distinct.
- Route release and signing authorization to `delivery-release-gate`.
- Track watchOS, tvOS, and visionOS separately; iOS or iPadOS evidence proves none of them.

## High-Value Gotchas

- A second scene can reuse the wrong account or duplicate an effect.
- A scheduled task can expire, launch late, or never receive enough runtime for an exact-timing promise.
- Shared data can outlive its entitlement, key, or account binding.
- A simulator or TestFlight pass can hide iPad layout, extension, deployment-target, signing, or mixed-version defects.

## Execution Checklist

- Load only the active decision family's Reference and preserve the Professional owner's acceptance.
- Exercise revoked capability, external entry, scene recreation, background expiration, upgrade, mixed-version, form-factor, and accessibility paths.
- Report artifact/device scope, source freshness, untested paths, authorization owner, and non-inferences.

## Stop / Escalation Conditions

- Stop on unknown target, SDK/deployment, form factor, scene owner, entry authority, entitlement, recovery, extension, artifact/signing identity, API contract, or device evidence.
- Resolve an unknown target from repository, build, and release facts before selecting iOS/iPadOS; route rollout, signing authorization, and release approval to `delivery-release-gate`.

## Output Contract

Return the decision, rejected alternative, owner, OS/SDK/deployment and device scope, normal/failure behavior, app/API evidence, and artifact validation. Include source freshness, proof limits, authorization owner, and risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [lifecycle scenes and background contracts](references/lifecycle-scenes-and-background-contracts.md) | targeted | app or scene lifecycle multiple-scene restoration BackgroundTasks or background expiration affects the decision | no iOS/iPadOS lifecycle scene restoration or background-execution behavior can change | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [entry capabilities and entitlements contracts](references/entry-capabilities-and-entitlements-contracts.md) | targeted | URL scheme Universal Link push capability entitlement App ID or provisioning behavior affects the decision | no external entry capability entitlement identity or provisioning behavior changes | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, validation-plan |
| [data keychain and extension contracts](references/data-keychain-and-extension-contracts.md) | targeted | Keychain Data Protection app group shared container or app-extension data behavior affects the decision | no local secret protected file shared-container or extension boundary changes | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [ui form factor and accessibility contracts](references/ui-form-factor-and-accessibility-contracts.md) | targeted | UIKit SwiftUI iPhone iPad VoiceOver Dynamic Type or adaptive-interface behavior affects the decision | no Apple mobile UI framework form-factor or accessibility delta changes | analysis-agent, task-agent, review-agent | selected-approach, proof-limit, validation-plan |
| [compatibility signing and distribution contracts](references/compatibility-signing-and-distribution-contracts.md) | targeted | deployment compatibility app/API versions archive signing provisioning TestFlight or App Store proof affects the decision | no supported version artifact identity signing distribution or mixed-version evidence changes | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [special platform boundaries](references/special-platform-boundaries.md) | targeted | watchOS tvOS or visionOS is an explicit target or requested coverage claim adjacent to iOS/iPadOS | the confirmed scope is only iOS/iPadOS with no special-platform claim | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, validation-plan |
