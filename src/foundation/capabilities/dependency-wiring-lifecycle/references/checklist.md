# Dependency Wiring Lifecycle Checklist

- When the dependency graph changes, name its new or changed entries across dependencies, collaborators, resource handles, clients, pools, timers, subscriptions, workers, providers, containers, factories, and test overrides.
- Identify construction owner, lifecycle scope, consumers, config inputs, identity/tenant/cancellation/transaction coupling, and shutdown owner.
- Inspect composition roots, constructors, factories, providers, DI/container modules, imports, config binding, generated clients, tests/fixtures, shutdown hooks, and current graph evidence.
- Prefer existing composition roots, factories, providers, facades, or test seams before introducing a container, singleton, service locator, global, or lazy provider.
- Match client and pool construction to library, state, isolation, and cleanup contracts. Reject repeated construction of resources that should be shared; an operation-scoped client may use a shared transport when its state cannot safely be shared.
- Define failure and teardown behavior for the selected lifecycle.
- Include startup validation, health, cancellation, timeouts, retry/refresh, or resource cleanup only where the dependency contract requires them.
- For lazy/provider decisions, record race behavior, error caching, retry behavior, first-use latency, observability, and test override behavior.
- For config-driven wiring, record typed config, defaults, variant matrix, startup fail-fast, secret boundary, rollout/rollback, and tests.
- For test overrides, preserve production graph semantics through public seams; avoid private/global patching unless justified and owned.
- Map every changed dependency, graph edge, lifecycle scope, config variant, startup/shutdown path, override seam, repository inspection/prior evidence claim, and generated artifact to validation evidence or residual risk.
