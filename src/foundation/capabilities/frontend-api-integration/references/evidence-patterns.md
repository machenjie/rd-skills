# Frontend API Integration Evidence Patterns

Use this reference when frontend API integration closure depends on validation freshness, operation-level proof, race or auth evidence, prior source or task evidence claims, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second lifecycle matrix.

## Operation-To-Validation Map

| Integration claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Request lifecycle is bounded | Operation list, timeout, cancellation trigger, stale-response rule, and test or review artifact | Inspected operations cannot obviously hang or overwrite current UI state | All browsers, providers, or production latency distributions are safe |
| Mutation retry is safe or disabled | Method, side-effect class, idempotency requirement, retry stop condition, unknown-timeout behavior, and test | Inspected mutation avoids obvious duplicate effects | Server dedupe implementation is correct unless separately verified |
| Auth expiry is recoverable | 401 path, refresh-once rule, cache clear, failure redirect, denied state, and test or review artifact | Inspected auth branch avoids raw 401 and refresh loops | Deployed identity provider behavior or token storage security is fully proven |
| Response shape is validated | Schema or guard source, consumed fields, malformed fixture, invalid-shape state, and test | Inspected response cannot crash the render path for tested malformed shape | Server contract or all provider variants are compatible |
| Pagination remains coherent | Pagination type, sort/tiebreaker, cursor/filter binding, empty/end states, and edge test or residual risk | Inspected list behavior handles declared pagination edges | All concurrent inserts/deletes or deep page behavior are proven |
| Cache freshness is intentional | Cache key, user/tenant scope, freshness or stale allowance, retention or eviction policy, invalidation triggers, reset trigger, applicable library-option mapping, and test | Inspected cached data has explicit freshness, retention, and reset rules | Production cache pressure or all permission changes are covered |
| Telemetry is safe | Trace/log fields, redaction rule, destination allowlist, token/PII exclusion, and review artifact | Inspected diagnostics avoid obvious secret or PII exposure | External monitoring configuration is fully verified |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, generated clients, mocks, stories, and prior validation as selectors until current API client, component, schema, mocks, and tests confirm them.
- Accept prior "React Query handles it", "client retries safely", "auth wrapper covers 401", or "mock matches contract" claims only when current source and validation still match the changed operation.
- Mark evidence stale after edits to endpoints, generated clients, consumed fields, cache keys, auth handlers, retry wrappers, pagination, optimistic updates, mocks, tests, reports, or build outputs.
- Map each triggered lifecycle, retry/idempotency, authorization, schema, cache, pagination, optimistic-update, telemetry, or handoff decision for the changed frontend-API operation to applicable command, test, report, owner-review evidence, or explicit not-run residual risk.

- If live API call, production auth test, third-party mutation, or browser credential change, record environment, owner approval, stop condition, rollback plan, and redaction rule.
- If production telemetry or monitoring query, keep access read-only or approved-connector-scoped, aggregate sensitive labels, and redact tenant/user/secret-bearing fields.
