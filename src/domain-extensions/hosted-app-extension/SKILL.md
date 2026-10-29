---
name: hosted-app-extension
description: "For analysis/task/review agents: use for browser, IDE, or mini-program host contracts; skip ordinary Web/PWA and standalone applications."
---

# hosted-app-extension

## Role

Focused Layer 3 Domain Skill: `analysis-agent` resolves rules; `task-agent` implements; `review-agent` checks evidence.

Apply host lifecycle, capability, execution-context, and upgrade constraints to an extension or hosted application.

## When To Use

- Manifest, host permissions, message identity, background lifetime, or host API behavior affects a hosted application.
- Host versions, remote execution, upgrades, or revocation change available capabilities.

## Do Not Use

- The task is an ordinary webpage, PWA, or standalone application without an extension host contract.
- Only a framework label changes, with no confirmed host target.

## Required Inputs

- Host and minimum version, manifest, contribution points, execution contexts, and actual permissions.
- Message endpoints, persistent state, activation/recovery paths, upgrade format, and target-device evidence.

## Professional Decision Rules

- Bind each capability to its declared permission and actual runtime grant.
- Validate message sender, destination, context, and payload before privileged effects.
- Place state according to host lifetime rather than assuming a persistent background process.
- Treat installation, activation, update, unload, uninstall, and permission revocation as separate transitions.
- Preserve migration and recovery behavior across supported host versions.
- Verify each host independently; browser, IDE, and mini-program evidence is not interchangeable.

## High-Value Gotchas

- A trusted extension package can receive messages derived from an untrusted page or workspace.
- Development tools can keep a process alive or expose APIs unavailable on the target device.

## Execution Checklist

1. Identify the changed host capability and its actual execution context.
2. Exercise context shutdown, restart, revocation, and supported-version upgrades.
3. Validate the resulting behavior in the affected host and state any device gaps.

## Stop / Escalation Conditions

- Stop when the host target, execution context, permission grant, or migration authority cannot be established.
- Escalate a reachable message path that can invoke effects outside the granted host capability.

## Output Contract

- Return host/version scope, context and permission decisions, lifecycle recovery, per-host validation, and untested targets.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [browser extension lifecycle and messaging](references/browser-extension-lifecycle-and-messaging.md) | targeted | browser extension manifests, execution contexts, background recovery, or messaging | ordinary websites, PWAs, and changes without a browser extension target | analysis-agent, task-agent, review-agent | boundary-decision, validation-plan, proof-limit |
| [ide extension host and workspace](references/ide-extension-host-and-workspace.md) | targeted | IDE activation, workspace trust, remote execution, host processes, or extension upgrades | internal repository plugins without an IDE host lifecycle or capability contract | analysis-agent, task-agent, review-agent | boundary-decision, validation-plan, proof-limit |
| [mini program lifecycle and bridge](references/mini-program-lifecycle-and-bridge.md) | targeted | mini-program page lifetime, view/logic communication, login, permissions, or device behavior | browser-only applications and unconfirmed mini-program targets | analysis-agent, task-agent, review-agent | boundary-decision, validation-plan, proof-limit |
