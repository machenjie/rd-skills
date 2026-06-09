---
name: module-boundary-design
description: Designs module boundaries around business capability, ownership, dependency direction, contracts, and circular dependency prevention.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "19"
changeforge_version: 0.1.0
---

# Mission

Define **module boundaries that protect business capability ownership, dependency direction, change isolation, and explicit cross-boundary contracts** — ensuring that each module can be changed, tested, and reasoned about independently, that circular dependencies are structurally impossible, and that the import graph is enforced by automated tooling rather than convention.

# When To Use

Use this capability when a change: adds a new module, package, bounded context, or feature directory; moves code from one module to another; introduces a new import from one module into another (especially across bounded context lines); creates shared utility code that might inadvertently accumulate business logic; proposes merging or splitting an existing module; or is flagged in review for "circular dependency", "coupling too many modules", or "business logic in shared utility."

# Do Not Use When

Do not use this capability to organize code by technical type alone (e.g., `controllers/`, `services/`, `models/` top-level folders — that is a `layered-architecture-design` concern). Do not use it to create arbitrary folder hierarchies without business ownership or dependency direction rationale. Do not use it to enforce module boundaries so granular that every function lives in an isolated module (boundary cost must be justified by change isolation benefit).

# Non-Negotiable Rules

- **Module boundaries must be defined by business capability, not technical type.** A module named `OrderService` that owns the `Order` business capability (entities, use cases, API, persistence) is correct. A module named `Services` that contains all application services across all capabilities is a layer, not a boundary — it provides no isolation between capabilities.
- **Every cross-boundary import must go through a public contract, not an internal type.** Module A must not import `module-b/internal/OrderRepository` or `module-b/db/models.py`. Module B must expose a public API (`module-b/api/OrderService`, `module-b/api/OrderEvent`) and internal structure must be inaccessible from outside. In Python: `_private` convention + `__all__`; in TypeScript: `index.ts` barrel with explicit exports; in Java: `package-private` classes for internals + public interfaces.
- **Circular dependencies are prohibited.** Module A → Module B → Module A creates: inability to test A without B and B without A; merge conflicts when both teams modify the shared types; infinite import resolution in some runtimes. Circular dependencies must be detected by automated tooling (Dependency Cruiser, import-linter, ArchUnit) and treated as build failures.
- **Shared utilities must not contain business logic.** `shared/`, `common/`, `utils/` modules are dependency magnets. When they accumulate business rules, every module that imports `shared/` becomes coupled to every business rule that `shared/` contains — even unrelated ones. Rule: shared modules may contain only pure technical utilities (date formatting, crypto primitives, HTTP client wrapper). Business rules must live in the owning capability's module.
- **Every module boundary must have a named owner.** A module without an owner has no one to approve boundary changes, no one to maintain the contract, and no one to prevent inappropriate imports. Ownership must be declared (CODEOWNERS file, team annotation, README in module root).
- **Dependency direction must be enforced by tooling, not convention.** Architecture decisions decay without automated enforcement. Dependency Cruiser (JavaScript/TypeScript), import-linter (Python), ArchUnit (Java), NDepend (.NET) must run in CI. A PR that introduces a forbidden import must fail CI — not pass and receive a review comment.
- **Module public API surface must be minimal.** Export only what consumers need. Every additional exported type is a surface area that constrains the module's ability to refactor internally. The public API of a module is a commitment to all consumers.
- **Directory size is a module-boundary signal.** A large directory is acceptable only when it still represents one owner, one capability or layer convention, one public API family, and one change rhythm.
- **One directory should represent one module boundary unless it is explicitly a layer or grouping convention.** Mixed business object families, owners, public APIs, dependency clusters, jobs, adapters, domain code, infra, and test helpers require decomposition review.
- **Every module split must declare its relationship type.** Use sibling, parent-child, producer-consumer, upper-lower layer, orchestrator, adapter/port, or shared technical module; do not split by arbitrary folder taste.
- **Change locality is a boundary quality gate.** A small requirement should usually change the owning module and its tests; widespread edits require business justification or boundary repair.
- **Public API expansion must be justified by real current consumers.** Do not export types, helpers, or submodule internals "just in case."
- **Shared/common must not become a workaround for poor ownership decisions.** Shared technical modules contain domain-free utilities only and must not host business fixtures or rules.

