---
name: module-boundary-design
description: Designs module boundaries around business capability, ownership, internal object composition, dependency direction, contracts, and circular dependency prevention.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "19"
changeforge_version: 0.1.0
---

# Mission

Define **module boundaries that protect business capability ownership, cohesive internal object graphs, dependency direction, change isolation, and explicit cross-boundary contracts** — ensuring that each module can be changed, tested, and reasoned about independently, that circular dependencies are structurally impossible, and that the import graph is enforced by automated tooling rather than convention.

# When To Use

Use this capability when a change: adds a new module, package, bounded context, or feature directory; moves code from one module to another; introduces a new import from one module into another (especially across bounded context lines); creates shared utility code that might inadvertently accumulate business logic; proposes merging or splitting an existing module; organizes multiple objects/functions/helpers into a module internal object cluster; or is flagged in review for "circular dependency", "coupling too many modules", "module object graph unclear", or "business logic in shared utility."

# Do Not Use When

Do not use this capability to organize code by technical type alone (e.g., `controllers/`, `services/`, `models/` top-level folders — that is a `layered-architecture-design` concern). Do not use it to create arbitrary folder hierarchies without business ownership, internal object graph, or dependency direction rationale. Do not use it to enforce module boundaries so granular that every object or function lives in an isolated module (boundary cost must be justified by change isolation benefit).

# Stage Fit

Use during architecture planning when module ownership, public contracts, dependency direction, directory density, or split/merge shape is being decided. Use during implementation and review when imports, public exports, shared/common code, or moved files change the module graph. Use during testing and release when boundary enforcement, cycle checks, ownership review, or migration sequencing must prove the design is enforceable. Treat repository graph, project memory, and execution trajectory as discovery inputs only: current source, imports, public exports, owner files, tests, architecture checks, and validation output must confirm or reject that evidence before it supports a boundary decision.

# Non-Negotiable Rules

- **Module boundaries must be defined by business capability, not technical type.** A module named `OrderService` that owns the `Order` business capability (entities, use cases, API, persistence) is correct. A module named `Services` that contains all application services across all capabilities is a layer, not a boundary — it provides no isolation between capabilities.
- **Every cross-boundary import must go through a public contract, not an internal type.** Module A must not import `module-b/internal/OrderRepository` or `module-b/db/models.py`. Module B must expose a public API (`module-b/api/OrderService`, `module-b/api/OrderEvent`) and internal structure must be inaccessible from outside. In Python: `_private` convention + `__all__`; in TypeScript: `index.ts` barrel with explicit exports; in Java: `package-private` classes for internals + public interfaces.
- **Circular dependencies are prohibited.** Module A → Module B → Module A creates: inability to test A without B and B without A; merge conflicts when both teams modify the shared types; infinite import resolution in some runtimes. Circular dependencies must be detected by automated tooling (Dependency Cruiser, import-linter, ArchUnit) and treated as build failures.
- **Shared utilities must not contain business logic.** `shared/`, `common/`, `utils/` modules are dependency magnets. When they accumulate business rules, every module that imports `shared/` becomes coupled to every business rule that `shared/` contains — even unrelated ones. Rule: shared modules may contain only pure technical utilities (date formatting, crypto primitives, HTTP client wrapper). Business rules must live in the owning capability's module.
- **Every module boundary must have a named owner.** A module without an owner has no one to approve boundary changes, no one to maintain the contract, and no one to prevent inappropriate imports. Ownership must be declared (CODEOWNERS file, team annotation, README in module root).
- **Current evidence is mandatory.** A boundary recommendation must cite inspected current source paths, import/dependency graph output, public exports, private internals, owner files, tests, relevant project memory or ADRs with freshness, and validation status. Memory, generated summaries, or old architecture diagrams are selectors, not proof, until reconciled with current source.
- **Dependency direction must be enforced by tooling, not convention.** Architecture decisions decay without automated enforcement. Dependency Cruiser (JavaScript/TypeScript), import-linter (Python), ArchUnit (Java), NDepend (.NET) must run in CI. A PR that introduces a forbidden import must fail CI — not pass and receive a review comment.
- **Module public API surface must be minimal.** Export only what consumers need. Every additional exported type is a surface area that constrains the module's ability to refactor internally. The public API of a module is a commitment to all consumers.
- **Directory size is a module-boundary signal.** A large directory is acceptable only when it still represents one owner, one capability or layer convention, one public API family, and one change rhythm.
- **One directory should represent one module boundary unless it is explicitly a layer or grouping convention.** Mixed business object families, owners, public APIs, dependency clusters, jobs, adapters, domain code, infra, and test helpers require decomposition review.
- **A module is a cohesive object graph plus a public contract, not just a directory.** A module must name its public facade/API, internal domain/value/service/policy/repository/adapter/mapper/helper objects, object relationship graph, internal dependency direction, public/private visibility, module-level tests, and next related change location.
- **Every module split must declare its relationship type.** Use sibling, parent-child, producer-consumer, upper-lower layer, orchestrator, adapter/port, or shared technical module; do not split by arbitrary folder taste.
- **Change locality is a boundary quality gate.** A small requirement should usually change the owning module and its tests; widespread edits require business justification or boundary repair.
- **Public API expansion must be justified by real current consumers.** Do not export types, helpers, or submodule internals "just in case."
- **Shared/common must not become a workaround for poor ownership decisions.** Shared technical modules contain domain-free utilities only and must not host business fixtures or rules.
- **Module public API must not expose internals.** Internal policies, repositories, adapters, mappers, helpers, and concrete child objects remain private unless they are current cross-boundary contracts.

