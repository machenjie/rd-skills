# Professional Routing Coverage

- Generated: 2026-06-10T05:18:53.703746+00:00
- Status: pass
- Routing cases checked: 88
- Benchmark cases checked: 30
- Hidden risks checked: 91
- Strongly covered: 87
- Not required: 4
- Weak-only: 0
- Expected-route-only supplemental: 7
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
| `evals/professional-benchmarks/api/contract-change-without-consumer-verification` | covered | contract change without consumer verification | api-breaking-field-rename |
| `evals/professional-benchmarks/api/contract-change-without-consumer-verification` | covered | provider-only test misses consumer compatibility | api-breaking-field-rename |
| `evals/professional-benchmarks/api/contract-change-without-consumer-verification` | covered | breaking API field change lacks schema diff or migration evidence | api-breaking-field-rename |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | covered | IDOR from missing object ownership check | backend-auth-idor, backend-idor-tenant-leak-hidden-risk |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | covered | tenant data leak from identifier-only query | backend-idor-tenant-leak-hidden-risk |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | covered | local fix without same-pattern scan | backend-idor-tenant-leak-hidden-risk, bugfix-missing-same-pattern-scan, go-backend-goroutine-leak-bugfix |
| `evals/professional-benchmarks/backend/partial-success-without-transaction` | covered | inconsistent account and billing state | backend-partial-success-transaction-hidden-risk |
| `evals/professional-benchmarks/backend/partial-success-without-transaction` | covered | event emitted without durable state or compensation | backend-partial-success-transaction-hidden-risk |
| `evals/professional-benchmarks/backend/partial-success-without-transaction` | covered | silent partial success with no recovery contract | backend-partial-success-transaction-hidden-risk |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | covered | duplicate fulfillment from retry or redelivery | queue-consumer-idempotency-hidden-risk |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | covered | poison message retry loop | kafka-consumer-lag-dlq, queue-consumer-idempotency-hidden-risk |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | covered | lost replay path and invisible failure | iot-device-telemetry-buffer, l3-webhook-signature-verification, queue-consumer-idempotency-hidden-risk, webhook-signature-replay-hidden-risk |
| `evals/professional-benchmarks/data/cache-key-cross-tenant-collision` | covered | cross-tenant cache collision | redis-cache-ttl-invalidation-hidden-risk |
| `evals/professional-benchmarks/data/cache-key-cross-tenant-collision` | covered | stale authorization or entitlement state | redis-cache-ttl-invalidation-hidden-risk |
| `evals/professional-benchmarks/data/cache-key-cross-tenant-collision` | covered | unbounded cache cardinality or hot key | redis-cache-stampede, redis-cache-ttl-invalidation-hidden-risk |
| `evals/professional-benchmarks/data/redis-cache-without-ttl-or-invalidation` | covered | stale entitlement state | redis-cache-ttl-invalidation-hidden-risk |
| `evals/professional-benchmarks/data/redis-cache-without-ttl-or-invalidation` | covered | cross-tenant cache collision | redis-cache-ttl-invalidation-hidden-risk |
| `evals/professional-benchmarks/data/redis-cache-without-ttl-or-invalidation` | covered | unbounded Redis memory growth or hot key | redis-cache-stampede, redis-cache-ttl-invalidation-hidden-risk |
| `evals/professional-benchmarks/data/relational-query-without-index-or-explain` | covered | relational query without index or explain | large-table-migration |
| `evals/professional-benchmarks/data/relational-query-without-index-or-explain` | covered | missing index or query plan evidence on large table | large-table-migration |
| `evals/professional-benchmarks/data/relational-query-without-index-or-explain` | covered | production cardinality not represented by dev data | large-table-migration |
| `evals/professional-benchmarks/debugging/retry-same-failed-approach` | covered | repeated same-path retry without route repair | agent-repeated-failure-route-repair |
| `evals/professional-benchmarks/debugging/retry-same-failed-approach` | covered | migration lock impact on production writes | deploy-repeated-retry-no-new-evidence |
| `evals/professional-benchmarks/debugging/retry-same-failed-approach` | covered | diagnosis claim without verified cause | guessed-environment-diagnosis |
| `evals/professional-benchmarks/frontend/form-validation-without-accessibility-states` | covered | inaccessible validation feedback | frontend-form-accessibility-states-hidden-risk |
| `evals/professional-benchmarks/frontend/form-validation-without-accessibility-states` | covered | lossy form state after API failure | frontend-form-accessibility-states-hidden-risk |
| `evals/professional-benchmarks/frontend/form-validation-without-accessibility-states` | covered | test coverage only verifies visual red text | frontend-form-accessibility-states-hidden-risk |
| `evals/professional-benchmarks/integration/webhook-without-signature-or-replay-protection` | covered | forged webhook event mutates subscription state | webhook-signature-replay-hidden-risk |
| `evals/professional-benchmarks/integration/webhook-without-signature-or-replay-protection` | covered | replayed event duplicates side effects | webhook-signature-replay-hidden-risk |
| `evals/professional-benchmarks/integration/webhook-without-signature-or-replay-protection` | covered | parsed body invalidates HMAC verification | webhook-signature-replay-hidden-risk |
| `evals/professional-benchmarks/language/cpp-raw-pointer-lifetime-without-raii` | covered | C++ raw pointer lifetime without RAII | low-level-rust-ffi-memory-safety |
| `evals/professional-benchmarks/language/cpp-raw-pointer-lifetime-without-raii` | covered | dangling pointer ownership unclear | low-level-rust-ffi-memory-safety |
| `evals/professional-benchmarks/language/cpp-raw-pointer-lifetime-without-raii` | covered | sanitizer evidence missing | low-level-rust-ffi-memory-safety |
| `evals/professional-benchmarks/language/go-goroutine-without-cancel-or-error-propagation` | covered | Go goroutine without cancel or error propagation | go-backend-goroutine-leak-bugfix |
| `evals/professional-benchmarks/language/go-goroutine-without-cancel-or-error-propagation` | covered | goroutine leak from missing cancellation | go-backend-goroutine-leak-bugfix |
| `evals/professional-benchmarks/language/go-goroutine-without-cancel-or-error-propagation` | covered | error propagation lost in goroutine | go-backend-goroutine-leak-bugfix |
| `evals/professional-benchmarks/language/idiom-mismatch-copied-from-other-language` | covered | idiom mismatch copied from other language | implementation-naming-taxonomy |
| `evals/professional-benchmarks/language/idiom-mismatch-copied-from-other-language` | covered | invented abstraction ignores repository convention | implementation-naming-taxonomy |
| `evals/professional-benchmarks/language/idiom-mismatch-copied-from-other-language` | covered | framework-incorrect naming or file layout | implementation-naming-taxonomy |
| `evals/professional-benchmarks/language/java-executor-without-shutdown-or-bounds` | covered | Java executor without shutdown or bounds | java-executor-lifecycle-hidden-risk |
| `evals/professional-benchmarks/language/java-executor-without-shutdown-or-bounds` | covered | thread pool lifecycle leak | java-executor-lifecycle-hidden-risk |
| `evals/professional-benchmarks/language/java-executor-without-shutdown-or-bounds` | covered | interruption behavior not handled | java-executor-lifecycle-hidden-risk |
| `evals/professional-benchmarks/language/performance-unbounded-concurrency` | covered | performance unbounded concurrency | java-executor-lifecycle-hidden-risk |
| `evals/professional-benchmarks/language/performance-unbounded-concurrency` | covered | runtime safety invariant missing for concurrent hot path | java-executor-lifecycle-hidden-risk, typescript-any-api-boundary-hidden-risk |
| `evals/professional-benchmarks/language/performance-unbounded-concurrency` | covered | measurement evidence absent for thread pool saturation | java-executor-lifecycle-hidden-risk |
| `evals/professional-benchmarks/language/python-async-blocking-call-without-timeout` | covered | Python async blocking call without timeout | language-testing-strategy-runtime-boundary, python-async-blocking-call-hidden-risk |
| `evals/professional-benchmarks/language/python-async-blocking-call-without-timeout` | covered | blocking IO inside event loop | python-async-blocking-call-hidden-risk |
| `evals/professional-benchmarks/language/python-async-blocking-call-without-timeout` | covered | cancellation behavior untested | python-async-blocking-call-hidden-risk |
| `evals/professional-benchmarks/language/rust-unsafe-boundary-without-invariants` | covered | Rust unsafe boundary without invariants | low-level-rust-ffi-memory-safety |
| `evals/professional-benchmarks/language/rust-unsafe-boundary-without-invariants` | covered | unsafe block lacks safety contract | low-level-rust-ffi-memory-safety |
| `evals/professional-benchmarks/language/rust-unsafe-boundary-without-invariants` | covered | FFI ownership can cause use-after-free | low-level-rust-ffi-memory-safety |
| `evals/professional-benchmarks/language/shell-unquoted-rm-path` | covered | shell unquoted variable can delete wrong path | shell-unquoted-variable-secret-risk |
| `evals/professional-benchmarks/language/shell-unquoted-rm-path` | covered | secret exposed through process list | shell-unquoted-variable-secret-risk |
| `evals/professional-benchmarks/language/shell-unquoted-rm-path` | covered | destructive script lacks dry-run and trap cleanup | shell-unquoted-variable-secret-risk |
| `evals/professional-benchmarks/language/sql-dynamic-query-without-parameterization` | covered | SQL dynamic query without parameterization | sql-dynamic-query-no-parameterization |
| `evals/professional-benchmarks/language/sql-dynamic-query-without-parameterization` | covered | unsafe interpolation allows injection | sql-dynamic-query-no-parameterization |
| `evals/professional-benchmarks/language/sql-dynamic-query-without-parameterization` | covered | tenant predicate missing from query test | sql-dynamic-query-no-parameterization |
| `evals/professional-benchmarks/language/typescript-any-at-api-boundary` | covered | TypeScript any at API boundary | typescript-any-api-boundary-hidden-risk |
| `evals/professional-benchmarks/language/typescript-any-at-api-boundary` | covered | runtime validation missing for external data | java-executor-lifecycle-hidden-risk, typescript-any-api-boundary-hidden-risk |
| `evals/professional-benchmarks/language/typescript-any-at-api-boundary` | covered | nullable state hidden by cast | typescript-any-api-boundary-hidden-risk |
| `evals/professional-benchmarks/refactoring/refactor-with-hidden-behavior-change` | covered | hidden behavior change during supposedly behavior-preserving refactor | refactor-shared-utility-pollution-hidden-risk |
| `evals/professional-benchmarks/refactoring/refactor-with-hidden-behavior-change` | covered | public API or error semantics changed without evidence | api-breaking-field-rename, implementation-naming-taxonomy, k8s-probe-rbac-networkpolicy, oversized-directory-module-split, refactor-shared-utility-pollution-hidden-risk |
| `evals/professional-benchmarks/refactoring/refactor-with-hidden-behavior-change` | covered | deletion path not proven safe | refactor-shared-utility-pollution-hidden-risk |
| `evals/professional-benchmarks/refactoring/shared-utils-business-logic-pollution` | covered | business logic pollution in shared/common/utils | refactor-shared-utility-pollution-hidden-risk |
| `evals/professional-benchmarks/refactoring/shared-utils-business-logic-pollution` | covered | unclear owner for tenant and invoice rules | refactor-shared-utility-pollution-hidden-risk |
| `evals/professional-benchmarks/refactoring/shared-utils-business-logic-pollution` | covered | hidden behavior change during refactor | refactor-shared-utility-pollution-hidden-risk |
| `evals/professional-benchmarks/release/migration-without-rollback` | covered | rollback fails because schema moved forward | migration-without-rollback-hidden-risk |
| `evals/professional-benchmarks/release/migration-without-rollback` | covered | rolling deploy version skew breaks old pods or consumers | migration-without-rollback-hidden-risk |
| `evals/professional-benchmarks/release/migration-without-rollback` | covered | contract phase removal before migration evidence | migration-without-rollback-hidden-risk |
| `evals/professional-benchmarks/testing/e2e-test-used-for-unit-level-bug` | covered | E2E test used for unit-level bug | e2e-layer-mismatch-unit-bug |
| `evals/professional-benchmarks/testing/e2e-test-used-for-unit-level-bug` | covered | slow browser test hides cheaper unit coverage | e2e-layer-mismatch-unit-bug |
| `evals/professional-benchmarks/testing/e2e-test-used-for-unit-level-bug` | covered | test layer selection inverted for local logic | e2e-layer-mismatch-unit-bug |
| `evals/professional-benchmarks/testing/integration-test-mocks-away-real-boundary` | covered | integration test mocks away real boundary | backend-partial-success-transaction-hidden-risk |
| `evals/professional-benchmarks/testing/integration-test-mocks-away-real-boundary` | covered | mocked repository hides database constraint or transaction behavior | backend-partial-success-transaction-hidden-risk |
| `evals/professional-benchmarks/testing/integration-test-mocks-away-real-boundary` | covered | transaction failure path not tested against real database | backend-partial-success-transaction-hidden-risk |
| `evals/professional-benchmarks/testing/language-runtime-risk-wrong-test-layer` | covered | language runtime risk tested at wrong layer | language-testing-strategy-runtime-boundary |
| `evals/professional-benchmarks/testing/language-runtime-risk-wrong-test-layer` | covered | Python async blocking call lacks async harness | language-testing-strategy-runtime-boundary |
| `evals/professional-benchmarks/testing/language-runtime-risk-wrong-test-layer` | covered | runtime boundary not covered by language-specific validation | language-testing-strategy-runtime-boundary |
| `evals/professional-benchmarks/testing/regression-test-passes-before-fix` | covered | test passes before fix and is not a real regression test | completion-evidence-unverified-fix |
| `evals/professional-benchmarks/testing/regression-test-passes-before-fix` | covered | defect recurrence path not protected | completion-evidence-unverified-fix |
| `evals/professional-benchmarks/testing/regression-test-passes-before-fix` | covered | completion claim without red-before-fix evidence | completion-evidence-unverified-fix |
| `evals/professional-benchmarks/testing/unit-test-overmocks-private-helper` | covered | over-mocked private helper hides behavior | test-structure-helper-pollution |
| `evals/professional-benchmarks/testing/unit-test-overmocks-private-helper` | covered | private helper assertion freezes implementation | test-structure-helper-pollution |
| `evals/professional-benchmarks/testing/unit-test-overmocks-private-helper` | covered | unit boundary not protected by observable assertions | test-structure-helper-pollution |

