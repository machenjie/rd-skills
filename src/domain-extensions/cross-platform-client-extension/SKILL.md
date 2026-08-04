---
name: cross-platform-client-extension
description: Use when an installed-client change has a confirmed shared framework and concrete registered platform targets.
---

# cross-platform-client-extension

## Role

This focused Layer 3 Domain Skill modifies `installed-client-change-builder` for `analysis-agent`, `task-agent`, and `review-agent`. It is never a standalone target or the primary Professional review owner. A `review-agent` must load it when the selected review Professional evaluates shared-client behavior. When task evidence confirms an affected concrete target, load its registered platform Domain.

## When To Use

- Use when repository, build, release, or published-artifact evidence confirms a shared installed client and its concrete platform targets.
- Use for shared/platform ownership, bridge or plugin compatibility, platform behavior differences, parity, or cross-platform regression decisions.

## Do Not Use

- Do not load from Flutter, React Native, Electron, Tauri, Qt, .NET MAUI, Kotlin Multiplatform, Compose Multiplatform, or another framework name alone.
- Do not use for an unknown target, language-only work, a native-only platform change without a shared client, Web/PWA, backend, infrastructure, or release authorization.

## Required Inputs

- Record the framework and version, target and release matrix, build variants, published artifacts, and OS/version range.
- Record shared and platform-specific owners, lifecycle and persistence behavior, bridge/FFI/plugin versions, parity claims, and per-target validation evidence.

## Professional Decision Rules

- Prove targets from repository, build targets, release configuration, or published artifacts without framework inference.
- If targets remain unknown after that inspection, do not load this modifier and ask one bounded target question.
- Keep confirmed targets in a cohesive executable slice when dependency order, shared/native ownership, write scope, validation, release, rollback, and integration risk stay cohesive.
- Use `analysis-agent` splitting when those boundaries create separately executable work.
- Assign shared, adapter, plugin, and native owners; keep platform lifecycle, persistence, permission, and packaging authority with the concrete platform Domain.
- Version bridge, FFI, plugin, and generated interfaces; define payload, threading, cancellation, error, and backward-compatibility behavior.
- Define behavior parity separately from UI parity.
- Treat uniform appearance as no proof of equivalent lifecycle, accessibility, permission, or failure behavior.
- Validate shared logic plus every affected target, native boundary, release artifact, and platform-specific negative path.
- Route signing, store/channel rollout, release approval, and rollback authority to `delivery-release-gate`.

## High-Value Gotchas

- A shared test can pass while one native adapter restores stale state or loses an error.
- A plugin can compile on every target while runtime capability, permission, or packaging support differs.
- An abstraction can hide platform-specific threading, lifecycle, navigation, accessibility, or security behavior.
- Pixel similarity can coexist with unequal keyboard, screen-reader, back, window, or failure behavior.

## Execution Checklist

- Load only the active decision family's Reference and every concrete platform Domain.
- Verify ownership, compatibility, normal, failure, upgrade, and artifact behavior per affected target.
- Report the target matrix, source freshness, untested targets, non-inferences, and residual risk.

## Stop / Escalation Conditions

- Stop on unresolved target, executable-slice boundary, owner, bridge contract, platform delta, artifact, or per-target evidence.
- Inspect repository/build/release/published artifacts first; then ask one bounded question if the concrete target set remains unresolved.

## Output Contract

Return the shared/platform ownership decision, concrete target matrix, rejected abstraction, compatibility boundary, parity definition, normal and failure behavior, and per-target validation. Include source freshness, proof limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [shared and target ownership contracts](references/shared-and-target-ownership-contracts.md) | targeted | shared adapter native lifecycle persistence permission or packaging ownership affects the decision | ownership is already accepted and no shared/platform boundary can change | analysis-agent, task-agent, review-agent | boundary-decision, decision-record, proof-limit |
| [bridge plugin and ffi contracts](references/bridge-plugin-and-ffi-contracts.md) | targeted | bridge FFI plugin generated binding serialization threading cancellation error or version behavior changes | no shared/native invocation or plugin compatibility boundary changes | analysis-agent, task-agent, review-agent | selected-approach, failure-decision, validation-plan |
| [parity and regression contracts](references/parity-and-regression-contracts.md) | targeted | behavior UI accessibility lifecycle failure or cross-target regression claims affect acceptance | the change has no cross-target parity or platform-specific regression claim | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [framework target evidence contracts](references/framework-target-evidence-contracts.md) | evidence-pattern | framework support build target release configuration or published artifacts determine the concrete platform set | concrete targets are already proven and framework support cannot alter scope | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
