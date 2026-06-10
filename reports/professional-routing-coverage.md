# Professional Routing Coverage

- Generated: 2026-06-10T02:20:14.009304+00:00
- Status: pass
- Routing cases checked: 81
- Benchmark cases checked: 11
- Hidden risks checked: 34
- Strongly covered: 30
- Not required: 4
- Weak-only: 0
- Expected-route-only supplemental: 5
- Uncovered: 0
- Manual review: 0
- L1 anti-over-routing cases: 9
- Findings: 0

## Benchmark Hidden Risk Coverage

| Benchmark | Coverage Status | Hidden Risk | Strong Matches |
| --- | --- | --- | --- |
| `evals/professional-benchmarks/adversarial/keyword-stuffed-with-skill-gaps` | not-required | route to nonexistent or unrelated capability | - |
| `evals/professional-benchmarks/adversarial/keyword-stuffed-with-skill-gaps` | not-required | validation command without outcome | - |
| `evals/professional-benchmarks/adversarial/keyword-stuffed-with-skill-gaps` | not-required | residual risk without owner | - |
| `evals/professional-benchmarks/adversarial/keyword-stuffed-with-skill-gaps` | not-required | hidden risk keywords without inspected boundaries | - |
| `evals/professional-benchmarks/ai-review/generated-code-invented-helper-without-reuse-search` | covered | invented shared helper without reuse search | generated-helper-reuse-search-hidden-risk |
| `evals/professional-benchmarks/ai-review/generated-code-invented-helper-without-reuse-search` | covered | wrong placement and business vocabulary in shared code | generated-helper-reuse-search-hidden-risk |
| `evals/professional-benchmarks/ai-review/generated-code-invented-helper-without-reuse-search` | covered | AI-generated comments claiming unsupported universality | generated-helper-reuse-search-hidden-risk |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | covered | IDOR from missing object ownership check | backend-auth-idor, backend-idor-tenant-leak-hidden-risk |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | covered | tenant data leak from identifier-only query | backend-idor-tenant-leak-hidden-risk |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | covered | local fix without same-pattern scan | backend-idor-tenant-leak-hidden-risk, bugfix-missing-same-pattern-scan, go-backend-goroutine-leak-bugfix |
| `evals/professional-benchmarks/backend/partial-success-without-transaction` | covered | inconsistent account and billing state | backend-partial-success-transaction-hidden-risk |
| `evals/professional-benchmarks/backend/partial-success-without-transaction` | covered | event emitted without durable state or compensation | backend-partial-success-transaction-hidden-risk |
| `evals/professional-benchmarks/backend/partial-success-without-transaction` | covered | silent partial success with no recovery contract | backend-partial-success-transaction-hidden-risk |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | covered | duplicate fulfillment from retry or redelivery | queue-consumer-idempotency-hidden-risk |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | covered | poison message retry loop | kafka-consumer-lag-dlq, queue-consumer-idempotency-hidden-risk |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | covered | lost replay path and invisible failure | iot-device-telemetry-buffer, l3-webhook-signature-verification, queue-consumer-idempotency-hidden-risk, webhook-signature-replay-hidden-risk |
| `evals/professional-benchmarks/data/redis-cache-without-ttl-or-invalidation` | covered | stale entitlement state | redis-cache-ttl-invalidation-hidden-risk |
| `evals/professional-benchmarks/data/redis-cache-without-ttl-or-invalidation` | covered | cross-tenant cache collision | redis-cache-ttl-invalidation-hidden-risk |
| `evals/professional-benchmarks/data/redis-cache-without-ttl-or-invalidation` | covered | unbounded Redis memory growth or hot key | redis-cache-stampede, redis-cache-ttl-invalidation-hidden-risk |
| `evals/professional-benchmarks/debugging/retry-same-failed-approach` | covered | repeated same-path retry without route repair | agent-repeated-failure-route-repair |
| `evals/professional-benchmarks/debugging/retry-same-failed-approach` | covered | migration lock impact on production writes | deploy-repeated-retry-no-new-evidence |
| `evals/professional-benchmarks/debugging/retry-same-failed-approach` | covered | diagnosis claim without verified cause | guessed-environment-diagnosis |
| `evals/professional-benchmarks/frontend/form-validation-without-accessibility-states` | covered | inaccessible validation feedback | frontend-form-accessibility-states-hidden-risk |
| `evals/professional-benchmarks/frontend/form-validation-without-accessibility-states` | covered | lossy form state after API failure | frontend-form-accessibility-states-hidden-risk |
| `evals/professional-benchmarks/frontend/form-validation-without-accessibility-states` | covered | test coverage only verifies visual red text | frontend-form-accessibility-states-hidden-risk |
| `evals/professional-benchmarks/integration/webhook-without-signature-or-replay-protection` | covered | forged webhook event mutates subscription state | webhook-signature-replay-hidden-risk |
| `evals/professional-benchmarks/integration/webhook-without-signature-or-replay-protection` | covered | replayed event duplicates side effects | webhook-signature-replay-hidden-risk |
| `evals/professional-benchmarks/integration/webhook-without-signature-or-replay-protection` | covered | parsed body invalidates HMAC verification | webhook-signature-replay-hidden-risk |
| `evals/professional-benchmarks/refactoring/shared-utils-business-logic-pollution` | covered | business logic pollution in shared/common/utils | refactor-shared-utility-pollution-hidden-risk |
| `evals/professional-benchmarks/refactoring/shared-utils-business-logic-pollution` | covered | unclear owner for tenant and invoice rules | refactor-shared-utility-pollution-hidden-risk |
| `evals/professional-benchmarks/refactoring/shared-utils-business-logic-pollution` | covered | hidden behavior change during refactor | refactor-shared-utility-pollution-hidden-risk |
| `evals/professional-benchmarks/release/migration-without-rollback` | covered | rollback fails because schema moved forward | migration-without-rollback-hidden-risk |
| `evals/professional-benchmarks/release/migration-without-rollback` | covered | rolling deploy version skew breaks old pods or consumers | migration-without-rollback-hidden-risk |
| `evals/professional-benchmarks/release/migration-without-rollback` | covered | contract phase removal before migration evidence | migration-without-rollback-hidden-risk |

<details>
<summary>Supplemental debug matches</summary>

| Benchmark | Hidden Risk | Weak Matches | Expected-Route-Only |
| --- | --- | --- | --- |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | IDOR from missing object ownership check | bugfix-missing-same-pattern-scan | bugfix-missing-same-pattern-scan, go-backend-goroutine-leak-bugfix |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | tenant data leak from identifier-only query | rag-permission-leak | go-backend-goroutine-leak-bugfix, rag-permission-leak |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | duplicate fulfillment from retry or redelivery | - | payment-idempotency, sev1-payment-outage |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | lost replay path and invisible failure | - | web3-eip712-replay, webhook-signature-replay |
| `evals/professional-benchmarks/release/migration-without-rollback` | rollback fails because schema moved forward | - | api-breaking-field-rename, bigdata-schema-evolution, helm-chart-secret-values, mobile-offline-sync-conflict |

</details>

## Findings

- None
