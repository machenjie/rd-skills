# High-Risk Test Depth And Handoff

Load only for a named migration, security, release, financial, concurrency, public-contract, integration, or multi-boundary validation risk.

## Risk To Proof Map

| Risk | Minimum evidence |
| --- | --- |
| Authorization/tenancy | Allowed/denied cases at real enforcement and object scope. |
| Money/irreversible state | Invariant, idempotency, duplicate, rollback/compensation, reconciliation. |
| Schema/migration | Forward, representative coexistence/backfill, integrity, rollback/forward-fix limit, compatibility order. |
| Public API/event | Old/new compatibility, validation/error semantics, generated artifacts, contract tests. |
| External integration | Contract/sandbox, timeout, retry, malformed response, credential denial, replay, reconciliation. |
| Concurrent/distributed state | Race/contention, order/lock invariant, duplicate delivery, recovery. |
| Frontend/accessibility | Loading, empty, error, success, denial, keyboard/focus, responsive, browser behavior. |
| Release/configuration | Built artifact, environment/config compatibility, migration order, stop, rollback, post-release plan. |
| Performance/scale | Representative input, method, threshold, comparison, environment limit. |

## Evidence Rules

- Broaden only for a concrete shared boundary or escape risk.
- Map material paths, acceptance, invariants, and failures to checks or residual risk.
- Prefer the lowest level exercising the real boundary; add a higher level only for concrete integration risk.
- Use real infrastructure or contract-calibrated doubles when its behavior is the risk.
- Show a regression assertion fails when the repaired branch is removed, inverted, or bypassed.
- Control or isolate time, randomness, IDs, data, concurrency, network behavior, and shared state.
- Record flaky, skipped, retried, quarantined, partial, and not-run checks as owned limits.
- Treat source, test, fixture, schema, configuration, generated-input, or lockfile edits as evidence invalidators.
- Refresh affected evidence after the latest material source, test, fixture, schema, or configuration edit; run only authorized commands.
- Review reports stale or missing evidence without setting timing.
- Do not label lint, type checking, one test, or manual inspection a full behavior pass.

## Handoff

Record strategy, acceptance/risk and changed-file maps, commands/results, real boundaries and doubles, proved/unproved scope, limitations, residual risk, and next step.

## Stop Conditions

- Stop before checks that mutate production, exceed authority, expose secrets, or lack cleanup.
- Return a finding for uncovered changed behavior, files, blocking risk, or last repair.
- Escalate a high-risk invariant without a realistic negative or recovery test.
- Keep release readiness unverified without built-artifact and rollback evidence.