<details>
<summary>Supplemental debug matches</summary>

| Benchmark | Hidden Risk | Weak Matches | Expected-Route-Only |
| --- | --- | --- | --- |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | IDOR from missing object ownership check | bugfix-missing-same-pattern-scan | bugfix-missing-same-pattern-scan, go-backend-goroutine-leak-bugfix, low-level-rust-ffi-memory-safety |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | tenant data leak from identifier-only query | rag-permission-leak | go-backend-goroutine-leak-bugfix, rag-permission-leak |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | duplicate fulfillment from retry or redelivery | - | payment-idempotency, sev1-payment-outage |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | lost replay path and invisible failure | - | web3-eip712-replay, webhook-signature-replay |
| `evals/professional-benchmarks/data/relational-query-without-index-or-explain` | missing index or query plan evidence on large table | sql-dynamic-query-no-parameterization | sql-dynamic-query-no-parameterization |
| `evals/professional-benchmarks/language/performance-unbounded-concurrency` | runtime safety invariant missing for concurrent hot path | low-level-rust-ffi-memory-safety | low-level-rust-ffi-memory-safety |
| `evals/professional-benchmarks/language/sql-dynamic-query-without-parameterization` | tenant predicate missing from query test | large-table-migration | - |
| `evals/professional-benchmarks/language/typescript-any-at-api-boundary` | runtime validation missing for external data | go-backend-goroutine-leak-bugfix, large-table-migration, low-level-rust-ffi-memory-safety | - |
| `evals/professional-benchmarks/release/migration-without-rollback` | rollback fails because schema moved forward | - | api-breaking-field-rename, bigdata-schema-evolution, helm-chart-secret-values, mobile-offline-sync-conflict |

</details>

## Findings

- None