# Industry Benchmarks

Anchor against: **Eric Evans "Domain-Driven Design"** — Bounded Context: a semantic boundary within which a domain model is consistent; each bounded context owns its language, model, and invariants; crossing a bounded context requires explicit translation (Context Map, Anti-Corruption Layer). **Robert C. Martin "Package Principles"** (in "Agile Software Development: Principles, Patterns, and Practices") — REP (Release Equivalence Principle): the granule of reuse is the granule of release; CCP (Common Closure Principle): classes that change together belong together; CRP (Common Reuse Principle): don't force users to depend on things they don't use; ADP (Acyclic Dependencies Principle): no cycles in the dependency graph. **Dependency Cruiser** (github.com/sverweij/dependency-cruiser) — JavaScript/TypeScript dependency rule enforcement; `.dependency-cruiser.js` with `forbidden` rules; runs in CI. **import-linter** (github.com/seddryck/import-linter) — Python contract: `[importlinter:contract:orders-no-payments]`; `type: layers` or `type: forbidden`; fails import if violated. **ArchUnit** (archunit.org) — Java `noClasses().that().resideIn("..orders..")...dependOn("..payments..")`. **NDepend** (.NET) — dependency matrix + dependency rule DSL. **Conway's Law** — system architecture reflects team communication structure; module boundaries should align with team ownership for effective parallel development. **Team Topologies** (Skelton & Pais) — stream-aligned team owns a value stream boundary; enabling team provides shared capability; complicated subsystem team owns complex technical modules. **Modular Monolith** (Sam Newman, Mauro Servienti) — full business capability boundary in a single deployable; modules have hard internal isolation and versioned contracts; can be extracted to microservices later if independent deployability becomes justified.

### Module Boundary Classification Matrix

| Boundary Type | Scope | Public API | Allowed Imports | Example |
| --- | --- | --- | --- | --- |
| Business Capability Module | Single bounded context | Use cases, domain events, DTOs | Shared technical utils; no other capability modules | `orders/` imports only `shared/` |
| Shared Technical Module | Cross-cutting pure utilities | Utility functions, primitives | Only stdlib / third-party; no business modules | `shared/crypto`, `shared/date` |
| Integration Adapter | External system boundary | Adapter interface (port) | Own capability module + external SDK | `payment-gateway-adapter/` |
| Domain Extension | Sub-domain specialization | Extension hooks, events | Parent capability public API only | `enterprise-billing/` imports `billing/api` |
| Orchestration / Gateway | Cross-capability coordination | Use case orchestrators | Multiple capability public APIs (read-only fan-in) | `checkout/` imports `orders/api` + `inventory/api` |

### Dependency Direction Enforcement Rules

```
Allowed:
  orders → shared/utils           (business capability → shared technical utility)
  payment-adapter → orders/api    (adapter → capability public API)
  checkout → orders/api           (orchestrator → capability public API)
  checkout → inventory/api        (orchestrator → capability public API)

Forbidden (examples):
  orders → payments               (capability A → capability B: business coupling)
  payments → orders               (capability B → capability A: bidirectional = circular risk)
  orders → orders/internal/db     (external module → private internals: violates encapsulation)
  shared/utils → orders           (shared utility → business capability: inversion)
  payments → checkout             (owned capability → orchestrator: direction inversion)

Dependency Cruiser rule (TypeScript):
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

import-linter contract (Python):
  [importlinter:contract:no-cross-capability]
  name = No cross-capability imports
  type = forbidden
  source_modules = orders
  forbidden_modules = payments
```

### Module Public API Surface Design

```
Module: orders/
  orders/
    api/              ← PUBLIC: everything here is the module's contract
      __init__.py     ← exports: OrderService, CreateOrderCommand, OrderCreatedEvent
      order_service.py
      commands.py
      events.py
    internal/         ← PRIVATE: never imported from outside
      _order_entity.py
      _order_repository.py
      _order_validator.py
    tests/

Rule: external modules may ONLY import from orders/api/
Rule: orders/internal/ is unreachable from outside (enforced by import-linter)
Rule: every new export from orders/api/ requires explicit decision (it is a commitment)
```

