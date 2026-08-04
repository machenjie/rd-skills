# Hookless Professional Benchmarks

> Checked-in captured outputs only; this report is not a fresh live-agent evaluation.

- Cases checked: 46
- Captured comparisons passed: 46
- Release-critical cases: 4
- Errors: 0

| Case | Class | Primary Skill | Layer 3 count | Baseline | With Skill | Delta | Status |
|---|---|---|---:|---:|---:|---:|---|
| `evals/professional-benchmarks/adversarial/keyword-stuffed-with-skill-gaps` | adversarial-negative-control | `ai-code-review-refactor` | 3 | 1 | 8 | 7 | expected-fail-detected |
| `evals/professional-benchmarks/ai-review/generated-code-invented-helper-without-reuse-search` | standard | `ai-code-review-refactor` | 3 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/api/contract-change-without-consumer-verification` | standard | `data-api-contract-changer` | 3 | 0 | 10 | 10 | pass |
| `evals/professional-benchmarks/api/public-export-without-compatibility-proof` | standard | `data-api-contract-changer` | 3 | 0 | 8 | 8 | pass |
| `evals/professional-benchmarks/architecture/unknown-consumers-dual-authority-premature-sharing` | release-critical | `architecture-impact-reviewer` | 3 | 0 | 14 | 14 | pass |
| `evals/professional-benchmarks/backend/idor-local-fix-without-same-pattern-scan` | standard | `backend-change-builder` | 3 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/backend/partial-success-without-transaction` | standard | `backend-change-builder` | 3 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/backend/queue-consumer-missing-idempotency` | standard | `backend-change-builder` | 3 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/backend/status-lifecycle-without-invariant-map` | standard | `domain-impact-modeler` | 3 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/data/cache-key-cross-tenant-collision` | standard | `data-middleware-change-builder` | 3 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/data/redis-cache-without-ttl-or-invalidation` | standard | `data-middleware-change-builder` | 3 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/data/relational-query-without-index-or-explain` | standard | `data-middleware-change-builder` | 3 | 0 | 10 | 10 | pass |
| `evals/professional-benchmarks/debugging/retry-same-failed-approach` | standard | `delivery-release-gate` | 3 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/debugging/root-cause-without-failure-contract-map` | standard | `backend-change-builder` | 3 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/domain/ai-permission-blind-retrieval-tool-authority` | standard | `security-privacy-gate` | 1 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/domain/bigdata-cdc-cutover-backfill-live-conflict` | standard | `data-middleware-change-builder` | 1 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/domain/iot-brownout-boot-loop-credential-recovery` | standard | `delivery-release-gate` | 1 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/domain/low-level-ffi-unwind-allocator-publication` | standard | `backend-change-builder` | 1 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/domain/mobile-account-switch-deeplink-background-duplicate` | standard | `installed-client-change-builder` | 1 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/domain/payment-partial-fill-cancel-sequence-kill-switch` | standard | `backend-change-builder` | 1 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/domain/web3-upgrade-reorg-cross-domain-duplicate` | standard | `integration-change-builder` | 1 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/frontend/form-validation-without-accessibility-states` | standard | `frontend-change-builder` | 3 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/integration/webhook-without-signature-or-replay-protection` | standard | `integration-change-builder` | 3 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/language/cpp-raw-pointer-lifetime-without-raii` | standard | `ai-code-review-refactor` | 1 | 0 | 10 | 10 | pass |
| `evals/professional-benchmarks/language/go-goroutine-without-cancel-or-error-propagation` | standard | `backend-change-builder` | 1 | 0 | 10 | 10 | pass |
| `evals/professional-benchmarks/language/idiom-mismatch-copied-from-other-language` | standard | `backend-change-builder` | 1 | 1 | 10 | 9 | pass |
| `evals/professional-benchmarks/language/java-executor-without-shutdown-or-bounds` | standard | `backend-change-builder` | 1 | 0 | 10 | 10 | pass |
| `evals/professional-benchmarks/language/performance-unbounded-concurrency` | standard | `backend-change-builder` | 1 | 1 | 10 | 9 | pass |
| `evals/professional-benchmarks/language/python-async-blocking-call-without-timeout` | standard | `backend-change-builder` | 1 | 0 | 10 | 10 | pass |
| `evals/professional-benchmarks/language/rust-unsafe-boundary-without-invariants` | standard | `ai-code-review-refactor` | 1 | 0 | 10 | 10 | pass |
| `evals/professional-benchmarks/language/shell-unquoted-rm-path` | standard | `delivery-release-gate` | 1 | 0 | 10 | 10 | pass |
| `evals/professional-benchmarks/language/sql-dynamic-query-without-parameterization` | standard | `data-middleware-change-builder` | 1 | 0 | 10 | 10 | pass |
| `evals/professional-benchmarks/language/typescript-any-at-api-boundary` | standard | `frontend-change-builder` | 1 | 0 | 10 | 10 | pass |
| `evals/professional-benchmarks/logging/pii-retry-noise-correlation-audit-boundary` | release-critical | `logging-design-gate` | 3 | 0 | 14 | 14 | pass |
| `evals/professional-benchmarks/refactoring/refactor-with-hidden-behavior-change` | standard | `ai-code-review-refactor` | 3 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/refactoring/senior-shared-helper-without-placement` | standard | `engineering-change-analysis` | 1 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/refactoring/shared-utils-business-logic-pollution` | standard | `engineering-change-analysis` | 1 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/release/migration-without-rollback` | standard | `delivery-release-gate` | 3 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/reliability/retry-amplification-stale-entitlement-recovery` | release-critical | `reliability-observability-gate` | 3 | 0 | 14 | 14 | pass |
| `evals/professional-benchmarks/security/object-auth-ssrf-integrity-secret-reachability` | release-critical | `security-privacy-gate` | 3 | 0 | 14 | 14 | pass |
| `evals/professional-benchmarks/skill-authoring/hookless-jit-skill-review` | standard | `ai-code-review-refactor` | 1 | 0 | 9 | 9 | pass |
| `evals/professional-benchmarks/testing/e2e-test-used-for-unit-level-bug` | standard | `quality-test-gate` | 3 | 1 | 10 | 9 | pass |
| `evals/professional-benchmarks/testing/integration-test-mocks-away-real-boundary` | standard | `quality-test-gate` | 2 | 0 | 10 | 10 | pass |
| `evals/professional-benchmarks/testing/language-runtime-risk-wrong-test-layer` | standard | `quality-test-gate` | 2 | 0 | 10 | 10 | pass |
| `evals/professional-benchmarks/testing/regression-test-passes-before-fix` | standard | `quality-test-gate` | 2 | 0 | 10 | 10 | pass |
| `evals/professional-benchmarks/testing/unit-test-overmocks-private-helper` | standard | `quality-test-gate` | 3 | 0 | 10 | 10 | pass |
