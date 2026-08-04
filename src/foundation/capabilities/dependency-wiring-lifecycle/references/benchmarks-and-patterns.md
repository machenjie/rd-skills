# Dependency Wiring Lifecycle Benchmarks And Patterns

Use this reference when `dependency-wiring-lifecycle` needs more depth than the main `SKILL.md` should carry efficiently. Keep the body focused on routing, output, and gates; use this file for composition-root, lifecycle, resource, lazy/provider, config variant, test seam, and anti-pattern review.

## Benchmark Anchors

- Composition root practice: application graph construction belongs at the boundary, not in business logic.
- Constructor injection and dependency inversion: stable required collaborators should be explicit.
- Factory/provider injection: use for short-lived objects or justified lazy access while preserving type and test control.
- Connection pooling and graceful shutdown: reusable clients, pools, timers, streams, sockets, and workers need health and close paths.
- Structured concurrency and cancellation: request/job/transaction scope should not leak into app scope.
- DI container validation and dependency graph checks: graph claims require current source and validation.
- Test double contract discipline: overrides should preserve production semantics or be backed by contract/integration proof.

## Lifecycle Scope Matrix

| Scope | Fits | Evidence required |
| --- | --- | --- |
| App | Reusable HTTP, DB, Redis, Kafka, telemetry, SDK clients, pools, workers. | Composition root, startup validation, shutdown path, metrics. |
| Module | Shared module collaborator hidden behind facade. | Module owner, facade boundary, dependency direction. |
| Request/job | Identity, cancellation, transaction, per-operation context. | Propagation path, cleanup, concurrency semantics. |
| Transaction | Unit of work, repository session, commit/rollback owner. | Transaction boundary, lifecycle owner, tests. |
| Short-lived | Domain object or one-off resource that must not be shared. | Factory owner, cleanup, no global retention. |
| Test | Fake/stub/mock/spy or fixture graph. | Public seam, fixture owner, production-semantics proof. |

## Construction Decision Pattern

```text
Can the existing composition root own construction?
  yes -> extend it with explicit lifecycle and tests.
  no -> use module factory or facade if ownership is local.
Does each operation need a fresh object?
  yes -> use factory injection and define cleanup.
Is lazy access required?
  yes -> record race, error caching, retry, first-use latency, and test override.
Is the dependency selected by config?
  yes -> route typed config and graph variant matrix.
```

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| Per-operation client construction. | Socket churn, token churn, pool starvation, and slow hot paths. | Long-lived client at narrowest safe owner. |
| Business logic uses service locator. | Hidden graph, cycles, and untestable behavior. | Constructor/factory/provider seam. |
| Mutable singleton stores request or tenant state. | Cross-request leakage and races. | Request/job scope or synchronized owner with reset and cleanup. |
| Lazy lookup hides cycle. | Circular ownership appears only in production. | Fix graph direction or bound lazy behavior with exit plan. |
| Test patches private globals. | Tests pass against a graph production cannot build. | Public seam plus contract/integration proof. |
| Shutdown path omitted. | Timers, sockets, streams, pools, or loops leak on deploy/test. | Close/drain/unsubscribe/stop path and teardown validation. |

## Handoff Boundaries

- Use `implementation-structure-design` when file, object, function, factory, or facade placement is primary.
- Use `configuration-runtime-policy` when provider, mode, region, tenant, flag, or environment selects the graph.
- Use `language-performance-safety` and `reliability-observability-gate` for resource cleanup, pool sizing, event loops, and production lifecycle readiness.
- Use `testability-seam-design` and `quality-test-gate` for fake/stub/mock strategy and validation depth.
- Use `architecture-impact-reviewer` or `module-boundary-design` when dependency direction or module boundaries change.
- Use `security-privacy-gate` when credentials, tenants, auth clients, or secrets can cross trust boundaries.
