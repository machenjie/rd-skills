---
name: windows-platform-extension
description: Use when a confirmed Windows target changes desktop or service platform behavior.
---

# windows-platform-extension

## Role

This focused Layer 3 Domain Skill modifies the selected Professional Skill for `analysis-agent`, `task-agent`, and `review-agent`. It is never the primary Professional review owner. A `review-agent` must load it for Windows behavior. Use `installed-client-change-builder` for desktop source changes; select the actual service Professional before adding this modifier for a Windows service.

## When To Use

- Use for a confirmed Windows target whose desktop framework, identity, deployment, integration, process, security, architecture, distribution, DPI, or accessibility behavior changes.
- For shared clients, also load `cross-platform-client-extension` when shared/native ownership changes.

## Do Not Use

- Do not use for Web/PWA, generic backend or infrastructure work without Windows application or service behavior, non-Windows, C#-only, PowerShell-only, or framework-only work without a confirmed Windows target.
- Do not route a Windows service to `installed-client-change-builder` solely because its platform is Windows.
- Do not use for release, signing, rollout authorization, or independent review ownership.

## Required Inputs

- Record target Windows/SDK range, Win32/WinUI/WPF/WinForms boundary, executable topology, package/app identity, packaged or unpackaged state, installer/update source, channel, and x86/x64/ARM64 claims.
- Record registration, activation, COM/IPC, privilege/container, secret, DLL, service/background/notification, DPI, accessibility, artifact, signing, and unavailable-host evidence.

## Professional Decision Rules

- Derive the framework, lifecycle, thread, activation, and single-instance owners from repository and final artifact facts.
- Bind MSIX or unpackaged identity to installation, update, repair, uninstall, registration, protocol, file-association, and COM behavior.
- Treat registry, activation, named-pipe, COM, and DLL-loading surfaces as explicit trust and compatibility boundaries.
- Bind UAC, AppContainer, DPAPI, Credential Manager, service identity, background tasks, and notifications to principal, session, package identity, denial, and recovery.
- For a Windows service, preserve the actual service Professional's acceptance and add Windows-specific service evidence only.
- Prove each x86/x64/ARM64 claim in the final executable and dependency graph.
- Keep reusable accessibility rules in Foundation; prove only Windows DPI, UI Automation, input, and assistive-technology deltas here.
- Route signing, Store/enterprise/direct-release approval, and rollout decisions to `delivery-release-gate`.

## High-Value Gotchas

- Debug can hide unpackaged activation, repair, dependency, and registration failures.
- A protocol, COM, named-pipe, or single-instance handoff can cross identity, integrity, session, or bitness boundaries.
- DPAPI scope, service accounts, interactive sessions, and DLL search paths can make local success non-portable.
- A signed main executable does not prove dependent binaries, architecture, installer, update, or distribution evidence.

## Execution Checklist

- Load only the active decision family's Reference and preserve Professional and Foundation ownership.
- Exercise denied elevation, missing identity, repair/update interruption, external activation, architecture, session, DPI, and accessibility paths.
- Report target, package identity, artifact/channel, source freshness, untested paths, authorization owner, and non-inferences.

## Stop / Escalation Conditions

- Stop on unknown target, framework, package/app identity, installer/update source, service owner, principal/session, trust boundary, architecture, channel, DPI/accessibility matrix, or artifact evidence.
- Resolve unknown targets from repository, build, and release facts; do not infer Windows from language or framework names.

## Output Contract

Return the Windows decision, rejected alternative, Professional owner, framework/OS/identity/architecture scope, normal and failure behavior, and artifact/host validation. Include source freshness, authorization owner, proof limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [framework lifecycle and activation contracts](references/framework-lifecycle-and-activation-contracts.md) | targeted | Win32 WinUI WPF WinForms lifecycle activation single-instance or UI-thread behavior affects the decision | no Windows desktop framework lifecycle activation instance or thread behavior changes | analysis-agent, task-agent, review-agent | selected-approach, proof-limit, validation-plan |
| [identity packaging and installation contracts](references/identity-packaging-and-installation-contracts.md) | targeted | packaged unpackaged MSIX package/app identity installer update repair or uninstall behavior affects the decision | no Windows identity deployment installation update repair or uninstall behavior changes | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, validation-plan |
| [os integration and registration contracts](references/os-integration-and-registration-contracts.md) | targeted | registry file association protocol handler or COM registration behavior affects the decision | no Windows registry association protocol or COM surface changes | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [service background and notification contracts](references/service-background-and-notification-contracts.md) | targeted | Windows service background task or app notification behavior affects the decision | no Windows service background execution or notification behavior changes | analysis-agent, task-agent, review-agent | routing-decision, failure-decision, validation-plan |
| [security ipc and loading contracts](references/security-ipc-and-loading-contracts.md) | targeted | UAC AppContainer DPAPI Credential Manager named pipe single-instance or DLL loading affects the decision | no Windows privilege container secret IPC instance or module-loading behavior changes | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, validation-plan |
| [architecture signing and distribution contracts](references/architecture-signing-and-distribution-contracts.md) | targeted | x86 x64 ARM64 signing Store enterprise or direct distribution evidence affects the decision | no Windows architecture signed-artifact or distribution-channel evidence changes | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [dpi and accessibility deltas](references/dpi-and-accessibility-deltas.md) | targeted | Windows scaling high-DPI UI Automation keyboard focus or assistive-technology behavior changes | no Windows-specific DPI accessibility input or focus behavior changes beyond Foundation rules | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
