---
name: macos-platform-extension
description: Use when an installed-client change has a confirmed macOS target and changes Apple desktop platform behavior.
---

# macos-platform-extension

## Role

This focused Layer 3 Domain Skill supports `analysis-agent`, `task-agent`, and
`review-agent` for a confirmed macOS installed application. The selected
Professional remains owner; this root never selects route or review owner.

## When To Use

- Confirmed framework/lifecycle, file/sandbox, keychain/helper, signing/artifact,
  architecture/update, or accessibility behavior changes.

## Do Not Use

- Web/PWA, backend, infrastructure, non-macOS, or language/framework-only work
  without a confirmed target; signing/notarization/release/rollout authorization.

## Required Inputs

- OS/SDK/deployment, framework/owner, active decision family, accepted carrier,
  identity/artifact/architecture/environment evidence, and proof limits.

## Professional Decision Rules

- Analysis loads only active decision-family References.
- Task and Review load paired evidence companions through the accepted carrier.
- Preserve Professional and Foundation ownership.
- Preserve all simultaneous families.
- Never reopen routing or infer updater, architecture, or distribution authority.

## High-Value Gotchas

- A signed main app proves neither nested code, architecture slices, helper
  identity, update recovery, nor installed behavior.

## Execution Checklist

1. Confirm target, owner, and active families from repository/artifact facts.
2. Load only the role-valid decision or evidence Reference set.
3. Record artifact/environment validation, non-inferences, and proof limits.

## Stop / Escalation Conditions

- Stop on an unresolved target, owner, boundary, accepted decision, or carrier.
- Stop when required artifact or hardware evidence is unavailable.
- Return release authorization to its owner.

## Output Contract

- macOS owner and scoped decision/evidence, normal and failure behavior,
  artifact/environment validation, source freshness, proof limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [framework lifecycle window and document contracts](references/framework-lifecycle-window-and-document-contracts.md) | targeted | AppKit SwiftUI Mac Catalyst app window document responder or restoration behavior affects the decision | no macOS framework lifecycle window document responder or restoration behavior can change | analysis-agent | selected-approach |
| [framework lifecycle window and document contracts implementation and review evidence](references/framework-lifecycle-window-and-document-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted framework lifecycle window and document approach requires implementation or review evidence | no framework lifecycle window or document implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [file sandbox and entitlement contracts](references/file-sandbox-and-entitlement-contracts.md) | targeted | file authorization security-scoped bookmark App Sandbox container or entitlement behavior affects the decision | no macOS file authority bookmark sandbox container or entitlement behavior changes | analysis-agent | boundary-decision |
| [file sandbox and entitlement contracts implementation and review evidence](references/file-sandbox-and-entitlement-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted file sandbox and entitlement boundary requires implementation or review evidence | no file sandbox or entitlement implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [keychain xpc and helper contracts](references/keychain-xpc-and-helper-contracts.md) | targeted | Keychain XPC helper agent daemon login item protocol identity or privilege behavior affects the decision | no macOS secret interprocess helper login persistence or privilege boundary changes | analysis-agent | decision-record |
| [keychain xpc and helper contracts implementation and review evidence](references/keychain-xpc-and-helper-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted keychain XPC and helper decision requires implementation or review evidence | no keychain XPC or helper implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [signing notarization and distribution contracts](references/signing-notarization-and-distribution-contracts.md) | targeted | hardened runtime nested signing Developer ID notarization Gatekeeper Mac App Store or independent distribution proof affects the decision | no macOS runtime protection signed artifact notarization or distribution-channel evidence changes | analysis-agent | decision-record |
| [signing notarization and distribution contracts implementation and review evidence](references/signing-notarization-and-distribution-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted signing notarization and distribution decision requires implementation or review evidence | no signing notarization or distribution implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [architecture and update contracts](references/architecture-and-update-contracts.md) | targeted | universal binary Apple Silicon Intel updater installer upgrade downgrade or mixed-version behavior affects the decision | no macOS architecture update installation or compatibility evidence changes | analysis-agent | boundary-decision |
| [architecture and update contracts implementation and review evidence](references/architecture-and-update-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted architecture and update boundary requires implementation or review evidence | no architecture or update implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [accessibility platform deltas](references/accessibility-platform-deltas.md) | targeted | AppKit SwiftUI or Mac Catalyst changes macOS keyboard focus VoiceOver menu window or custom-control accessibility | no macOS-specific accessibility behavior changes beyond reusable Foundation rules | analysis-agent | decision-record |
| [accessibility platform deltas implementation and review evidence](references/accessibility-platform-deltas-implementation-and-review-evidence.md) | evidence-pattern | the accepted macOS accessibility decision requires implementation or review evidence | no macOS accessibility implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