# Industry Benchmarks

Anchor against bounded contexts, package principles, acyclic dependency rules, Team Topologies ownership, modular monolith internal isolation, and import graph enforcement tools such as Dependency Cruiser, import-linter, ArchUnit, and NDepend. Load [references/benchmarks-and-enforcement.md](references/benchmarks-and-enforcement.md) when a design needs the benchmark catalog, boundary classification matrix, dependency-rule snippets, or public API surface example.

# Selection Rules

Select this capability when: the primary concern is **which modules may import which other modules**, business capability isolation, or circular dependency prevention. Route elsewhere when: **layered-architecture-design** is primary (presentation / application / domain / infrastructure layer responsibilities); **microservice-splitting** is primary (the question is whether an in-process boundary should become a separate deployable service); **domain-event-modeling** is primary (inter-module communication via domain events); **extensibility-design** is primary (plugin or extension points across module boundaries).

# Proactive Professional Triggers

- **Signal:** A new import crosses a capability, module, internal path, or shared/common path. **Hidden risk:** import graph drift, cycle creation, or private internals becoming a contract. **Required professional action:** inspect current graph, public API, owner, and enforcement rule before accepting the import. **Route to:** `repository-graph-analysis`, `architecture-enforcement-tooling`, `quality-test-gate`, this capability. **Evidence required:** changed import paths, graph or cycle output, public API decision, enforcement command.
- **Signal:** Code is moved, split, merged, or placed into `shared/`, `common/`, `utils/`, a feature directory, or a new module. **Hidden risk:** arbitrary directory boundary, shared business logic, or change locality degradation. **Required professional action:** classify relationship type, owner, next-change location, and rejected placements. **Route to:** `implementation-structure-design`, `code-clarity-maintainability`, this capability. **Evidence required:** moved paths, owner, relationship type, placement rationale, module tests.
- **Signal:** Project memory, an ADR, generated context, or prior trajectory claims a boundary already exists or is safe. **Hidden risk:** stale memory hides current cycles, private imports, or unowned modules. **Required professional action:** treat memory as a hypothesis and reconcile it against current source, graph, owners, tests, and validation freshness. **Route to:** `project-memory-governance`, `repository-graph-analysis`, `execution-trajectory-analysis`, this capability. **Evidence required:** memory source/date, accepted and rejected claims, current graph delta.
- **Signal:** A public API, barrel export, DTO, event, SDK contract, or module facade expands. **Hidden risk:** accidental downstream compatibility commitment. **Required professional action:** inventory current consumers, minimize the facade, add contract or boundary tests, and record rollback/deprecation impact. **Route to:** `consumer-impact-analysis`, `contract-testing`, `architecture-impact-reviewer`, this capability. **Evidence required:** consumer inventory, export diff, contract tests, rollback path.
- **Signal:** A small requirement touches many modules, shared code, or tests outside the supposed owner. **Hidden risk:** boundary defect disguised as normal implementation spread. **Required professional action:** decide whether the spread is inherent product behavior or boundary repair. **Route to:** `repository-context-map`, `plan-execution-consistency`, this capability. **Evidence required:** changed path map, owning module, spread rationale, rejected repair or repair plan.

# Reference Loading Policy

- **L1 quick decision:** Use this `SKILL.md` only for ordinary routing, non-negotiable rules, output fields, and completion gates.
- **L2 boundary review:** Load [references/checklist.md](references/checklist.md) when reviewing or drafting a concrete boundary map.
- **L3 benchmark/enforcement depth:** Load [references/benchmarks-and-enforcement.md](references/benchmarks-and-enforcement.md) when benchmark anchors, boundary classification, import-rule snippets, or public API surface examples are needed.
- **L4 decomposition depth:** Load [references/module-decomposition.md](references/module-decomposition.md) when splitting, merging, or validating internal object clusters and relationship types.
- **Example shaping:** Use [examples/example-output.md](examples/example-output.md) only to shape a concise final output, not as a substitute for current repository evidence.

# Risk Escalation Rules

Escalate when: a proposed import would create a circular dependency; a change moves business logic into a shared utility accessible by multiple unrelated capabilities; a module boundary change requires multiple teams to coordinate and approve; a new module crosses regulated data ownership (GDPR data controller boundaries, PCI cardholder data scope); or the import graph cannot be visualized and enforced because tooling is not in place.

# Critical Details

