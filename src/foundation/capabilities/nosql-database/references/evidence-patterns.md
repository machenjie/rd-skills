# NoSQL Database Evidence Patterns

Use this reference when NoSQL closure depends on validation freshness, prior source or task evidence claims, access-pattern proof, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second NoSQL modeling guide.

## Store-Decision-To-Validation Map

| NoSQL claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Store choice is justified | Access patterns, workload shape, invariants, scale model, rejected relational/cache/search alternatives, and owner review | The inspected workload has a reason to use the selected non-relational store | Future queries, live cost, or production skew are safe |
| Key/index design supports callers | AP list, caller paths, partition/sort key, secondary indexes, cardinality estimate, and rejected scan path | Inspected reads and writes have a modeled key or index path | Future access paths and uninspected consumers may still require backfill or redesign |
| Hot partition risk is bounded | Tenant/time/status distribution, write-rate math, top-key skew estimate, throttle limits, and monitor owner | The inspected key design addresses obvious skew risks | Production traffic, burst behavior, or cloud quota changes are proven |
| Consistency model protects invariants | Invariant list, strong/eventual decision, stale-read consequence, conflict behavior, and validation or handoff | Inspected invariants have intentional consistency treatment | Untested cross-partition races and remote side effects remain outside the claim |
| Schema evolution is compatible | `schemaVersion` or equivalent, old/new reader behavior, backfill plan, validation query, and rollback behavior | Inspected document versions can be read through the named rollout | Legacy data outside the sample and future shape changes remain unproven |
| Denormalized data is repairable | Source of truth, writer owner, propagation trigger, lag budget, drift check, and repair/replay path | Inspected duplicate data has an owner and repair mechanism | Uninspected consumers and drift modes remain outside the claim |
| TTL/retention is safe | TTL field semantics, records excluded from expiry, regulated-data classification, deletion test or configuration review, and owner | Inspected expiration or retention behavior is intentional | Store clock behavior or compliance approval is fully proven |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, workload estimates, store docs, telemetry, and previous validation as selectors until current source, store constraints, tests, and fresh reports confirm them.
- Recheck prior "NoSQL fit is proven", "partition key is safe", "secondary-index lag is acceptable", or "documents are versioned" claims against current access patterns, schema, and validation.
- Mark evidence stale after edits to table/collection definitions, keys, indexes, schema versions, TTL fields, denormalized writers, migrations/backfills, validators, tests, reports, or generated artifacts.
- For each final NoSQL decision, cite current command, query, test, report, or owner-review evidence.
- Otherwise, mark the decision not run and name its residual risk.

- If live table change, backfill, TTL enablement, index creation, replay, or repair job, record environment, owner approval, stop condition, rollback or pause path, and redaction rule.
- If production telemetry, cloud console, or data query, keep access read-only or approved-connector-scoped, aggregate sensitive labels, and redact tenant/user/secret-bearing fields.
