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
    ),
    "reliability": (
        "burn-rate-alert-cardinality",
    ),
    "delivery": (
        "rollback-migration-compatibility",
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
    ),
    "iot": (
        "ota-ab-rollback",
    ),
    "low-level": (
        "use-after-free-sanitizer",
    ),
    "devex": (
        "monorepo-affected-tests",
        "structure-placement-reuse-existing-function",
    ),
    "finops": (
        "cloud-cost-regression",
    ),
}
