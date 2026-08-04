# Frontend Testing Evidence Patterns

Use this reference when frontend-testing closure depends on repository inspection, prior task evidence, observable action sequence, validation freshness, command output, report artifacts, tool permission boundaries, or a changed-behavior-to-test map. Keep it as an evidence map, not a second frontend testing tutorial.

## Changed-Behavior-To-Test Map

| Claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Visible behavior is covered | Component or route source, user-visible start/end state, test level, accessible query, command, and owner. | The inspected behavior has a runnable proof obligation at the selected frontend boundary. | Uninspected journeys, real browser differences, or production data states are safe. |
| Role or permission branch is covered | Role fixture, denied fixture, unauthenticated or owner/non-owner case when relevant, and non-leak assertion. | The inspected role branch distinguishes allowed, denied, hidden, disabled, or request-access behavior. | Backend authorization or every tenant/object permission path is enforced. |
| API-backed state is covered | API schema or typed fixture source, MSW or equivalent handler, reset policy, loading/success/error/stale/timeout case. | The inspected UI state follows the declared response shape and deterministic async lifecycle. | Provider behavior, backend contract enforcement, or network/browser edge cases are complete. |
| Accessibility interaction is covered | Role/name/value assertion, keyboard sequence, focus assertion, live-region/error announcement, and axe or manual artifact. | The inspected interactive state has concrete accessibility evidence. | Full screen-reader certification, all browsers, zoom, high contrast, or specialist audit is complete. |
| Flake control is credible | No arbitrary sleeps, isolated state, handler reset, deterministic data, clock/network control, and full-suite or shard outcome. | The inspected test is less likely to fail because of order, timing, or polluted state. | CI capacity, all shards, or future test order changes cannot reintroduce flake. |
| Validation is fresh | Command, working directory, exit code/outcome, report or artifact path, and final-edit freshness. | Evidence was produced after the final material change for the mapped frontend behavior. | Later source, fixture, schema, story, config, generated, or report edits are covered. |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, prior stories, old snapshots, coverage notes, generated reports, and observable action sequence as discovery inputs until current source confirms them.
- Accept a prior coverage claim only while current component source, tests, stories, schemas, fixtures, and validation artifacts still match. Examples include "existing test covers this", "story already has state", "mock matches API", "a11y covered", and "E2E is sufficient".
- Reject or downgrade memory that lacks date, owner, command, inspected component/route scope, fixture source, accessibility scope, or validation freshness.
- Mark evidence stale after edits to component source, hooks, routes, state model, API schema, typed fixtures, MSW handlers, stories, snapshots, accessibility behavior, test config, reports, build outputs, or validation mappings.
- Map every final frontend-testing confidence claim to a command, test, story, screenshot, accessibility artifact, schema/fixture source, review artifact, owner approval, or explicit not-run residual risk.

- If snapshot update, fixture regeneration, generated client refresh, or story artifact refresh, record source-of-truth input, generated output owner, diff review, and rollback path.
- If browser cloud, production analytics, session replay, customer screenshot, or connector export, require permission, redact tenant/user/secret-bearing values, and state retention limits.
