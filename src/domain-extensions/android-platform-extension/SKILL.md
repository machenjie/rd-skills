---
name: android-platform-extension
description: Use when an installed-client change has a confirmed Android target and changes Android platform behavior.
---

# android-platform-extension

## Role

This focused Layer 3 Domain Skill modifies `installed-client-change-builder` for `analysis-agent`, `task-agent`, and `review-agent`. It is never the primary Professional review owner. A `review-agent` must load it as a modifier when the selected review Professional evaluates Android behavior. Add decision-owning client/Kotlin Foundations.

## When To Use

- Use for a confirmed Android target whose lifecycle, component, permission, background, storage, accessibility, package, or device behavior changes.
- For a shared client, also load `cross-platform-client-extension` when shared/native ownership changes.

## Do Not Use

- Do not use for Web/PWA, backend, infrastructure, non-Android, Kotlin-only, or framework-only work without a confirmed Android target.
- Do not use for store rollout, signing authorization, or release/rollback approval.

## Required Inputs

- Record form factor, API/SDK range, variant, package identity, framework, and lifecycle or component owner.
- Record manifest exposure, permissions, background/notification guarantees, storage/key/backup behavior, artifact/signing source, device matrix, ANR evidence, and startup baseline.
- Record changed Views or Compose representation, input paths, scaling range, and required Android accessibility evidence.

## Professional Decision Rules

- Distinguish configuration recreation, process death, task removal, and user back; assign each state to transient, restorable, or durable ownership.
- Treat an Intent as an external entry boundary only when its input is externally supplied or untrusted, including input delivered through a deep link or exported component. Prove safe handling of that boundary by validating the payload, caller or source identity, authorization, and task behavior as applicable.
- Model runtime permissions and notification access as revocable state, including denial, later revocation, and recovery.
- Choose foreground service, persistent work, or no background execution from urgency, user visibility, persistence, and current platform limits.
- Bind local data and Android Keystore use to account scope, backup, migration, invalidation, logout, and recovery behavior.
- Derive compatibility and final APK/AAB proof from repository SDKs, manifest, variant, package identity, signing inputs, and current Play requirements.
- Set ANR and startup acceptance from current baselines, then exercise affected lifecycle and failure paths across the supported device matrix.
- Preserve Android representation, action, focus, input-alternative, and scaling behavior; reuse `accessibility-inclusive-design` for shared inclusive-interaction rules.
- Keep separate coverage and proof limits for Android TV, Wear OS, and Android Automotive; handheld evidence proves none of them.

## High-Value Gotchas

- A configuration-change test can pass while process-death restoration loses state or repeats an effect.
- An exported deep-link entry can select the wrong task, navigation destination, or signed-in account.
- Persistent work can be lost when a foreground-service assumption, notification state, or exact-timing promise is invalid.
- Backup can restore ciphertext without a usable key, and a debug APK can hide release AAB, signing, or Play delivery defects.
- A Compose or Views test can pass while merged semantics, focus traversal, or scaled layout is unusable with an Android accessibility service.

## Execution Checklist

- Load only the active decision family's Reference and preserve the Professional owner's acceptance.
- Verify reachable denied, recreated, killed, external-entry, upgrade, and device-specific paths.
- Report artifact, device, API/SDK, source freshness, untested paths, and non-inferences.

## Stop / Escalation Conditions

- Stop on unknown target, form factor, SDK/variant, package/signing identity, exported surface, permission, state owner, accessibility representation, data/key recovery, or required device evidence.
- Resolve an unknown target from repository, build, and release facts before selecting Android; route authorization and rollout decisions to `delivery-release-gate`.

## Output Contract

Return the Android decision, rejected alternative, platform owner, API/SDK and form-factor scope, normal and failure behavior, accessibility delta, and artifact/device validation. Include source freshness, proof limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [lifecycle task and state contracts](references/lifecycle-task-and-state-contracts.md) | targeted | Activity process task back-stack configuration-change or saved-state behavior affects the decision | the change cannot alter Android lifecycle task navigation restoration or state ownership | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [components permissions and background contracts](references/components-permissions-and-background-contracts.md) | targeted | Intent deep-link exported-component permission foreground-service persistent-work or notification behavior affects the decision | the change has no Android entry authority permission background execution or notification effect | analysis-agent, task-agent, review-agent | boundary-decision, failure-decision, validation-plan |
| [storage and keystore contracts](references/storage-and-keystore-contracts.md) | targeted | local storage backup account scope encryption or Android Keystore behavior affects the decision | no Android-local data key backup migration logout or recovery behavior can change | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [compatibility packaging and performance contracts](references/compatibility-packaging-and-performance-contracts.md) | targeted | API compatibility APK AAB signing Play packaging ANR startup or device-matrix proof affects the decision | no Android version artifact package signing performance or supported-device evidence changes | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [jetpack compose contracts](references/jetpack-compose-contracts.md) | targeted | Jetpack Compose state navigation lifecycle side-effect or rendering behavior affects the Android decision | the UI uses Views only or Kotlin syntax changes without Android Compose behavior | analysis-agent, task-agent, review-agent | selected-approach, proof-limit, validation-plan |
| [accessibility representation input and scaling](references/accessibility-representation-input-and-scaling.md) | targeted | Android Views or Compose semantics TalkBack Switch Access Voice Access keyboard D-pad accessibility focus alternatives font or display scaling or Android accessibility evidence affects the decision | no Android behavior changes or only Android accessibility API names are mentioned | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [special form factor boundaries](references/special-form-factor-boundaries.md) | targeted | Android TV Wear OS or Android Automotive is an explicit supported target or requested coverage claim | the confirmed target is handheld or tablet Android with no special-form-factor claim | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, validation-plan |