# Selection Rules

Select this capability when: the primary concern is **which modules may import which other modules**, business capability isolation, or circular dependency prevention. Route elsewhere when: **layered-architecture-design** is primary (presentation / application / domain / infrastructure layer responsibilities); **microservice-splitting** is primary (the question is whether an in-process boundary should become a separate deployable service); **domain-event-modeling** is primary (inter-module communication via domain events); **extensibility-design** is primary (plugin or extension points across module boundaries).

# Risk Escalation Rules

Escalate when: a proposed import would create a circular dependency; a change moves business logic into a shared utility accessible by multiple unrelated capabilities; a module boundary change requires multiple teams to coordinate and approve; a new module crosses regulated data ownership (GDPR data controller boundaries, PCI cardholder data scope); or the import graph cannot be visualized and enforced because tooling is not in place.

# Critical Details

- **Conway's Law means team structure should inform module boundary decisions.** If two teams must coordinate on every change to Module A, the module boundary is too large — split it along the team boundary. If one team owns a module that two other teams import heavily, dependency coupling will slow all three teams. Module boundaries should minimize the need for cross-team coordination on any single change.
- **"Barrel exports" (index.ts) control public API without changing folder structure.** In TypeScript/JavaScript, an `index.ts` that explicitly re-exports only the public types provides a stable public API without enforcing folder conventions on internal structure. Any internal refactoring that doesn't change the `index.ts` exports is safe. This pattern should be the default for every module.
- **Domain events decouple modules without creating direct imports.** If `orders` needs to notify `inventory` when an order is placed, `orders` publishing an `OrderPlaced` event and `inventory` subscribing to it avoids a direct import in either direction. This is preferable to an orchestrator that imports both. Events must be defined in a shared schema module (not in either business capability module) to avoid the ownership coupling.
- **Test isolation validates module boundary integrity.** If testing Module A requires importing Module B's internals (not its public API), the module boundary is leaky. Each module should be testable in isolation using only its public API and mocks/stubs for dependencies on other modules' public APIs.
- **Module decomposition requires a named relationship.** Splits are not complete until the relationship type and dependency rule are named: sibling, parent-child, producer-consumer, upper-lower layer, orchestrator, adapter/port, or shared technical module. Source/dev-only deep reference for skill authors: `references/module-decomposition.md`.
- **Change locality exposes boundary quality.** If adding one order rule changes `shared/utils`, `payments`, `notifications`, adapters, and tests unrelated to the owning module, the route must decide whether that spread is inherent product behavior or a module-boundary defect.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| `shared/utils/OrderValidation.py` contains order business rules | All importers of shared/utils coupled to order business rules | Move OrderValidation into orders/api; shared/utils contains only pure technical utilities |
| `payments/db/models.py` imported directly by `orders/` | Internal DB model is a cross-module contract; payments schema change breaks orders | Expose `PaymentSummaryDTO` from `payments/api`; orders imports only from payments/api |
| `orders/` → `payments/` → `orders/` circular import | Circular dependency; cannot test either without the other | Break cycle with domain event or shared contract interface |
| No CODEOWNERS for module | Boundary changes happen without owner review | Add CODEOWNERS entry; boundary changes require owner approval |
| All application services in top-level `services/` folder | Zero business capability isolation; every change potentially touches every capability | Reorganize by capability: `orders/application/`, `payments/application/` |
| Import graph not checked in CI | Boundary violations introduced silently in PRs | Add Dependency Cruiser / import-linter to CI; forbidden imports = build failure |

# Failure Modes

- `shared/utils` grows to 12,000 lines and contains business validation logic for orders, payments, and notifications — every capability is coupled to every other capability's business rules through a single import.
- `payments/` imports `orders/internal/OrderRepository` — a refactor of the orders internal persistence layer breaks payments; change requires coordinating two teams; module boundary provides no isolation.
- Circular import: `orders` → `notifications` → `orders` — Python import error at startup; `orders` module partially initialized when `notifications` imports it; runtime `AttributeError` in one of three call paths.
- Module renamed internally (`OrderAggregate` → `OrderEntity`) — since external modules imported `orders/internal/OrderAggregate.ts` directly (not through `orders/api`), all three external importers break.
- No dependency direction enforcement in CI — over 18 months, 47 cross-capability imports accumulate silently; a team attempts to extract `payments` into a microservice and finds 47 import sites to unpick first.
- Shared `PricingCalculator` utility imported by `orders`, `subscriptions`, and `promotions` — a bug fix to promotions pricing logic in the shared utility changes behavior for orders and subscriptions unexpectedly.

