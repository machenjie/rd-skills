---
name: linux-desktop-platform-extension
description: Use when a confirmed Linux graphical desktop target changes platform behavior.
---

# linux-desktop-platform-extension

## Role

This focused Layer 3 Domain Skill supports `analysis-agent`, `task-agent`, and
`review-agent` for a confirmed Linux graphical desktop target. The selected
Professional remains owner; server/system routing stays outside this root.

## When To Use

- Confirmed display/session, D-Bus/portal, desktop identity/keyring, package,
  environment/input/localization, or accessibility behavior changes.

## Do Not Use

- Linux server, daemon, service, kernel, container-host, headless runtime, Web,
  backend, infrastructure, or toolkit/language-only work without a desktop target;
  release or rollout authorization.

## Required Inputs

- Distribution/desktop/session/toolkit, package/sandbox/identity, active decision
  family, accepted owner carrier, artifact/environment evidence, and proof limits.

## Professional Decision Rules

- Analysis loads only active decision-family References.
- Task and Review load paired evidence companions through the accepted carrier.
- `server-and-system-boundaries` may establish the owner boundary.
- Its evidence companion validates an accepted owner and never reroutes.
- Preserve simultaneous families.

## High-Value Gotchas

- One compositor, toolkit, package, or desktop session proves no other combination.

## Execution Checklist

1. Confirm graphical target, owner boundary, and active families.
2. Load only the role-valid decision or evidence Reference set.
3. Record environment/package validation, non-inferences, and proof limits.

## Stop / Escalation Conditions

- Stop on unresolved target, owner, session/toolkit/package boundary, accepted
  decision, carrier, or required artifact/environment evidence.

## Output Contract

- Linux desktop owner and scoped decision/evidence, environment/package behavior,
  validation, source freshness, non-inferences, proof limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [display session and toolkit contracts](references/display-session-and-toolkit-contracts.md) | targeted | X11 Wayland Xwayland compositor window focus coordinate clipboard input or toolkit behavior affects the decision | no Linux display-session compositor window input or toolkit behavior changes | analysis-agent | boundary-decision |
| [display session and toolkit contracts implementation and review evidence](references/display-session-and-toolkit-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Linux display-session and toolkit boundary requires implementation or review evidence | no display-session or toolkit implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [dbus portal and session integration contracts](references/dbus-portal-and-session-integration-contracts.md) | targeted | D-Bus name object interface desktop portal consent request or graphical-session integration affects the decision | no Linux D-Bus portal consent or session integration changes | analysis-agent | decision-record |
| [dbus portal and session integration contracts implementation and review evidence](references/dbus-portal-and-session-integration-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Linux D-Bus portal and session decision requires implementation or review evidence | no D-Bus portal or session implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [desktop entry mime and keyring contracts](references/desktop-entry-mime-and-keyring-contracts.md) | targeted | desktop entry application ID MIME association activation or keyring behavior affects the decision | no Linux launcher association identity activation or secret-store behavior changes | analysis-agent | boundary-decision |
| [desktop entry mime and keyring contracts implementation and review evidence](references/desktop-entry-mime-and-keyring-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Linux desktop identity MIME and keyring boundary requires implementation or review evidence | no desktop identity MIME or keyring implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [packaging installation and update contracts](references/packaging-installation-and-update-contracts.md) | targeted | Flatpak Snap AppImage deb rpm sandbox install update rollback or distribution evidence affects the decision | no Linux desktop package sandbox installation update or channel evidence changes | analysis-agent | selected-approach |
| [packaging installation and update contracts implementation and review evidence](references/packaging-installation-and-update-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Linux package approach requires implementation or review evidence | no Linux package implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [desktop environment input and localization contracts](references/desktop-environment-input-and-localization-contracts.md) | targeted | desktop environment IME locale font fractional scaling or toolkit behavior affects the decision | no Linux desktop input localization font scaling or environment-specific behavior changes | analysis-agent | decision-record |
| [desktop environment input and localization contracts implementation and review evidence](references/desktop-environment-input-and-localization-contracts-implementation-and-review-evidence.md) | evidence-pattern | the accepted Linux environment input and localization decision requires implementation or review evidence | no environment input or localization implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [accessibility platform deltas](references/accessibility-platform-deltas.md) | targeted | Linux desktop toolkit AT-SPI keyboard focus scaling or assistive-technology behavior changes | no Linux-desktop-specific accessibility behavior changes beyond Foundation rules | analysis-agent | decision-record |
| [accessibility platform deltas implementation and review evidence](references/accessibility-platform-deltas-implementation-and-review-evidence.md) | evidence-pattern | the accepted Linux accessibility delta requires implementation or review evidence | no Linux accessibility implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
| [server and system boundaries](references/server-and-system-boundaries.md) | targeted | Linux server daemon system service or host-runtime adjacency could misroute ownership | the task is confirmed graphical desktop work with no server system or service boundary | analysis-agent | routing-decision, boundary-decision |
| [server and system boundaries implementation and review evidence](references/server-and-system-boundaries-implementation-and-review-evidence.md) | evidence-pattern | the accepted Linux server or system owner boundary requires implementation or review evidence | no accepted server or system boundary implementation or review claim is being closed | task-agent, review-agent | evidence-record, proof-limit, validation-plan |
