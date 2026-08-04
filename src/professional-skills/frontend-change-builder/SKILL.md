---
name: frontend-change-builder
description: "Use `task-agent` for bounded frontend component or browser changes involving interaction, accessibility, API failures, security, or regression proof. Skip backend-only work and design exploration without implementation."
---

# frontend-change-builder

## Role

Support `task-agent` in changing frontend interaction states, accessibility,
responsive behavior, and API failure handling.

## When To Use

- frontend component change
- browser behavior change

## Do Not Use

- backend only
- design exploration without implementation

## Required Inputs

- experience evidence
- interaction-state and API failure contracts
- design-system and accessibility constraints

## Professional Decision Rules

- Keep state in the narrowest correct owner and derive rather than duplicate state.
- Handle loading, empty, error, success, disabled, permission, cancellation, retry, and stale-response behavior for async work.
- Reuse design-system components and preserve keyboard, focus, semantic, responsive, and screen-reader behavior.
- Map UI acceptance to component, integration, accessibility, and visual validation proportional to risk.

## High-Value Gotchas

- Duplicated derived state drifts.
- Unmount, cancellation, and out-of-order responses create race defects.
- Automated accessibility checks do not prove keyboard and screen-reader flows.

## Execution Checklist

1. Trace the affected interaction states, API outcomes, focus path, and responsive behavior.
2. Choose state ownership and component reuse from current design-system and lifecycle evidence.
3. Implement the bounded behavior with explicit cancellation, denial, failure, and recovery paths.
4. Stop closure when an affected state lacks accessibility or behavior proof.

## Stop / Escalation Conditions

- Stop implementation when component ownership, state scope, API error semantics, accessibility/focus behavior, or security boundary is implicit.
- Stop shared UI, hook, global store, wrapper API client, mode flag, or dependency creation until current consumers, native/design-system alternatives, and rollback/deletion path are proven.
- Stop frontend closure when loading, empty, error, success, disabled, validation, permission, and retry/fallback states are not mapped to validation evidence or accepted residual risk.
- Stop tool execution when browser, app, account, API, storage, production-like, or connector actions lack permission/sandbox, test scope, rollback/revert path, and redaction evidence.

## Output Contract

- changed interaction and state boundaries
- accessibility and failure-state evidence
- current post-final-edit validation result, including interaction-state and API-failure proof
- residual UX risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded L2 review needs a compact frontend inventory for component, route, form, state, API, accessibility, security, performance, or tests | The inline quality gate is enough or deeper gate/evidence mapping is required | task-agent | checklist-result, residual-risk |
| [frontend output and gates](references/frontend-output-and-gates.md) | targeted | Drafting or reviewing placement decisions, failure contracts, a11y/security gates, same-pattern scans, state-to-validation maps, or closure evidence | The body output contract and minimal verification are sufficient for the risk | task-agent | gate-decision, residual-risk |
| [index](references/index.md) | index | competing frontend change builder references require dependency, conflict, or output-fragment selection | the frontend change builder root or a task-named reference already resolves selection | task-agent | reference-selection |
| [solution optimality](references/solution-optimality.md) | targeted | A rendering, state, data-fetching, asset, lifecycle, or interaction-path choice may materially change user experience or browser resource use | Copy/style changes do not affect runtime behavior, or current design-system/repository evidence already fixes the bounded implementation | task-agent | selected-approach, residual-risk |
