# Module Decomposition

Use this reference when a directory, package, module, shared area, public API, or import graph grows unclear. It is loaded for architecture-design, implementation-planning, code-review, and refactoring when module density, split relationship, or change locality is in question.

## Directory Module Density Decision Tree

1. Name the directory boundary.
   - Business capability, feature, layer, adapter, generated-code boundary, technical utility, or test boundary.
   - If the directory is only "where files of this type live," verify whether it is an intentional layer convention rather than a module boundary.

2. Check business object families.
   - One object family with cohesive variants: keep.
   - Multiple families such as cancellation, refund, shipping, invoice, entitlement, and notification: split into submodules or sibling modules.

3. Check ownership.
   - One owner or team can approve boundary changes: keep.
   - Multiple owners or review paths: split or declare public contracts between owners.

4. Check change rhythm.
   - Files changing together for the same reasons: keep.
   - Files changing independently or causing unrelated merge conflicts: split by change rhythm.

5. Check public APIs.
   - One explicit API surface: keep.
   - Multiple unrelated public APIs or barrels: split or introduce submodule API entry points.

6. Check naming and dependency clusters.
   - File names and imports cluster around one concept: keep.
   - Obvious clusters form around multiple concepts or dependency sets: split along those clusters.

7. Check role mixing.
   - A module may contain api/internal/domain/adapter/test structure when all serve one capability.
   - A directory mixing unrelated api, internal, domain, adapter, job, infra, helper, fixture, and generated code is a boundary smell.

8. Interpret file count.
   - A large directory is not automatically wrong.
   - Many files are a split signal when they reveal multiple owners, public APIs, object families, dependency clusters, or change rhythms.

## Module Relationship Decision Tree

Every split must declare its relationship type:

1. Sibling modules.
   - Peer capabilities at the same level.
   - They do not import each other's internals.
   - Communication uses public APIs, events, or an orchestrator.

2. Parent-child modules.
   - Parent owns the public capability API.
   - Child modules encapsulate internal sub-capabilities.
   - External consumers depend on the parent or explicit child public API, never child internals by accident.

3. Producer-consumer modules.
   - Producer emits events, messages, schemas, files, or records.
   - Consumer reads the contract, not producer internals.
   - Schema owner, versioning, idempotency, and replay behavior must be declared.

4. Upper-lower layer modules.
   - Upper layer orchestrates or presents behavior.
   - Lower layer owns domain, persistence, or infrastructure details according to local architecture.
   - Dependency direction is one-way and tool-enforced where possible.

5. Orchestrator module.
   - Coordinates multiple capabilities for a use case.
   - Depends only on public APIs of those capabilities.
   - Must not become a hidden owner of their business rules.

6. Adapter/port module.
   - Isolates external systems, protocols, SDKs, file formats, persistence, queues, or framework APIs.
   - Exposes a stable port or adapter contract to the owning module.

7. Shared technical module.
   - Contains pure technical utilities only.
   - No domain vocabulary, business rules, tenant/order/payment/permission logic, or test fixtures with business ownership.
   - Every public export needs real consumers.

## Change Locality Gate

Use this gate before approving module splits, shared utilities, public API expansion, or small changes that spread widely.

1. Owning module.
   - A new rule should have one authoritative owning module.
   - If a requirement changes shared/common, multiple features, and several adapters, distinguish business necessity from bad ownership.

2. Extension point.
   - A new variant should enter through a declared extension point.
   - If adding one variant requires editing switch statements in many modules, the extension point is immature.

3. Shared/common pressure.
   - Shared/common is not a workaround for uncertain ownership.
   - If a shared utility contains domain terms, move it to the owning module or expose a public capability API.

4. Cross-module imports.
   - New imports across modules require public API use and dependency-direction review.
   - Cross-module internal imports are boundary defects.

5. Public API expansion.
   - Public exports are commitments.
   - Add exports only for real current consumers and document consumers.

6. Small change spread.
   - If a small requirement touches many unrelated modules, record one of:
     - business behavior truly spans those modules;
     - module boundary is wrong and requires refactoring;
     - temporary compatibility branch with owner and expiry;
     - rejected implementation.

## Module Split Evidence Record

Record:

- Directory boundary name and owner.
- File/object families detected.
- Naming clusters and dependency clusters.
- Public APIs before and after.
- Relationship type: sibling, parent-child, producer-consumer, upper-lower, orchestrator, adapter/port, shared technical.
- Allowed and forbidden dependencies.
- Change locality assessment.
- Shared/common audit.
- Test directory and fixture ownership impact.
- Migration or refactor plan for existing imports.