# Output Contract

Return a module boundary map with:

- `modules` (name, business capability owned, owning team, public API surface: list of exported types/functions)
- `private_internals` (what is explicitly NOT part of the public API; access from outside is forbidden)
- `allowed_dependencies` (module → module: permitted imports; justified by business or technical reason)
- `forbidden_dependencies` (module → module: prohibited imports; reason; what to use instead)
- `circular_dependency_check` (result of import graph analysis; zero cycles required)
- `enforcement_config` (Dependency Cruiser / import-linter / ArchUnit rule snippets; CI integration)
- `shared_module_audit` (list of items in shared/common/utils; classification: pure technical utility vs. business logic; business logic items must be moved to owning capability)
- `ownership_declaration` (CODEOWNERS entries for each module)
- `cross_boundary_communication` (for each inter-module dependency: direct import via public API, domain event, or orchestrator pattern — justified)
- `directory_density_assessment` (business object families, owners, change rhythms, public APIs, naming clusters, dependency clusters, mixed roles, and file-count signal)
- `module_relationship_type` (sibling / parent-child / producer-consumer / upper-lower layer / orchestrator / adapter-port / shared technical module)
- `change_locality_gate` (owning module, authoritative rule location, extension point, shared/common pressure, cross-module import delta, public API expansion, and small-change spread)
- `migration_impact` (existing code that violates the new boundaries; refactoring plan with priority)
- `test_boundary` (each module testable in isolation using only its public API + mocks for dependencies)

# Quality Gate

The boundary design is complete only when:

1. Every module is defined by a business capability with a named owner.
2. All cross-boundary imports use only the target module's explicit public API (`api/`, `index.ts`, `__all__`).
3. Zero circular dependencies (automated check passes in CI).
4. Dependency direction rules configured in Dependency Cruiser / import-linter / ArchUnit and enforced in CI as a build failure.
5. `shared/` and `common/` modules contain only pure technical utilities — no business logic.
6. Every module can be unit-tested in isolation without importing other capabilities' internals.
7. CODEOWNERS entries declare ownership for every module boundary.
8. Cross-boundary communication pattern (direct import / event / orchestrator) is justified for each dependency.
9. Import graph is visualized and reviewed (Dependency Cruiser `--output-type dot | dot -Tsvg`).
10. Migration plan exists for existing violations.
11. Large directories have a density assessment and are split or justified by one boundary.
12. Every split declares the relationship type and allowed dependency direction.
13. Change locality is checked for small requirements; widespread edits are justified by business behavior or routed to boundary repair.
14. Public API expansion names current consumers and rejects speculative exports.
15. Shared/common remains a pure technical module and is not used to avoid choosing an owner.

# Used By

- architecture-impact-reviewer
- backend-change-builder
- domain-impact-modeler
- frontend-change-builder
- ai-code-review-refactor

# Handoff

Hand off to `layered-architecture-design` for presentation/application/domain/infrastructure layer responsibilities within each module; `microservice-splitting` if a module boundary should become a deployable service; `domain-event-modeling` for event-based inter-module communication; `extensibility-design` for plugin or extension points at module boundaries.

# Completion Criteria

The capability is complete when **every module boundary is defined by business capability, cross-boundary imports use explicit public contracts, circular dependencies are structurally prevented by automated tooling running in CI, shared utilities contain no business logic, and every boundary has a named owner with CODEOWNERS enforcement**.

# Used By

- architecture-impact-reviewer
- backend-change-builder
- ai-code-review-refactor

# Handoff

Hand off to layered-architecture-design for layer responsibilities, architecture-style-selection for overall style choice, or data-model-design when persistence ownership is unresolved.

# Completion Criteria

The capability is complete when module boundaries reflect business capability, avoid circular dependencies, and make coupling visible enough to enforce.
