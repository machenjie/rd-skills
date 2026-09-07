---
name: cross-platform-client-extension
description: Use for a source-confirmed shared installed client and concrete targets; skip framework-name-only, native-only, Web, backend, and release work.
---

# cross-platform-client-extension

## Role

This focused Layer 3 Domain Skill modifies installed-client decisions for `analysis-agent`, `task-agent`, and `review-agent`; never standalone or primary. Main selects it and any needed platform Domains for confirmed targets; Task and Review consume that assignment.

## When To Use

- Use with a source-confirmed shared installed client and concrete platform targets.
- Use for ownership, bridge/plugin, platform delta, parity, or cross-target regression.

## Do Not Use

- Do not load from a framework name alone.
- Exclude unknown-target, language-only, native-only, Web/PWA, backend, infrastructure, and release-authority work.

## Required Inputs

- Framework/version, target matrix, variants/artifacts, shared/platform owners, bridge versions, parity claims, and per-target evidence.

## Professional Decision Rules

- Unknown targets after source inspection prohibit loading and require one bounded target question.
- Load only active ownership, bridge, parity, or target-evidence References and capsule-named platform Domains within Main's zero-to-three Layer 3 assignment.
- Return newly confirmed target needs to Main for selection.
- Keep cohesive targets together. Use Analysis when an unresolved ownership, dependency, validation, or integration decision could change execution or its split.
- Return signing, rollout, release, and rollback authority to `delivery-release-gate`.

## High-Value Gotchas

- Shared or compile-time success does not close target-specific runtime behavior; load the target evidence before closure.

## Execution Checklist

1. Confirm the concrete target matrix and current owners.
2. Load only active shared-client References and target Domains already named in the assignment.
3. Close with per-target evidence, non-inferences, and proof limits.

## Stop / Escalation Conditions

Stop on unresolved target, owner, bridge, platform delta, artifact, or per-target evidence; inspect source before one bounded question.

## Output Contract

Return ownership, target matrix, compatibility, parity, normal/failure behavior, per-target validation, freshness, proof limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [shared and target ownership contracts](references/shared-and-target-ownership-contracts.md) | targeted | shared adapter native lifecycle persistence permission or packaging ownership affects the decision | ownership is already accepted and no shared/platform boundary can change | analysis-agent, task-agent, review-agent | boundary-decision, decision-record, proof-limit |
| [bridge plugin and ffi contracts](references/bridge-plugin-and-ffi-contracts.md) | targeted | bridge FFI plugin generated binding serialization threading cancellation error or version behavior changes | no shared/native invocation or plugin compatibility boundary changes | analysis-agent, task-agent, review-agent | selected-approach, failure-decision, validation-plan |
| [parity and regression contracts](references/parity-and-regression-contracts.md) | targeted | behavior UI accessibility lifecycle failure or cross-target regression claims affect acceptance | the change has no cross-target parity or platform-specific regression claim | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [framework target evidence contracts](references/framework-target-evidence-contracts.md) | evidence-pattern | framework support build target release configuration or published artifacts determine the concrete platform set | concrete targets are already proven and framework support cannot alter scope | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
