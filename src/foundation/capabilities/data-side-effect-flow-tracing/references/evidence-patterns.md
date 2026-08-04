# Data Side-Effect Flow Tracing Evidence Patterns

Use this reference when side-effect flow closure depends on validation freshness, prior source or task evidence claims, sensitive telemetry boundaries, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second side-effect taxonomy.

## Flow-Claim-To-Validation Map

| Flow claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Side effects are visible and owned | Entry point, callers, callees, inventory, owner boundary, order, and validation status | Inspected effects have named owners and order | Uninspected framework hooks or dynamic dispatch are absent |
| Pure logic remains pure | Mapper/getter/validator/policy/domain scan, convention exception, and tests or review | Obvious hidden mutation/IO was checked in inspected paths | Every generated wrapper or decorator is effect-free |
| Transaction/event/cache order is safe | Transaction boundary, commit point, outbox or publish-after-commit decision, cache source/key/order, rollback behavior | Consumers and cache are not knowingly exposed to rolled-back state | All downstream consumers are correct or idempotent |
| External/file IO is bounded | Adapter boundary, timeout, cancellation, retry/no-retry, idempotency, cleanup, reconciliation, and operator visibility | The inspected IO effect has failure and duplicate behavior | External provider behavior or production latency is fully proven |
| Nondeterminism is controlled | Clock/random/env/flag source, injection or centralization, defaults, test override, replay/audit impact | Non-replayable inputs are named and testable | All tests are deterministic under every runner |
| Observability has no business effect | Log/metric/trace fields, redaction, exporter failure behavior, callback policy, and security review when sensitive | Observability is not knowingly authoritative or leaking obvious secrets | Every sink or retention policy is approved |
| Validation is fresh after final flow edit | Test/validator/review path, side-effect IDs covered, exit code or manual result, final edit scope, freshness | Evidence covers the final inspected flow map | Untested retries, external systems, or operator procedures are proven |
| Tool output is safe to retain | Action class, permission state, redaction rule, artifact path, retention owner, and rollback or cleanup path | Evidence collection avoids obvious sensitive output leakage | Every future connector export or debug trace is safe |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, prior incidents, generated clients, decorators, ORM hooks, validation output, and telemetry as selectors until current source, tests, configs, and owner evidence confirm them.
- Accept a prior flow-safety claim only while current callers, wrappers, transaction owner, cache users, topics, adapters, and validation still match. Examples include "flow is safe", "event is post-commit", "mapper is pure", "retry is idempotent", and "cache is invalidated".
- Mark flow evidence stale after edits to call order, transaction scope, cache key, event topic, adapter boundary, retry wrapper, compensation, observability fields, generated clients, tests, or build outputs.
- For reachable side-effect edges changed in the traced flow, map the effect and ordering claims to fresh evidence and state proof limits. Add hidden-effect or same-pattern scans, validation commands, prior-claim decisions, tool-output artifacts, and residual risks when the selected inputs and flow risk trigger them.

- If staging replay, integration sandbox, failure injection, queue/cache/file cleanup rehearsal, record data class, stop condition, cleanup, rollback or compensation, and redaction.
- If production replay, live provider call, queue mutation, cache purge, file delete, admin/support action, or connector write, require owner approval, blast-radius limit, rollback or compensation path, and redaction rule.
