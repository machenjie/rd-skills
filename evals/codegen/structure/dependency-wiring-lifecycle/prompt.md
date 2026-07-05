# Benchmark Prompt

## Task

Refactor an invoice sync worker that creates a new HTTP client and DB connection pool for every request and has no shutdown path.

## Context

The starter repository uses a global service locator to fetch clients from anywhere. Tests replace the locator directly and accidentally change production wiring semantics. A retry timer and message subscription are never closed.

## Requirements

- Define a composition root that constructs the worker dependencies.
- Give every dependency an app, module, request, job, transaction, or operation lifecycle scope.
- Reuse long-lived HTTP, DB, cache, queue, and SDK clients instead of constructing them per operation.
- Add startup validation, shutdown cleanup, and test override strategy.
- Detect and remove or justify circular dependencies and service locator usage.

## Constraints

- Do not keep per-request reusable client construction.
- Do not introduce a hidden service locator.
- Do not use global mutable state without ownership, reset, synchronization, and shutdown.
- Do not let test overrides alter production wiring semantics.

## Deliverables

- Dependency Wiring Plan.
- Composition root and dependency graph.
- Lifecycle scope per dependency.
- Shutdown cleanup and circular dependency check.

## Completion Evidence

- Tests or validation show a shared app-scoped client and explicit shutdown.
- Service locator usage is removed or justified by framework convention.
- Configuration binding is typed and validated.
