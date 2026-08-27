---
name: frontend-change-builder
description: "Use `task-agent` for bounded frontend component or browser changes involving interaction, accessibility, API failures, security, or regression proof. Skip backend-only work and design exploration without implementation."
---

# frontend-change-builder

## Role

Support `task-agent` in owning bounded frontend interaction states within declared owners and acceptance.

## When To Use

- frontend component change
- browser behavior change

## Do Not Use

- backend only
- design exploration without implementation

## Required Inputs

- current owner, consumers, behavior contracts, and observable acceptance
- validation signal and proof limits

## Professional Decision Rules

- When any named frontend decision remains unresolved, keep the change with its owner and load only the active named References whose contracts supply the required outputs.
- No shared UI, hook, store, client, flag, or dependency without consumers, reuse, and deletion evidence.

## High-Value Gotchas

- Promoting feature-local state or a one-consumer component into a shared store or wrapper can hide domain assumptions and widen every failure and rollback path.
- Duplicated derived state or an out-of-order response can overwrite fresher input, leave stale loading or error state, or make retry repeat the wrong transition.
- A generic catch can collapse permission, validation, conflict, timeout, and terminal failures into a false recovery path.
- Snapshot or automated accessibility success does not prove keyboard focus, live-region announcements, responsive overflow, or screen-reader recovery.

## Execution Checklist

- Inspect the current component owner, consumers, design-system alternatives, and deletion path before adding shared UI, a hook, store, client, flag, or dependency.
- Trace local, form, URL, server-cache, global, and derived state through loading, empty, success, validation, permission, conflict, timeout, cancellation, stale-response, and retry transitions.
- Run component or integration tests through accessible queries for the changed normal, failure, denied, cancellation, stale-response, and recovery paths.
- Exercise the changed keyboard, focus, live-region, screen-reader, responsive, and text-overflow paths; record the artifact and proof limits.
- Run a malicious-content and denied-path fixture when HTML, content, token, script, or browser-storage behavior changes.
- Search sibling components, hooks, stores, validators, API clients, and tests for the same failure pattern; record hits, exclusions, and residual risk.

## Stop / Escalation Conditions

- Stop implementation on unresolved authority, owner, behavior, or proof.
- Stop unbounded or unapproved tool actions.

## Output Contract

- changed boundaries, current evidence, proof limits, and residual UX risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded L2 review needs a compact frontend inventory for component, route, form, state, API, accessibility, security, performance, or tests | The inline quality gate is enough or deeper gate/evidence mapping is required | task-agent | checklist-result, residual-risk |
| [component placement and reuse gates](references/component-placement-and-reuse-gates.md) | targeted | Component, shared UI, hook, store, client, or reuse ownership remains open | Owner, current consumers, and reuse decision are fixed | task-agent | boundary-decision, selected-approach, residual-risk |
| [state ownership and api failure gates](references/state-ownership-and-api-failure-gates.md) | targeted | State ownership or API, failure, or retry contract remains open | Current contract fixes states, failures, recovery, and retry | task-agent | decision-record, failure-decision, residual-risk |
| [accessibility closure gates](references/accessibility-closure-gates.md) | targeted | Frontend accessibility closure decision remains open | Accepted accessibility contract already fixes the implementation | task-agent | gate-decision, validation-plan, proof-limit |
| [frontend security closure gates](references/frontend-security-closure-gates.md) | targeted | HTML, content, token, script, or browser-storage security decision remains open | No frontend security boundary changes | task-agent | gate-decision, validation-plan, residual-risk |
| [frontend quality and validation evidence](references/frontend-quality-and-validation-evidence.md) | evidence-pattern | State, testability, reliability, performance, or quality claim needs proof | No changed frontend quality claim awaits validation | task-agent | evidence-record, validation-plan, proof-limit, residual-risk |
| [same pattern scan and handoff evidence](references/same-pattern-scan-and-handoff-evidence.md) | evidence-pattern | Same-pattern, tool-boundary, or final-handoff evidence is required | No scan or closure claim remains | task-agent | evidence-record, validation-plan, proof-limit, residual-risk |
| [index](references/index.md) | index | competing frontend change builder references require dependency, conflict, or output-fragment selection | the frontend change builder root or a task-named reference already resolves selection | task-agent | reference-selection |
| [solution optimality](references/solution-optimality.md) | targeted | A rendering, state, data-fetching, asset, lifecycle, or interaction-path choice may materially change user experience or browser resource use | Copy/style changes do not affect runtime behavior, or current design-system/repository evidence already fixes the bounded implementation | task-agent | selected-approach, residual-risk |
| [visual quality and redesign](references/visual-quality-and-redesign.md) | targeted | The user explicitly requests visual polish or redesign, or hierarchy, typography, spacing, density, or composition is an acceptance target | The frontend task is ordinary behavior work without a visual-quality acceptance target, or reference fidelity alone defines the visual goal | task-agent | selected-approach, residual-risk |
| [visual reference reconstruction](references/visual-reference-reconstruction.md) | targeted | Screenshot, mockup, or reference-image implementation requires visual fidelity or matching the supplied reference | No visual reference is supplied, or visual polish and redesign do not require matching one | task-agent | proof-limit, selected-approach, validation-plan |
