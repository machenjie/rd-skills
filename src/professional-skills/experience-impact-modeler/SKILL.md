---
name: experience-impact-modeler
description: "Use `analysis-agent` to map user-flow, interaction-state, accessibility, content, and recovery impact when experience behavior changes. Skip backend-only work with no experience effect and question-only requests."
---

# experience-impact-modeler

## Role

Support `analysis-agent` in mapping affected journeys, interaction states,
accessibility behavior, and recovery expectations.

## When To Use

- user flow change
- interaction state change

## Do Not Use

- backend only with no experience impact
- question only

## Required Inputs

- intent slice
- existing flow evidence
- read scope

## Professional Decision Rules

- Map entry, action, system feedback, success, failure, recovery, and exit states for every affected user role.
- Include loading, empty, disabled, permission, offline, retry, focus, keyboard, responsive, and accessibility behavior when triggered.
- Preserve the user task and information hierarchy before optimizing component structure.
- Separate design choices requiring user input from behavior already established in source.

## High-Value Gotchas

- Happy-path mockups hide error, permission, focus, and responsive failures.
- Visual similarity does not prove semantic or accessibility equivalence.
- Async stale responses can overwrite newer user intent.

## Execution Checklist

1. Trace each affected actor from entry through success, failure, recovery, and exit.
2. Select the interaction states that materially change user action or system feedback.
3. Map accessibility, responsive, permission, and stale-response risks to observable checks.
4. Stop modeling when source cannot establish a consequential content or behavior choice.

## Stop / Escalation Conditions

- Stop implementation planning when actor, entry/exit path, state matrix, content decision, accessibility obligation, permission/denial path, or breakpoint behavior is implicit.
- Stop form or modal closure when focus destination, keyboard path, screen-reader announcement, validation timing, disabled state, and input preservation are missing.
- Stop analytics or experiment closure when exposure, assignment, event taxonomy, dashboard migration, guardrail, SRM check, or rollback owner is unknown.
- Stop destructive/sensitive-flow closure when consequence copy, confirmation, denial path, audit/receipt, recovery/undo, or server-side enforcement owner is absent.

## Output Contract

- flow evidence
- affected states
- experience constraints

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded review needs actor, entry, state, accessibility, analytics, and verification inventory | Full flow evidence, accessibility gates, or experiment proof decides closure | analysis-agent | checklist-result, residual-risk |
| [experience output and gates](references/experience-output-and-gates.md) | targeted | Closure depends on flow evidence, accessibility/recovery gates, analytics coupling, state-to-validation maps, or handoff fields | The body output contract is enough and evidence is not being closed | analysis-agent | gate-decision, residual-risk |
| [index](references/index.md) | index | competing experience impact modeler references require dependency, conflict, or output-fragment selection | the experience impact modeler root or a task-named reference already resolves selection | analysis-agent | reference-selection |
| [journey risk](references/journey-risk-patterns.md) | benchmark-pattern | Journey risks involve destructive/sensitive flows, high-volume operational work, experiment instrumentation, stale prior-evidence claims, or proof limits | A local component UX check has no journey, analytics, or sensitive-flow risk | analysis-agent | option-comparison, selected-approach |