- **Module internal composition is required before boundary change.** A module is complete only when it names its public facade/API, current consumers, private internals, internal domain/value/service/policy/repository/adapter/mapper/helper objects, cohesive object graph, internal dependency direction, cycle check, module-level tests, and next related change location.
- **A split or merge must name the module relationship type.** Use sibling, parent-child, producer-consumer, upper-lower layer, orchestrator, adapter/port, shared technical module, or no-split. Reject splits by technical type, one-module-per-object fragmentation, and merges that expose internals or mix unrelated object families.
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

- `mode_selected` (architecture planning, implementation, review, refactoring, testing/release, or repair)
- `boundary_decision_scope` (new boundary, split, merge, import change, public API change, shared/common audit, or migration repair)
- `source_evidence` (current source paths, import graph, public exports, private internals, owner files, tests, architecture rules, and validation output inspected with freshness limits)
- `graph_memory_execution_validation` (repository graph, project memory/ADR, and execution trajectory claims accepted, rejected, stale, partial, or not verified)
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
- `module_internal_composition` (module owner/capability, cohesive object cluster, grouping rationale, and module-level test boundary)
- `module_object_graph` (internal object/function/helper graph, relationship types, allowed collaboration, and forbidden internal access)
- `module_public_facade` (minimal public API, current consumers, exported commands/queries/events/DTOs/contracts)
- `module_private_internals` (internal domain/value/service/policy/repository/adapter/mapper/helper objects and visibility rules)
- `internal_dependency_direction` (allowed internal imports/calls, forbidden directions, cycle check)
- `module_next_change_location` (where the next related rule, adapter, policy, DTO, mapper, repository, or test change belongs)
- `module_object_cluster_split_or_merge_decision` (split/merge/no-split decision for sub-clusters and object families)
- `module_relationship_type` (sibling / parent-child / producer-consumer / upper-lower layer / orchestrator / adapter-port / shared technical module)
- `change_locality_gate` (owning module, authoritative rule location, extension point, shared/common pressure, cross-module import delta, public API expansion, and small-change spread)
- `boundary_to_validation_map` (each boundary rule mapped to graph check, import rule, owner review, contract test, module test, or release check)
- `evidence_limits_and_unknowns` (uninspected modules, unavailable graph tooling, stale memory, missing owner data, generated artifact exclusions)
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
16. Module internal composition names the public facade, private internals, object graph, dependency direction, and module-level test boundary.
17. A module groups cohesive objects/methods/helpers around one capability or layer; unrelated object families are split or explicitly justified.
18. Internal policies, repositories, adapters, mappers, DTOs, helpers, and concrete child objects do not leak through the public facade unless they are real current contracts.
19. A module split or merge declares object cluster split/merge rationale, next-change location, and dependency-direction impact.
20. Current source, graph, owner, public API, private internals, tests, memory/ADR freshness, and validation output are cited or explicitly marked unavailable.
21. Repository graph, project memory, and execution trajectory evidence is classified as accepted, rejected, stale, partial, or not verified.
22. Every boundary rule has a matching validation action: graph/cycle check, import rule, public API/contract test, owner review, shared audit, module test, or release check.
23. Public API and shared/common changes include current consumer evidence and reject speculative exports or ownership workarounds.
24. Handoff states evidence limits, unknown modules, unavailable tooling, rollback/migration impact, and residual coupling risk.

# Evidence Contract

Do not approve a module boundary from names alone. The minimum evidence set is: current repository paths, current imports or dependency graph, public export surface, private internal paths, owner or review authority, tests that exercise the public facade, shared/common inventory, project memory or ADR freshness if used, and validation commands with outcomes. If graph tooling is missing, state the fallback scan, confidence limit, and the exact rule that still needs automated enforcement.

# Benchmark Coverage

Boundary decisions must map to at least one benchmark anchor: bounded context consistency, common closure/common reuse, acyclic dependencies, Team Topologies ownership, modular monolith isolation, or import graph enforcement. Load the benchmark reference when the decision depends on a named pattern, enforcement snippet, or classification matrix.

# Routing Coverage

Route to this capability whenever module ownership, public/private visibility, cross-module import direction, shared/common pressure, circular dependency risk, module split/merge, directory density, public API expansion, object-cluster cohesion, or change locality is material. Pair with `repository-graph-analysis` for graph evidence, `project-memory-governance` for stale memory claims, `execution-trajectory-analysis` for prior-action freshness, `implementation-structure-design` for placement, and `quality-test-gate` for validation mapping.

# Used By

- architecture-impact-reviewer
- backend-change-builder
- frontend-change-builder
- domain-impact-modeler
- ai-code-review-refactor

# Handoff

Hand off to `layered-architecture-design` for presentation/application/domain/infrastructure layer responsibilities within each module; `microservice-splitting` if a module boundary should become a deployable service; `domain-event-modeling` for event-based inter-module communication; `extensibility-design` for plugin or extension points at module boundaries.

# Completion Criteria

The capability is complete when **every module boundary is defined by business capability, exposes an explicit public contract, describes a cohesive internal object graph, keeps private internals private, names internal dependency direction, prevents circular dependencies with automated tooling, restricts shared/common code to pure technical utilities, names an owner, evaluates directory density, declares the module relationship type, proves change locality for small requirements, names the next related change location, and justifies every public API expansion with current consumers**.
