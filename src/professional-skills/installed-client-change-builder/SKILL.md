---
name: installed-client-change-builder
description: "`task-agent`: installed-client implementation; skip browser/PWA, backend, infrastructure, planning, release, and review."
---

# installed-client-change-builder

## Role

Support `task-agent` inside the accepted installed-client boundary.

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

- Accepted behavior, owners, targets, repository-pinned versions, boundaries, and validation; source records accessed 2026-07-24.

## Professional Decision Rules

- Preserve the accepted scope and target behavior through the affected platform and framework boundaries.
- Inspect owner, consumers, tests, and target/package facts before the smallest complete change.
- Record target checks, unavailable evidence, proof limits, and residual risk.

## High-Value Gotchas

- Keep the selected installed client change builder decision within its declared owner, inputs, stops, and output contract.

## Execution Checklist

1. Apply the decision rules above in order.

## Stop / Escalation Conditions

- Stop on unresolved target, owner, client contract, artifact, or environment.
- Release approval and task routing are outside this Skill's authority.

## Output Contract

- Changed placement, framework/version, native owner/behavior, bridge/compatibility/migration decisions, target/package evidence, affected target behavior, proof limits, residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [native platform source contracts](references/native-platform-source-contracts.md) | targeted | Android iOS/iPadOS Windows macOS or Linux desktop lifecycle permission link OS integration or packaging behavior affects the change | Only shared framework behavior changes and native target contracts remain untouched | task-agent | boundary-decision, proof-limit, validation-plan |
| [flutter framework contracts](references/flutter-framework-contracts.md) | targeted | Flutter shared state platform-channel restoration link plugin or target packaging behavior affects the accepted change | No Flutter source channel plugin lifecycle link or packaging behavior changes | task-agent | proof-limit, selected-approach, validation-plan |
| [react native framework contracts](references/react-native-framework-contracts.md) | targeted | React Native JavaScript state native state process recreation link or platform seam affects the accepted change | No React Native state lifecycle link native seam or packaging behavior changes | task-agent | proof-limit, selected-approach, validation-plan |
| [electron framework contracts](references/electron-framework-contracts.md) | targeted | Electron main renderer operating-system privilege deep-link or packaged-artifact behavior affects the accepted change | No Electron process privilege deep-link operating-system or packaging behavior changes | task-agent | proof-limit, selected-approach, validation-plan |
| [tauri framework contracts](references/tauri-framework-contracts.md) | targeted | Tauri command plugin capability webview deep-link or bundle behavior affects the accepted change | No Tauri command capability plugin webview link or bundle behavior changes | task-agent | proof-limit, selected-approach, validation-plan |
| [qt framework contracts](references/qt-framework-contracts.md) | targeted | Qt window ownership window-manager runtime library plugin QML or package behavior affects the accepted change | No Qt window runtime plugin QML platform or packaging behavior changes | task-agent | proof-limit, selected-approach, validation-plan |
| [dotnet maui framework contracts](references/dotnet-maui-framework-contracts.md) | targeted | .NET MAUI window native lifecycle restoration permission workload or package target affects the accepted change | No .NET MAUI lifecycle restoration permission workload or package behavior changes | task-agent | proof-limit, selected-approach, validation-plan |
| [kotlin multiplatform framework contracts](references/kotlin-multiplatform-framework-contracts.md) | targeted | Kotlin Multiplatform source-set target support expected actual binary or host integration affects the accepted change | No Kotlin Multiplatform source-set target binary or host-integration behavior changes | task-agent | proof-limit, selected-approach, validation-plan |
