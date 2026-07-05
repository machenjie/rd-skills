# Frontend Testing Evidence Patterns

Use this reference when frontend-testing closure depends on repository graph, project memory, execution trajectory, validation freshness, command output, report artifacts, tool permission boundaries, or a changed-behavior-to-test map. Keep it as an evidence map, not a second frontend testing tutorial.

## Changed-Behavior-To-Test Map

| Claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Visible behavior is covered | Component or route source, user-visible start/end state, test level, accessible query, command, and owner. | The inspected behavior has a runnable proof obligation at the selected frontend boundary. | Uninspected journeys, real browser differences, or production data states are safe. |
| Role or permission branch is covered | Role fixture, denied fixture, unauthenticated or owner/non-owner case when relevant, and non-leak assertion. | The inspected role branch distinguishes allowed, denied, hidden, disabled, or request-access behavior. | Backend authorization or every tenant/object permission path is enforced. |
| API-backed state is covered | API schema or typed fixture source, MSW or equivalent handler, reset policy, loading/success/error/stale/timeout case. | The inspected UI state follows the declared response shape and deterministic async lifecycle. | Provider behavior, backend contract enforcement, or network/browser edge cases are complete. |
| Accessibility interaction is covered | Role/name/value assertion, keyboard sequence, focus assertion, live-region/error announcement, and axe or manual artifact. | The inspected interactive state has concrete accessibility evidence. | Full screen-reader certification, all browsers, zoom, high contrast, or specialist audit is complete. |
| Flake control is credible | No arbitrary sleeps, isolated state, handler reset, deterministic data, clock/network control, and full-suite or shard outcome. | The inspected test is less likely to fail because of order, timing, or polluted state. | CI capacity, all shards, or future test order changes cannot reintroduce flake. |
| Validation is fresh | Command, working directory, exit code/outcome, report or artifact path, and final-edit freshness. | Evidence was produced after the final material change for the mapped frontend behavior. | Later source, fixture, schema, story, config, generated, or report edits are covered. |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, prior stories, old snapshots, coverage notes, generated reports, and execution trajectory as discovery inputs until current source confirms them.
- Accept prior "existing test covers this", "story already has state", "mock matches API", "a11y covered", or "E2E is sufficient" claims only when current component source, tests, stories, schemas, fixtures, and validation artifacts still match.
- Reject or downgrade memory that lacks date, owner, command, inspected component/route scope, fixture source, accessibility scope, or validation freshness.
- Mark evidence stale after edits to component source, hooks, routes, state model, API schema, typed fixtures, MSW handlers, stories, snapshots, accessibility behavior, test config, reports, build outputs, or validation mappings.
- Map every final frontend-testing confidence claim to a command, test, story, screenshot, accessibility artifact, schema/fixture source, review artifact, owner approval, or explicit not-run residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, graph search, report inspection, and markdown validation | Read-only local shell action; cite searched paths and avoid full output dumps. |
| Local frontend tests, accessibility scans, Storybook checks, visual diffs, validators, and builds | State-mutating only for reports, caches, screenshots, snapshots, dist/build artifacts, or local fixtures; cite log path, command, exit code, and cleanup. |
| Snapshot update, fixture regeneration, generated client refresh, or story artifact refresh | State-mutating development action; record source-of-truth input, generated output owner, diff review, and rollback path. |
| Browser cloud, production analytics, session replay, customer screenshot, or connector export | High-risk or connector-scoped action; require permission, redact tenant/user/secret-bearing values, and state retention limits. |

## Handoff Evidence Shape

```yaml
frontend_testing_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_behavior_to_test_map:
    - behavior_or_state: ""
      source_or_story_path: ""
      test_level: ""
      validation_command: ""
      exit_code_or_status: ""
      artifact_or_report: ""
      proves: ""
      does_not_prove: ""
      owner: ""
      freshness: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
