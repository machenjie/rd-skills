# Module Boundary Benchmarks And Enforcement

Load this reference when module boundary design needs named benchmark support, dependency enforcement examples, a boundary classification matrix, or public API surface examples. The `SKILL.md` body carries the decision-critical routing and output contract; this file carries deep benchmark and enforcement material for architecture-design, implementation-planning, code-review, and refactoring.

## Benchmark Anchors

- Eric Evans, Domain-Driven Design: bounded contexts define semantic boundaries where language, model, and invariants are consistent; crossing a context requires explicit translation such as a context map or anti-corruption layer.
- Robert C. Martin package principles: release equivalence, common closure, common reuse, and acyclic dependencies explain why modules should group code that changes and releases together while avoiding cycles and unused dependency burden.
- Conway's Law and Team Topologies: module boundaries should reflect ownership and communication paths so one stream-aligned team can evolve a value stream without routine cross-team coordination.
- Modular monolith practice: a single deployable can still enforce hard internal isolation and versioned contracts, leaving service extraction as a later operational decision only when independent deployability is justified.
- Dependency Cruiser, import-linter, ArchUnit, and NDepend: module rules should fail CI through import graph contracts, not rely on review comments or convention.

## Module Boundary Classification Matrix

| Boundary Type | Scope | Public API | Allowed Imports | Example |
| --- | --- | --- | --- | --- |
| Business Capability Module | Single bounded context | Use cases, domain events, DTOs | Shared technical utilities; no other capability internals | `orders/` imports only `shared/` |
| Shared Technical Module | Cross-cutting pure utilities | Utility functions, primitives | Standard library and third-party dependencies; no business modules | `shared/crypto`, `shared/date` |
| Integration Adapter | External system boundary | Adapter interface or port | Owning capability module plus external SDK | `payment-gateway-adapter/` |
| Domain Extension | Sub-domain specialization | Extension hooks, events | Parent capability public API only | `enterprise-billing/` imports `billing/api` |
| Orchestration / Gateway | Cross-capability coordination | Use-case orchestrators | Multiple capability public APIs, read-only fan-in unless explicitly owned | `checkout/` imports `orders/api` and `inventory/api` |

## Dependency Direction Enforcement Rules

Allowed dependency examples:

```text
orders -> shared/utils           (business capability -> shared technical utility)
payment-adapter -> orders/api    (adapter -> capability public API)
checkout -> orders/api           (orchestrator -> capability public API)
checkout -> inventory/api        (orchestrator -> capability public API)
```

Forbidden dependency examples:

```text
orders -> payments               (capability A -> capability B: business coupling)
payments -> orders               (capability B -> capability A: bidirectional circular risk)
orders -> orders/internal/db     (external module -> private internals)
shared/utils -> orders           (shared utility -> business capability inversion)
payments -> checkout             (owned capability -> orchestrator direction inversion)
```

Dependency Cruiser rule example:

```json
{
  "forbidden": [
    {
      "name": "no-cross-capability-import",
      "from": { "path": "^src/orders" },
      "to": { "path": "^src/payments" }
    },
    {
      "name": "no-internal-access",
      "from": { "pathNot": "^src/orders" },
      "to": { "path": "^src/orders/internal" }
    }
  ]
}
```

import-linter contract example:

```ini
[importlinter:contract:no-cross-capability]
name = No cross-capability imports
type = forbidden
source_modules = orders
forbidden_modules = payments
```

## Module Public API Surface Design

```text
orders/
  api/              PUBLIC: everything here is the module contract
    __init__.py     exports: OrderService, CreateOrderCommand, OrderCreatedEvent
    order_service.py
    commands.py
    events.py
  internal/         PRIVATE: never imported from outside
    _order_entity.py
    _order_repository.py
    _order_validator.py
  tests/
```

Rules:

- External modules import only from the public API surface.
- Internals are unreachable from outside and enforced by import tooling where possible.
- Every new public export is a compatibility commitment and requires current consumer evidence.
