# High-Risk Test Depth And Handoff

Load this reference only when the task names a migration, security, release, financial, concurrency, public-contract, external-integration, or multi-boundary validation risk.

## Risk To Proof Map

| Risk | Minimum evidence |
| --- | --- |
| Authorization or tenant isolation | Allowed and denied cases at the real enforcement boundary, including object scope. |
| Money or irreversible state | Branch, invariant, idempotency, duplicate, rollback or compensation, and reconciliation tests. |
| Schema or data migration | Forward migration, representative backfill or coexistence, integrity check, rollback/forward-fix limit, and compatibility order. |
| Public API or event contract | Old/new consumer compatibility, validation/error semantics, generated artifacts when applicable, and contract tests. |
| External integration | Contract or sandbox test plus timeout, retry, malformed response, credential denial, replay, and reconciliation paths. |
| Concurrency or distributed state | Race/contention test, ordering or lock invariant, duplicate delivery, and failure recovery. |
| Frontend or accessibility | Loading, empty, error, success, denial, keyboard/focus, responsive, and browser-relevant behavior. |
| Release or configuration | Built artifact, environment/config compatibility, migration order, stop signal, rollback check, and post-release validation plan. |
| Performance or scale | Representative input, measurement method, threshold, regression comparison, and environment caveat. |

## Evidence Rules

- Map every material changed path, acceptance item, invariant, and failure mode to a check or residual risk.
- Prefer the lowest test level that exercises the real failure boundary; add a higher level only for a concrete integration risk.
- Use real infrastructure or contract-calibrated doubles when database, queue, cache, filesystem, HTTP, or browser behavior is the risk.
- Prove that a regression assertion fails when the repaired branch is removed, inverted, or bypassed.
- Keep time, randomness, UUIDs, test data, concurrency, network behavior, and shared state deterministic or isolated.
- Treat flaky, skipped, retried, quarantined, partial, and not-run checks as explicit limitations with an owner.
- Record source, test, fixture, schema, configuration, generated-input, or lockfile edits that invalidate evidence and the resulting Core Guard G refresh decision.
- After that decision, task mode may run accepted commands.
- Review mode reports stale or missing evidence without independently setting timing.
- Do not call lint, type checking, a single test, or manual inspection a full behavior pass.

## Natural-Language Handoff

```markdown
## Validation Strategy

## Acceptance and Risk Mapping

## Changed-file Coverage

## Commands Run and Actual Results

## Fixtures, Mocks, and Real Boundaries

## What the Evidence Proves

## Flaky, Skipped, Partial, or Not-run Checks

## Unverified Scope and Residual Risk

## Recommended Next Step
```

## Stop Conditions

- Stop before a check that mutates production, exceeds authority, exposes secrets, or lacks cleanup.
- Return a finding when changed behavior, a changed file, a blocking risk, or the last repair remains uncovered.
- Escalate when a high-risk invariant has no realistic negative or recovery test.
- Keep release readiness unverified when the evidence does not cover the built artifact and rollback boundary.
