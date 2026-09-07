---
name: ios-ipados-platform-extension
description: Use when an installed-client change has a confirmed iOS or iPadOS target and changes Apple mobile platform behavior.
---

# ios-ipados-platform-extension

## Role

This focused Layer 3 Domain Skill supports `analysis-agent`, `task-agent`, and
`review-agent` for a confirmed iOS/iPadOS target. The selected Professional
remains owner; this root never selects a new route or review owner.

## When To Use

- Confirmed Apple mobile lifecycle/background, entry/entitlement, data/keychain,
  UI/accessibility, compatibility/distribution, or special-platform behavior changes.

## Do Not Use

- Web/PWA, backend, infrastructure, non-iOS/iPadOS, or language/framework-only
  work without a confirmed target; signing, store, release, or rollout authorization.

## Required Inputs

- Target/device family, OS/SDK/deployment, app/scene owner, active decision family,
  accepted carrier, identity/artifact/device evidence, and proof limits.

## Professional Decision Rules

- Analysis loads only active decision-family References.
- Task and Review load paired evidence companions through the accepted carrier.
- Preserve Professional and Foundation ownership.
- Preserve all simultaneous families.
- Never reopen routing or infer watchOS, tvOS, or visionOS coverage.

## High-Value Gotchas

- Simulator, debug, or one device proves neither archive identity nor lifecycle,
  extension, accessibility, background, or mixed-version behavior broadly.

## Execution Checklist

1. Confirm target and active families from repository and artifact facts.
2. Load only the role-valid decision or evidence Reference set.
3. Record artifact/device validation, non-inferences, and proof limits.

## Stop / Escalation Conditions

- Stop on an unresolved target, owner, boundary, accepted decision, or carrier.
- Stop when required archive or device evidence is unavailable.
- Return release authorization to its owner.

## Output Contract

- iOS/iPadOS owner and scoped decision/evidence, normal and failure behavior,
  artifact/device validation, source freshness, proof limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [lifecycle scenes and background contracts](references/lifecycle-scenes-and-background-contracts.md) | targeted | app or scene lifecycle multiple-scene restoration BackgroundTasks or background expiration affects the decision | no iOS/iPadOS lifecycle scene restoration or background-execution behavior can change | analysis-agent | decision-record |
| [lifecycle scenes and background contracts implementation and review evidence](references/lifecycle-scenes-and-background-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted lifecycle and background decision requires implementation or review evidence | no lifecycle or background implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [entry capabilities and entitlements contracts](references/entry-capabilities-and-entitlements-contracts.md) | targeted | URL scheme Universal Link push capability entitlement App ID or provisioning behavior affects the decision | no external entry capability entitlement identity or provisioning behavior changes | analysis-agent | boundary-decision |
| [entry capabilities and entitlements contracts implementation and review evidence](references/entry-capabilities-and-entitlements-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted entry and entitlement boundary requires implementation or review evidence | no entry capability or entitlement implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [data keychain and extension contracts](references/data-keychain-and-extension-contracts.md) | targeted | Keychain Data Protection app group shared container or app-extension data behavior affects the decision | no local secret protected file shared-container or extension boundary changes | analysis-agent | decision-record |
| [data keychain and extension contracts implementation and review evidence](references/data-keychain-and-extension-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted data key and extension decision requires implementation or review evidence | no data key or extension implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [ui form factor and accessibility contracts](references/ui-form-factor-and-accessibility-contracts.md) | targeted | UIKit SwiftUI iPhone iPad VoiceOver Dynamic Type or adaptive-interface behavior affects the decision | no Apple mobile UI framework form-factor or accessibility delta changes | analysis-agent | selected-approach |
| [ui form factor and accessibility contracts implementation and review evidence](references/ui-form-factor-and-accessibility-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted UI form-factor and accessibility approach requires implementation or review evidence | no UI form-factor or accessibility implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [compatibility signing and distribution contracts](references/compatibility-signing-and-distribution-contracts.md) | targeted | deployment compatibility app/API versions archive signing provisioning TestFlight or App Store proof affects the decision | no supported version artifact identity signing distribution or mixed-version evidence changes | analysis-agent | decision-record |
| [compatibility signing and distribution contracts implementation and review evidence](references/compatibility-signing-and-distribution-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted compatibility artifact and channel decision requires implementation or review evidence | no compatibility signing or distribution implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [special platform boundaries](references/special-platform-boundaries.md) | targeted | watchOS tvOS or visionOS is an explicit target or requested coverage claim adjacent to iOS/iPadOS | the confirmed scope is only iOS/iPadOS with no special-platform claim | analysis-agent | boundary-decision |
| [special platform boundaries implementation and review evidence](references/special-platform-boundaries-implementation-and-review-evidence.md) | evidence-pattern | the accepted special-platform boundary requires implementation or review evidence | no watchOS tvOS or visionOS implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
