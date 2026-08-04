---
name: linux-desktop-platform-extension
description: Use when a confirmed Linux graphical desktop target changes platform behavior.
---

# linux-desktop-platform-extension

## Role

This focused Layer 3 Domain Skill modifies `installed-client-change-builder` for `analysis-agent`, `task-agent`, and `review-agent`. It is never the primary Professional review owner. A `review-agent` must load it for Linux desktop behavior. Keep Linux server, service, daemon, kernel, and host-runtime ownership with the actual Professional and `linux-systems-professional-usage`.

## When To Use

- Use for a confirmed Linux graphical desktop target whose display session, desktop integration, D-Bus/portal, package, input, locale, scaling, or accessibility behavior changes.
- For shared clients, also load `cross-platform-client-extension` when shared/native ownership changes.

## Do Not Use

- Do not use for Linux server/service/runtime, Web/PWA, backend, infrastructure, non-Linux, language-only, or framework-only work without a confirmed Linux desktop target.
- Do not use for distribution/update approval, rollout authorization, or independent review ownership.

## Required Inputs

- Record distribution/version, desktop environment, compositor/session, X11/Wayland/Xwayland state, toolkit/version, graphical session owner, application ID, desktop/MIME/D-Bus names, portal/keyring use, package format/channel, and sandbox.
- Record Flatpak/Snap/AppImage/deb/rpm install/update owner, locale/input method/font/scaling/accessibility matrix, artifact, and unavailable environment evidence.

## Professional Decision Rules

- Base decisions on the inspected target compositor, desktop, session, toolkit, and packaging instead of generalized Linux desktop behavior.
- Separate X11, Wayland, and Xwayland authority, coordinates, focus, input, clipboard, activation, and window-management evidence.
- Bind D-Bus names/objects and portal requests to caller, session, consent, lifecycle, cancellation, and version.
- Bind desktop entries, MIME handlers, application IDs, keyring collections, sandbox identity, and user choice to installation and removal.
- Separate Flatpak, Snap, AppImage, deb, and rpm confinement, dependency, install, update, rollback, and distribution behavior.
- Do not infer fractional scaling, IME, locale, font, keyring, accessibility, or toolkit behavior across desktops or sessions.
- Keep reusable accessibility rules in Foundation and release/update authorization in `delivery-release-gate`.

## High-Value Gotchas

- X11 success can hide Wayland portal, activation, coordinate, clipboard, or input failures.
- A valid desktop file can disagree with package identity, D-Bus name, MIME registration, sandbox, or installed path.
- Keyring availability and unlock policy can change across desktops, sessions, headless launch, and test hosts.
- Flatpak, Snap, AppImage, deb, and rpm artifacts do not share confinement, dependency, update, or rollback semantics.

## Execution Checklist

- Load only the active decision family's Reference and preserve Professional and Foundation ownership.
- Exercise missing portal/keyring/session, denied consent, packaging transitions, desktop/session differences, input/locale/scaling, and accessibility paths.
- Report environment/package matrix, artifact/channel, source freshness, untested paths, authorization owner, and non-inferences.

## Stop / Escalation Conditions

- Stop on unknown target, distribution/version, desktop, compositor/session, toolkit, package/sandbox, identity, integration owner, update source, accessibility matrix, or artifact evidence.
- Resolve unknown targets from repository, build, and release facts; do not infer Linux desktop from language, toolkit, or “Unix” alone.

## Output Contract

Return the Linux desktop decision, rejected alternative, Professional owner, distribution/desktop/session/toolkit/package scope, normal and failure behavior, and artifact/environment validation. Include source freshness, non-inferences, proof limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [display session and toolkit contracts](references/display-session-and-toolkit-contracts.md) | targeted | X11 Wayland Xwayland compositor window focus coordinate clipboard input or toolkit behavior affects the decision | no Linux display-session compositor window input or toolkit behavior changes | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, validation-plan |
| [dbus portal and session integration contracts](references/dbus-portal-and-session-integration-contracts.md) | targeted | D-Bus name object interface desktop portal consent request or graphical-session integration affects the decision | no Linux D-Bus portal consent or session integration changes | analysis-agent, task-agent, review-agent | decision-record, failure-decision, validation-plan |
| [desktop entry mime and keyring contracts](references/desktop-entry-mime-and-keyring-contracts.md) | targeted | desktop entry application ID MIME association activation or keyring behavior affects the decision | no Linux launcher association identity activation or secret-store behavior changes | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, validation-plan |
| [packaging installation and update contracts](references/packaging-installation-and-update-contracts.md) | targeted | Flatpak Snap AppImage deb rpm sandbox install update rollback or distribution evidence affects the decision | no Linux desktop package sandbox installation update or channel evidence changes | analysis-agent, task-agent, review-agent | selected-approach, proof-limit, validation-plan |
| [desktop environment input and localization contracts](references/desktop-environment-input-and-localization-contracts.md) | targeted | desktop environment IME locale font fractional scaling or toolkit behavior affects the decision | no Linux desktop input localization font scaling or environment-specific behavior changes | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [accessibility platform deltas](references/accessibility-platform-deltas.md) | targeted | Linux desktop toolkit AT-SPI keyboard focus scaling or assistive-technology behavior changes | no Linux-desktop-specific accessibility behavior changes beyond Foundation rules | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [server and system boundaries](references/server-and-system-boundaries.md) | targeted | Linux server daemon system service or host-runtime adjacency could misroute ownership | the task is confirmed graphical desktop work with no server system or service boundary | analysis-agent, task-agent, review-agent | routing-decision, boundary-decision, proof-limit |
