# Professional Routing Coverage

- Generated: 2026-06-10T00:50:11.708950+00:00
- Status: pass
- Routing cases checked: 81
- Benchmark cases checked: 11
- Hidden risks covered: 34/34
- Strong matches: 30
- Weak matches: 2
- Matched by expected route only: 5
- Needs manual review: 0
- Hidden risks with weak matches: 2
- Hidden risks matched by expected route only: 5
- Hidden risks needing manual review: 0
- L1 anti-over-routing cases: 9
- Findings: 0

## Benchmark Hidden Risk Coverage

| Benchmark | Covered | Hidden Risk | Strong Matches | Weak Matches | Expected-Route-Only | Manual Review |
| --- | --- | --- | --- | --- | --- | --- |
| `evals/professional-benchmarks/adversarial/keyword-stuffed-with-skill-gaps` | true | route to nonexistent or unrelated capability | - | - | - | false |
| `evals/professional-benchmarks/adversarial/keyword-stuffed-with-skill-gaps` | true | validation command without outcome | - | - | - | false |
| `evals/professional-benchmarks/adversarial/keyword-stuffed-with-skill-gaps` | true | residual risk without owner | - | - | - | false |
| `evals/professional-benchmarks/adversarial/keyword-stuffed-with-skill-gaps` | true | hidden risk keywords without inspected boundaries | - | - | - | false |
| `evals/professional-benchmarks/ai-review/generated-code-invented-helper-without-reuse-search` | true | invented shared helper without reuse search | generated-helper-reuse-search-hidden-risk | - | - | false |
| `evals/professional-benchmarks/ai-review/generated-code-invented-helper-without-reuse-search` | true | wrong placement and business vocabulary in shared code | generated-helper-reuse-search-hidden-risk | - | - | false |
| `evals/professional-benchmarks/ai-review/generated-code-invented-helper-without-reuse-search` | true | AI-generated comments claiming unsupported universality | generated-helper-reuse-search-hidden-risk | - | - | false |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | true | IDOR from missing object ownership check | backend-auth-idor, backend-idor-tenant-leak-hidden-risk | bugfix-missing-same-pattern-scan | bugfix-missing-same-pattern-scan, go-backend-goroutine-leak-bugfix | false |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | true | tenant data leak from identifier-only query | backend-idor-tenant-leak-hidden-risk | rag-permission-leak | go-backend-goroutine-leak-bugfix, rag-permission-leak | false |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | true | local fix without same-pattern scan | backend-idor-tenant-leak-hidden-risk, bugfix-missing-same-pattern-scan, go-backend-goroutine-leak-bugfix | - | - | false |
| `evals/professional-benchmarks/backend/partial-success-without-transaction` | true | inconsistent account and billing state | backend-partial-success-transaction-hidden-risk | - | - | false |
| `evals/professional-benchmarks/backend/partial-success-without-transaction` | true | event emitted without durable state or compensation | backend-partial-success-transaction-hidden-risk | - | - | false |
| `evals/professional-benchmarks/backend/partial-success-without-transaction` | true | silent partial success with no recovery contract | backend-partial-success-transaction-hidden-risk | - | - | false |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | true | duplicate fulfillment from retry or redelivery | queue-consumer-idempotency-hidden-risk | - | payment-idempotency, sev1-payment-outage | false |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | true | poison message retry loop | kafka-consumer-lag-dlq, queue-consumer-idempotency-hidden-risk | - | - | false |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | true | lost replay path and invisible failure | iot-device-telemetry-buffer, l3-webhook-signature-verification, queue-consumer-idempotency-hidden-risk, webhook-signature-replay-hidden-risk | - | web3-eip712-replay, webhook-signature-replay | false |
| `evals/professional-benchmarks/data/redis-cache-without-ttl-or-invalidation` | true | stale entitlement state | redis-cache-ttl-invalidation-hidden-risk | - | - | false |
| `evals/professional-benchmarks/data/redis-cache-without-ttl-or-invalidation` | true | cross-tenant cache collision | redis-cache-ttl-invalidation-hidden-risk | - | - | false |
| `evals/professional-benchmarks/data/redis-cache-without-ttl-or-invalidation` | true | unbounded Redis memory growth or hot key | redis-cache-stampede, redis-cache-ttl-invalidation-hidden-risk | - | - | false |
| `evals/professional-benchmarks/debugging/retry-same-failed-approach` | true | repeated same-path retry without route repair | agent-repeated-failure-route-repair | - | - | false |
| `evals/professional-benchmarks/debugging/retry-same-failed-approach` | true | migration lock impact on production writes | deploy-repeated-retry-no-new-evidence | - | - | false |
| `evals/professional-benchmarks/debugging/retry-same-failed-approach` | true | diagnosis claim without verified cause | guessed-environment-diagnosis | - | - | false |
| `evals/professional-benchmarks/frontend/form-validation-without-accessibility-states` | true | inaccessible validation feedback | frontend-form-accessibility-states-hidden-risk | - | - | false |
| `evals/professional-benchmarks/frontend/form-validation-without-accessibility-states` | true | lossy form state after API failure | frontend-form-accessibility-states-hidden-risk | - | - | false |
| `evals/professional-benchmarks/frontend/form-validation-without-accessibility-states` | true | test coverage only verifies visual red text | frontend-form-accessibility-states-hidden-risk | - | - | false |
| `evals/professional-benchmarks/integration/webhook-without-signature-or-replay-protection` | true | forged webhook event mutates subscription state | webhook-signature-replay-hidden-risk | - | - | false |
| `evals/professional-benchmarks/integration/webhook-without-signature-or-replay-protection` | true | replayed event duplicates side effects | webhook-signature-replay-hidden-risk | - | - | false |
| `evals/professional-benchmarks/integration/webhook-without-signature-or-replay-protection` | true | parsed body invalidates HMAC verification | webhook-signature-replay-hidden-risk | - | - | false |
| `evals/professional-benchmarks/refactoring/shared-utils-business-logic-pollution` | true | business logic pollution in shared/common/utils | refactor-shared-utility-pollution-hidden-risk | - | - | false |
| `evals/professional-benchmarks/refactoring/shared-utils-business-logic-pollution` | true | unclear owner for tenant and invoice rules | refactor-shared-utility-pollution-hidden-risk | - | - | false |
| `evals/professional-benchmarks/refactoring/shared-utils-business-logic-pollution` | true | hidden behavior change during refactor | refactor-shared-utility-pollution-hidden-risk | - | - | false |
| `evals/professional-benchmarks/release/migration-without-rollback` | true | rollback fails because schema moved forward | migration-without-rollback-hidden-risk | - | api-breaking-field-rename, bigdata-schema-evolution, helm-chart-secret-values, mobile-offline-sync-conflict | false |
| `evals/professional-benchmarks/release/migration-without-rollback` | true | rolling deploy version skew breaks old pods or consumers | migration-without-rollback-hidden-risk | - | - | false |
| `evals/professional-benchmarks/release/migration-without-rollback` | true | contract phase removal before migration evidence | migration-without-rollback-hidden-risk | - | - | false |

## Findings

- None
