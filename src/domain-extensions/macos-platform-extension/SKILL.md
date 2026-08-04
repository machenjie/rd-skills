---
name: macos-platform-extension
description: Use when an installed-client change has a confirmed macOS target and changes Apple desktop platform behavior.
---

# macos-platform-extension

## Role

This focused Layer 3 Domain Skill modifies `installed-client-change-builder` for `analysis-agent`, `task-agent`, and `review-agent`. It is never the primary Professional review owner. A `review-agent` must load it as a modifier when the selected review Professional evaluates macOS behavior. Add decision-owning client/Swift Foundations.

## When To Use

- Use for a confirmed macOS target whose framework, lifecycle, file authority, sandbox, helper, architecture, accessibility, package, or update behavior changes.
- For a shared client, also load `cross-platform-client-extension` when shared/native ownership changes.

## Do Not Use

- Do not use for Web/PWA, backend, infrastructure, non-macOS, Swift-only, or framework-only work without a confirmed macOS target.
- Do not use for release, signing, notarization, store-rollout authorization, or independent review ownership.

## Required Inputs

- Record OS/SDK/deployment, AppKit/SwiftUI/Catalyst boundary, lifecycle/responder owners, file/sandbox authority, Keychain/helper topology, artifact/channel, and architectures.
- Record updater/installer authority, app/API combinations, accessibility, signing/notarization source without secrets, and unavailable hardware/distribution evidence.

## Professional Decision Rules

- Assign app, window, document, responder, restoration, and termination ownership before changing shared state.
- Choose AppKit, SwiftUI, Mac Catalyst, or an explicit bridge from target APIs and lifecycle needs; framework names alone prove no macOS behavior.
- Treat user-selected files, security-scoped bookmarks, sandbox containers, and entitlements as explicit revocable authorization.
- Bind Keychain, XPC, helpers, agents, and login items to identity, protocol, privilege, installation, and recovery.
- Bind hardened runtime, nested-code signing, Developer ID, notarization, Gatekeeper, Mac App Store, or independent distribution proof to the selected artifact and channel.
- Prove every claimed Apple Silicon/Intel slice in the final dependency graph.
- Require a repository-declared updater/installer owner and official source for its mechanism.
- Stop or mark independent update behavior unproven when that authority is absent.
- Require client and API evidence for each claimed mixed app/API combination.
- Reject backend-compatibility inference from packaging, notarization, or store mechanics.
- Keep reusable accessibility rules in Foundation and prove only AppKit/SwiftUI/Catalyst-specific deltas here.

## High-Value Gotchas

- A closing document can leave saves, responder actions, or restoration targeting obsolete state.
- A security-scoped bookmark can be stale, overbroad, or unbalanced.
- A signed main app can contain invalid helpers, services, plug-ins, or slices.
- Developer-managed distribution does not prove an updater exists, is authorized, or supports safe downgrade and recovery.

## Execution Checklist

- Load only the active decision family's Reference and preserve the Professional owner's acceptance.
- Exercise denied file access, restoration, helper failure, architecture, upgrade, mixed-version, Gatekeeper, and accessibility paths.
- Report artifact/architecture scope, source freshness, untested paths, authorization owner, and non-inferences.

## Stop / Escalation Conditions

- Stop on unknown target, framework, SDK/deployment, lifecycle owner, file authority, entitlement, helper, artifact/channel, nested signing, architecture, updater source, API contract, or hardware evidence.
- Resolve an unknown target from repository, build, and release facts before selecting macOS; route signing/notarization/release/rollout authorization to `delivery-release-gate`.

## Output Contract

Return the decision, rejected alternative, owner, framework/OS/SDK/deployment scope, normal/failure behavior, architecture and app/API evidence, and artifact validation. Include updater state, source freshness, proof limits, authorization owner, and risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [framework lifecycle window and document contracts](references/framework-lifecycle-window-and-document-contracts.md) | targeted | AppKit SwiftUI Mac Catalyst app window document responder or restoration behavior affects the decision | no macOS framework lifecycle window document responder or restoration behavior can change | analysis-agent, task-agent, review-agent | selected-approach, proof-limit, validation-plan |
| [file sandbox and entitlement contracts](references/file-sandbox-and-entitlement-contracts.md) | targeted | file authorization security-scoped bookmark App Sandbox container or entitlement behavior affects the decision | no macOS file authority bookmark sandbox container or entitlement behavior changes | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, validation-plan |
| [keychain xpc and helper contracts](references/keychain-xpc-and-helper-contracts.md) | targeted | Keychain XPC helper agent daemon login item protocol identity or privilege behavior affects the decision | no macOS secret interprocess helper login persistence or privilege boundary changes | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [signing notarization and distribution contracts](references/signing-notarization-and-distribution-contracts.md) | targeted | hardened runtime nested signing Developer ID notarization Gatekeeper Mac App Store or independent distribution proof affects the decision | no macOS runtime protection signed artifact notarization or distribution-channel evidence changes | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [architecture and update contracts](references/architecture-and-update-contracts.md) | targeted | universal binary Apple Silicon Intel updater installer upgrade downgrade or mixed-version behavior affects the decision | no macOS architecture update installation or compatibility evidence changes | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, validation-plan |
| [accessibility platform deltas](references/accessibility-platform-deltas.md) | targeted | AppKit SwiftUI or Mac Catalyst changes macOS keyboard focus VoiceOver menu window or custom-control accessibility | no macOS-specific accessibility behavior changes beyond reusable Foundation rules | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
