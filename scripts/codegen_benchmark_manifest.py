"""Shared manifest for ChangeForge code generation benchmarks."""

from __future__ import annotations


EXPECTED_BENCHMARKS: dict[str, tuple[str, ...]] = {
    "backend": (
        "idempotent-payment-create",
        "method-vs-service-vs-helper",
        "object-auth-order-read",
        "service-method-vs-new-helper",
        "webhook-signature-replay",
    ),
    "frontend": (
        "accessible-form-error-state",
        "component-hook-naming-placement",
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
    "structure": (
        "design-pattern-overengineering",
        "inheritance-vs-composition-decision",
        "module-object-cluster-organization",
        "object-method-encapsulation-placement",
        "observer-lifecycle-backpressure",
        "over-fragmented-file-split",
        "oversized-service-object-split",
        "parent-child-sibling-object-relationship",
        "pattern-selection-with-real-variation",
        "reckless-small-file-merge",
        "testability-seam-design",
        "dependency-wiring-lifecycle",
        "algorithm-data-structure-selection",
        "failure-contract-design",
        "configuration-runtime-policy",
        "model-boundary-mapping",
        "data-side-effect-flow-tracing",
        "architecture-enforcement-tooling",
        "consumer-impact-analysis",
        "cleanup-deletion-governance",
        "side-effect-boundary",
    ),
    "performance": (
        "event-loop-blocking-async-path",
        "lock-held-across-io",
        "per-operation-client-construction",
    ),
    "finops": (
        "cloud-cost-regression",
    ),
}
