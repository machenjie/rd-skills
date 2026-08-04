---
name: frontend-testing
description: "`analysis-agent`/`task-agent`/`review-agent`: use for component, route, browser, accessibility, and API-backed UI-state tests; skip backend, portfolio, and release-verdict work."
---

# frontend-testing

## Registry Trigger

**Use when**

- test component route browser accessibility interaction and API backed UI state behavior

**Do not use when**

- work is limited to backend enforcement overall proof portfolio integration seams or release readiness

## Skill Role

Select the frontend boundary, states, interactions, fixtures, and observable oracles that expose the changed user-facing risk. Own component, route, browser, and client-fixture behavior.

## High-Value Rules

- Select only reachable loading, success, empty, stale, error, conflict, permission, cancellation, and rollback states.
- Name the failure mechanism and recovery outcome for every retained state.
- Define assertions for accessible names, rendered meaning, focus, announcements, navigation, client state, or outbound requests.
- Select browser tests for history, focus, layout, and browser APIs, with E2E reserved for cross-system journeys.
- Derive fixtures from owned contracts and reset handlers, clocks, cache, storage, and rendered state.
- Select bounded waits for observable terminal conditions instead of arbitrary sleeps.
- Test UI permission differences without claiming backend enforcement.
- Preserve the first flake failure, environment, fixture state, evidence, owner, and remediation condition.

## Anti-Patterns

- Reject CSS selectors, private hook/call assertions, test identifiers, or snapshots as the sole oracle for user-visible meaning.
- Reject happy-path-only dynamic views, hand-written contract-drifting fixtures, fixed sleeps, unreset handlers or storage, and permission tests that exercise only the privileged view.
- Reject component evidence promoted to browser, backend-policy, provider, accessibility-certification, or release proof beyond its inspected states.

## Stop Conditions

Stop when state or recovery is unclear, required environments are unavailable, or fixture ownership and flake reproduction are unknown. Frontend evidence does not prove backend enforcement, production data, or release readiness.

## Output Contract

- Return a frontend-test decision: state behaviors, interactions, oracles, boundaries, fixtures, cleanup, accessibility, flake controls, evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Component route browser visual network-fixture or accessibility evidence competes | One frontend boundary clearly carries the risk | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Roles async states recovery forms accessibility cleanup or flake controls need multi-part closure | No user-observable frontend behavior changes | task-agent, analysis-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Confidence depends on fresh stories schemas fixtures browsers accessibility artifacts commands or reports | No frontend-confidence claim awaits proof | task-agent, analysis-agent, review-agent | evidence-record, proof-limit, residual-risk |
