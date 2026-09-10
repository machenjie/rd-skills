---
name: windows-platform-extension
description: Use when a confirmed Windows target changes desktop or service platform behavior.
---

# windows-platform-extension

## Role

This focused Layer 3 Domain Skill supports `analysis-agent`, `task-agent`, and
`review-agent` for a confirmed Windows application or service. The selected
Professional remains owner; service routing stays outside this root.

## When To Use

- Confirmed framework/lifecycle, identity/install, OS registration, service or
  background, security/IPC, architecture/distribution, DPI, or accessibility changes.

## Do Not Use

- Web/PWA, generic backend/infrastructure, non-Windows, or language/framework-only
  work without a Windows target; release, signing, or rollout authorization.

## Required Inputs

- Windows/SDK/framework, application or service owner, identity/architecture,
  active decision family, accepted carrier, artifact/host evidence, and proof limits.

## Professional Decision Rules

- Analysis loads only active decision-family References.
- Task and Review load paired evidence companions through the accepted carrier.
- `service-background-and-notification-contracts` may establish the owner boundary.
- Its evidence companion validates the accepted owner and never reroutes.
- Preserve co-triggered families.

## High-Value Gotchas

- Debug, one architecture, or the main executable proves no installed identity,
  dependent binary, service/session, DPI, or accessibility behavior.

## Execution Checklist

1. Confirm target, owner boundary, and active families.
2. Load only the role-valid decision or evidence Reference set.
3. Record artifact/host validation, non-inferences, and proof limits.

## Stop / Escalation Conditions

- Stop on unresolved target, owner, identity/service/trust boundary, accepted
  decision, carrier, or required artifact/host evidence.

## Output Contract

- Windows owner and scoped decision/evidence, normal and failure behavior,
  artifact/host validation, source freshness, proof limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [framework lifecycle and activation contracts](references/framework-lifecycle-and-activation-contracts.md) | targeted | Win32 WinUI WPF WinForms lifecycle activation single-instance or UI-thread behavior affects the decision | no Windows desktop framework lifecycle activation instance or thread behavior changes | analysis-agent | selected-approach |
| [framework lifecycle and activation contracts implementation and review evidence](references/framework-lifecycle-and-activation-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Windows framework and lifecycle approach requires implementation or review evidence | no framework lifecycle or activation implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [identity packaging and installation contracts](references/identity-packaging-and-installation-contracts.md) | targeted | packaged unpackaged MSIX package/app identity installer update repair or uninstall behavior affects the decision | no Windows identity deployment installation update repair or uninstall behavior changes | analysis-agent | boundary-decision |
| [identity packaging and installation contracts implementation and review evidence](references/identity-packaging-and-installation-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Windows identity and installation boundary requires implementation or review evidence | no Windows identity packaging or installation implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [os integration and registration contracts](references/os-integration-and-registration-contracts.md) | targeted | registry file association protocol handler or COM registration behavior affects the decision | no Windows registry association protocol or COM surface changes | analysis-agent | decision-record |
| [os integration and registration contracts implementation and review evidence](references/os-integration-and-registration-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Windows registration decision requires implementation or review evidence | no Windows registration implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [service background and notification contracts](references/service-background-and-notification-contracts.md) | targeted | Windows service background task or app notification behavior affects the decision | no Windows service background execution or notification behavior changes | analysis-agent | routing-decision, failure-decision |
| [service background and notification contracts implementation and review evidence](references/service-background-and-notification-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Windows service background and notification owner boundary requires implementation or review evidence | no accepted service background or notification implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [security ipc and loading contracts](references/security-ipc-and-loading-contracts.md) | targeted | UAC AppContainer DPAPI Credential Manager named pipe single-instance or DLL loading affects the decision | no Windows privilege container secret IPC instance or module-loading behavior changes | analysis-agent | boundary-decision |
| [security ipc and loading contracts implementation and review evidence](references/security-ipc-and-loading-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Windows security IPC and loading boundary requires implementation or review evidence | no Windows security IPC or loading implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [architecture signing and distribution contracts](references/architecture-signing-and-distribution-contracts.md) | targeted | x86 x64 ARM64 signing Store enterprise or direct distribution evidence affects the decision | no Windows architecture signed-artifact or distribution-channel evidence changes | analysis-agent | decision-record |
| [architecture signing and distribution contracts implementation and review evidence](references/architecture-signing-and-distribution-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Windows architecture and distribution decision requires implementation or review evidence | no Windows architecture signing or distribution implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [dpi and accessibility deltas](references/dpi-and-accessibility-deltas.md) | targeted | Windows scaling high-DPI UI Automation keyboard focus or assistive-technology behavior changes | no Windows-specific DPI accessibility input or focus behavior changes beyond Foundation rules | analysis-agent | decision-record |
| [dpi and accessibility deltas implementation and review evidence](references/dpi-and-accessibility-deltas-implementation-and-review-evidence.md) | evidence-pattern | the accepted Windows DPI and accessibility delta requires implementation or review evidence | no Windows DPI or accessibility implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
