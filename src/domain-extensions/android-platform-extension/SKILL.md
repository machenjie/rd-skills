---
name: android-platform-extension
description: Use when an installed-client change has a confirmed Android target and changes Android platform behavior.
---

# android-platform-extension

## Role

This focused Layer 3 Domain Skill supports `analysis-agent`, `task-agent`, and
`review-agent` for a confirmed Android target. The selected Professional remains
owner; this root never selects a new route or review owner.

## When To Use

- Confirmed Android lifecycle, component/permission/background, storage/key,
  Compose, accessibility, compatibility/package, or form-factor behavior changes.

## Do Not Use

- Web/PWA, backend, infrastructure, non-Android, or language/framework-only work
  without a confirmed Android target; release or rollout authorization.

## Required Inputs

- Target/form factor, API/SDK/variant, package and source owner, active decision
  family, accepted decision carrier, artifact/device evidence, and proof limits.

## Professional Decision Rules

- Analysis loads only active decision-family References.
- Task and Review load paired evidence companions through the accepted carrier.
- Preserve Professional and Foundation ownership.
- Preserve all simultaneously active families.
- Never reopen routing or infer one form factor from another.

## High-Value Gotchas

- A debug or single-device result does not prove release artifact, process-death,
  permission-revocation, accessibility, or special-form-factor behavior.

## Execution Checklist

1. Confirm the target and active families from repository facts.
2. Load only the role-valid decision or evidence Reference set.
3. Record current artifact/device validation, non-inferences, and proof limits.

## Stop / Escalation Conditions

- Stop on an unresolved target, owner, boundary, accepted decision, or carrier.
- Stop when required artifact or device evidence is unavailable.
- Return release authorization to its owner.

## Output Contract

- Android owner and scoped decision/evidence, normal and failure behavior,
  artifact/device validation, source freshness, proof limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [lifecycle task and state contracts](references/lifecycle-task-and-state-contracts.md) | targeted | Activity process task back-stack configuration-change or saved-state behavior affects the decision | the change cannot alter Android lifecycle task navigation restoration or state ownership | analysis-agent | decision-record |
| [lifecycle task and state contracts implementation and review evidence](references/lifecycle-task-and-state-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Android lifecycle task and state decision requires implementation or review evidence | no lifecycle task or state implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [components permissions and background contracts](references/components-permissions-and-background-contracts.md) | targeted | Intent deep-link exported-component permission foreground-service persistent-work or notification behavior affects the decision | the change has no Android entry authority permission background execution or notification effect | analysis-agent | boundary-decision |
| [storage and keystore contracts](references/storage-and-keystore-contracts.md) | targeted | local storage backup account scope encryption or Android Keystore behavior affects the decision | no Android-local data key backup migration logout or recovery behavior can change | analysis-agent | decision-record |
| [storage and keystore contracts implementation and review evidence](references/storage-and-keystore-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Android storage and key decision requires implementation or review evidence | no storage or key implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [compatibility packaging and performance contracts](references/compatibility-packaging-and-performance-contracts.md) | targeted | API compatibility APK AAB signing Play packaging ANR startup or device-matrix proof affects the decision | no Android version artifact package signing performance or supported-device evidence changes | analysis-agent | decision-record |
| [compatibility packaging and performance contracts implementation and review evidence](references/compatibility-packaging-and-performance-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Android compatibility artifact and performance decision requires implementation or review evidence | no compatibility packaging or performance implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [jetpack compose contracts](references/jetpack-compose-contracts.md) | targeted | Jetpack Compose state navigation lifecycle side-effect or rendering behavior affects the Android decision | the UI uses Views only or Kotlin syntax changes without Android Compose behavior | analysis-agent | selected-approach |
| [jetpack compose contracts implementation and review evidence](references/jetpack-compose-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Jetpack Compose approach requires implementation or review evidence | no Compose implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [accessibility representation input and scaling](references/accessibility-representation-input-and-scaling.md) | targeted | Android Views or Compose semantics TalkBack Switch Access Voice Access keyboard D-pad accessibility focus alternatives font or display scaling or Android accessibility evidence affects the decision | no Android behavior changes or only Android accessibility API names are mentioned | analysis-agent | decision-record |
| [accessibility representation input and scaling implementation and review evidence](references/accessibility-representation-input-and-scaling-implementation-and-review-evidence.md) | evidence-pattern | the accepted Android accessibility decision requires implementation or review evidence | no Android accessibility implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [special form factor boundaries](references/special-form-factor-boundaries.md) | targeted | Android TV Wear OS or Android Automotive is an explicit supported target or requested coverage claim | the confirmed target is handheld or tablet Android with no special-form-factor claim | analysis-agent | boundary-decision |
| [special form factor boundaries implementation and review evidence](references/special-form-factor-boundaries-implementation-and-review-evidence.md) | evidence-pattern | the accepted Android special form-factor boundary requires implementation or review evidence | no special form-factor implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [components permissions and background contracts implementation and review evidence](references/components-permissions-and-background-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Android component permission and background boundary requires implementation or review evidence | no component permission or background implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
