"""Shared manifest for ChangeForge code generation benchmarks."""

from __future__ import annotations


EXPECTED_BENCHMARKS: dict[str, tuple[str, ...]] = {
    "backend": (
        "idempotent-payment-create",
        "object-auth-order-read",
        "service-method-vs-new-helper",
        "webhook-signature-replay",
    ),
    "frontend": (
        "accessible-form-error-state",
        "feature-local-component-vs-shared-component",
        "optimistic-ui-rollback",
    ),
    "data-api": (
        "backward-compatible-api-field",
        "large-table-online-migration",
    ),
    "security": (
        "ssrf-url-allowlist",
    ),
    "integration": (
        "webhook-hmac-raw-body",
    ),
    "data-middleware": (
        "cache-invalidation-consistency",
        "kafka-consumer-offset-dlq",
    ),
    "reliability": (
        "burn-rate-alert-cardinality",
        "redis-cache-stampede-protection",
    ),
    "delivery": (
        "rollback-migration-compatibility",
        "helm-chart-values-schema",
    ),
    "ai": (
        "rag-tenant-permission-filter",
    ),
    "web3": (
        "eip712-chainid-nonce",
    ),
    "payment": (
        "double-entry-refund",
    ),
    "mobile": (
        "offline-sync-conflict",
    ),
    "bigdata": (
        "schema-registry-compatibility",
        "spark-skew-partitioning",
    ),
    "iot": (
        "ota-ab-rollback",
    ),
    "low-level": (
        "use-after-free-sanitizer",
    ),
    "devex": (
        "bugfix-same-pattern-scan",
        "helper-reuse-search",
        "monorepo-affected-tests",
        "structure-placement-reuse-existing-function",
        "test-failure-no-env-blame",
    ),
    "finops": (
        "cloud-cost-regression",
    ),
}
