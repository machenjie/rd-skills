---
name: implementation-structure-design
description: Designs implementation structure before code is written by forcing reuse, extension, composition, object modeling, encapsulation, inheritance, helper, class, file, directory, dependency-direction, shared-utility, and test-placement decisions for every code change.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "101"
changeforge_version: 0.1.0
---

# Mission

Design the internal implementation structure of every code change before writing or modifying code: decide whether to reuse an existing function, class, module, service, repository, hook, or component; extend an existing abstraction; compose it; wrap it with an adapter; model behavior as an object with identity, value semantics, encapsulated state, invariants, lifecycle, and collaborators; extract a helper; create a new function; create a new class; create a new file; or create a new directory while preserving local architecture conventions, dependency direction, cohesion, testability, and long-term maintainability.

The goal is to make every implementation look like it belongs in the codebase, not like an isolated AI-generated patch.

# When To Use

Use whenever code is added, moved, extracted, or reorganized, including:

- Adding a new function, method, class, component, hook, service, repository, adapter, command handler, job, validator, parser, mapper, DTO, or helper.
- Deciding where a new behavior should live.
- Deciding whether a concept should be represented as a domain object, value object, service object, adapter, strategy, plain data record, function, or module-level operation.
- Considering inheritance, subclassing, abstract base classes, traits, interfaces, protocols, polymorphic variation, or object collaboration boundaries.
- Modifying an existing function or class when responsibility boundaries are unclear.
- AI-generated code proposes a new abstraction, utility, file, directory, or helper.
- An agent-assisted change needs proof that reuse search and placement rationale happened before new structure was accepted.
- Similar logic already exists somewhere in the codebase.
- A change could be implemented by reuse, extension, composition, extraction, or new code.
- A file starts accumulating mixed responsibilities.
- A function or class becomes hard to name because its responsibility is unclear.

# Do Not Use When

Do not use for pure formatting changes, comment-only edits, or existing code review where no structural decision is needed.

Do not use to justify speculative abstractions. If there is only one current use case, prefer a concrete local implementation unless there is a current, explicit requirement for extension.

Do not wrap procedural code in objects merely to make it look structured. Do not introduce inheritance for code sharing alone.

# Non-Negotiable Rules

- Search before adding. Before creating any new function, class, file, or directory, inspect existing nearby code and project-wide equivalents. Adding duplicate logic without checking existing code is rejected.
- Reuse before abstraction. Prefer direct reuse of an existing function, class, or module when semantics match. Prefer composition over inheritance. Prefer a small local helper over a new shared abstraction.
- Object thinking comes before class creation. First decide whether there is a real object responsibility: identity, value semantics, lifecycle, state, invariant, policy, protocol role, or collaboration boundary. A class is only one possible implementation vehicle.
- Encapsulation protects invariants, not arbitrary code. Keep state mutation private or internal by default, expose behavior-oriented methods, and reject objects that only hide procedural helper calls behind getters, setters, or generic manager methods.
- Inheritance is exceptional. Use it only for a true substitutable type hierarchy, framework-required extension point, or protocol conformance with current variants and contract tests. Prefer composition, delegation, strategy, or explicit interfaces when variation is behavioral rather than taxonomic.
- No business logic in shared, common, or utils. Shared utilities may contain pure technical utilities only. Business logic belongs to the owning module or domain capability.
- New functions need a single responsibility and a natural name. If a function name needs "and", "or", "manager", "helper", "misc", "common", or "util", the responsibility is probably unclear.
- New classes require state, lifecycle, dependency injection, invariants, polymorphism, or protocol conformance. Do not create a class when a pure function or existing service method is sufficient.
- New files require a cohesive owner. A file should group closely related behavior. Do not create one-file-per-function unless the local codebase already follows that pattern.
- New directories require a boundary. A directory must represent a business capability, layer, adapter, feature, or generated-code boundary, not a dumping ground.
- Private stays private. If code is used only inside one module, keep it private or internal. Do not export it just in case.
- Dependency direction must not change accidentally. New imports must respect module boundary and layered architecture rules.
- Tests follow the structure. Tests must be placed next to the unit, module, or integration boundary according to project convention and must prove the selected structure is usable through public APIs, not internals.
- Structure decisions must be attachable to execution evidence. When the change is agent-assisted, the plan must be referenced from the Execution Discipline Report rather than left as an implicit reviewer assumption.

# Industry Benchmarks

Anchor against: domain-driven design module ownership and bounded context rules; layered architecture dependency direction; Clean Architecture dependency inversion; SOLID principles with special attention to single responsibility, interface segregation, and Liskov substitutability; Tell Don't Ask and Law of Demeter object-collaboration heuristics; Gang of Four composition-over-inheritance guidance; Martin Fowler refactoring catalog for extract, move, inline, introduce parameter object, and replace inheritance with delegation decisions; Google Engineering Practices code review guidance for readability, complexity, and local consistency; Architecture Decision Records for non-trivial structure decisions; dependency graph tools such as ArchUnit, Dependency Cruiser, Nx project graph, Bazel visibility, Pants dependency inference, and Go package boundaries; Testing Library and xUnit conventions for behavior-oriented tests placed at the observable boundary.

# Selection Rules

Select this capability when an implementation needs a placement decision before code is written or accepted. Use it with:

- `backend-change-builder` for service, repository, controller, validator, job, mapper, transaction, and domain logic placement.
- `frontend-change-builder` for component, hook, state, API client, form validator, route, and shared UI placement.
- `architecture-impact-reviewer` and `module-boundary-design` when placement could alter module boundaries or dependency direction.
- `ai-code-review-refactor` and `code-review` when generated code adds helpers, utilities, abstractions, files, directories, or imports without local-pattern evidence.
- `refactoring` when behavior-preserving movement needs a target structure before extraction, move, split, inline, or collapse steps.

Prefer adjacent capabilities when the main question is broader: `module-boundary-design` for module ownership and public interfaces, `layered-architecture-design` for layer responsibility, `page-component-decomposition` for UI hierarchy, `service-business-logic` for backend orchestration responsibility, and `refactoring` for behavior-preserving movement after the target structure is chosen.

# Risk Escalation Rules

Escalate to `architecture-impact-reviewer` when the decision adds a new module, directory boundary, public export, cross-layer import, service boundary, shared abstraction, or dependency direction exception.

Escalate to `security-privacy-gate` when placement affects authorization, authentication, tenant isolation, secrets, sensitive data handling, upload processing, or code that could bypass a trust boundary.

Escalate to `data-api-contract-changer` when placement changes public DTOs, API contracts, generated client surfaces, SDK exports, schemas, event payloads, or versioned configuration.

Escalate to `quality-test-gate` when the selected structure cannot be tested through a public behavior boundary or would require brittle tests against private internals.

Escalate to `agent-execution-discipline` when an agent adds structure without documenting reuse search, rejected alternatives, placement rationale, validation result, and closure boundary.

# Critical Details

## Function Decision Tree

```text
Need new behavior?
|-- Does an existing function already implement the same semantic behavior?
|   |-- Yes: Reuse it directly.
|   `-- No
|-- Is there an existing function with the same concept but missing a case?
|   |-- Yes: Extend it only if its responsibility remains single and tests cover old and new behavior.
|   `-- No
|-- Is this behavior private to one file or class?
|   |-- Yes: Add a private or local helper in the same file.
|   `-- No
|-- Is this behavior private to one module?
|   |-- Yes: Add a module-internal function.
|   `-- No
|-- Is this behavior a stable public contract used by multiple modules?
|   |-- Yes: Add to the module public API with compatibility review.
|   `-- No: Keep local; do not export.
```

## Object-Oriented Structure Decision Tree

```text
Considering object-oriented structure?
|-- Is there a real domain object, value object, service object, adapter, strategy, or protocol participant?
|   |-- Yes: Name the role, owner, lifecycle, collaborators, and observable behavior.
|   `-- No: Prefer a function, module operation, or plain data record.
|-- Does the object protect invariants or prevent invalid state transitions?
|   |-- Yes: Encapsulate state mutation and expose behavior-oriented methods.
|   `-- No
|-- Does the object only group stateless helpers or mirror DTO fields with getters/setters?
|   |-- Yes: Reject object; use functions, records, or module-local helpers.
|   `-- No
|-- Are multiple behavior variants required today?
|   |-- Yes: Prefer interface + composition, strategy, or delegation unless taxonomy is real.
|   `-- No: Do not pre-build extension points.
|-- Is inheritance being considered?
|   |-- Yes: Prove substitutability, base-class contract compatibility, initialization safety, and tests for each subtype.
|   `-- No: Keep composition/delegation explicit.
|-- Would callers need to know concrete subclasses or internal state to use it correctly?
|   |-- Yes: Boundary is leaky; redesign interface or keep logic local.
|   `-- No: Object boundary may be accepted with tests through public behavior.
```

Object design is a structural decision, not a naming exercise. A good object has a stable responsibility and protects a useful boundary. A bad object merely scatters procedural logic across classes, hides data bags behind accessors, or creates a hierarchy that future callers must understand to avoid invalid use.

Inheritance must be treated as a public contract. Every subtype must preserve base-class preconditions, postconditions, error behavior, and lifecycle expectations. If inheritance is only used to share helper code, replace it with composition, delegation, extraction, or a private helper.

## Class Decision Tree

```text
Considering a new class?
|-- Does it own mutable state or lifecycle?
|   |-- Yes: Class may be appropriate.
|   `-- No
|-- Does it enforce invariants across multiple operations?
|   |-- Yes: Class, value object, or domain object may be appropriate.
|   `-- No
|-- Does it implement an interface or protocol with multiple concrete implementations today?
|   |-- Yes: Class or strategy may be appropriate.
|   `-- No
|-- Does it only group stateless helper functions?
|   |-- Yes: Reject class; use functions or module-local helpers.
|   `-- Continue
|-- Is it replacing a clear existing service or class?
|   |-- Yes: Extend or compose the existing class.
|   `-- Create only with owner, responsibility, tests, and dependency justification.
```

## File Decision Tree

```text
Need a new file?
|-- Does an existing file already own this responsibility?
|   |-- Yes: Add there unless it would exceed cohesion or readability threshold.
|   `-- No
|-- Is the new logic a private helper for one feature or module?
|   |-- Yes: Add under the module internal or private area.
|   `-- No
|-- Is it a public module contract?
|   |-- Yes: Put under module api, public, or export surface.
|   `-- No
|-- Is it an adapter to external infrastructure?
|   |-- Yes: Put under adapter, infrastructure, or integration area.
|   `-- No
|-- Is it pure shared technical utility?
|   |-- Yes: Put under shared or common only if no business terminology appears.
|   `-- No: Keep in the owning business module.
```

## Directory Decision Tree

```text
Need a new directory?
|-- Does it represent a business capability or bounded context?
|   |-- Yes: Create module or capability directory with owner and public API.
|   `-- No
|-- Does it represent a layer inside an existing module?
|   |-- Yes: Follow existing layer convention.
|   `-- No
|-- Does it represent an external adapter or generated-code boundary?
|   |-- Yes: Create with source-of-truth and regeneration policy.
|   `-- No: Reject directory. Use existing structure.
```

Frontend placement must decide feature-local versus shared for components, hooks, validators, state, API clients, and route code. Avoid turning `components/common`, `hooks`, or `utils` into dumping grounds. Feature-local state must not move to a global store without actual cross-feature ownership.

Backend placement must decide controller, service, domain, repository, adapter, validator, mapper, DTO, and job ownership. Business rules do not belong in transport handlers, generic utilities, or persistence adapters.

# Failure Modes

- New code duplicates an existing function because the implementation skipped local search.
- A shared utility contains business terms such as order, tenant, invoice, booking, cancellation, entitlement, or permission.
- A class is created before deciding the object responsibility, so naming and methods drift toward generic manager, processor, helper, or util behavior.
- Encapsulation hides a data bag behind getters and setters but does not protect invariants or behavior.
- Inheritance is introduced for code reuse without substitutability, base-contract tests, or a real taxonomy.
- A hierarchy forces callers to branch on concrete subclasses, making polymorphism cosmetic and coupling worse.
- A class exists only to group stateless helper functions.
- A new file has no cohesive owner and becomes one-file-per-function drift.
- A new directory is created because the model needed somewhere to put code, not because a real boundary exists.
- A public export is added for code used by only one module.
- A helper is placed in `common` to avoid choosing the owning module.
- A frontend hook spreads feature-local behavior into a global reusable hook with hidden domain assumptions.
- A backend service imports infrastructure directly in a direction the local architecture forbids.
- Tests are placed far from the owning behavior or assert private helpers instead of public behavior.
- Refactoring extracts helpers but leaves duplicated logic and naming drift across modules.

# Output Contract

Return an Implementation Structure Plan for every non-trivial code addition, move, extraction, or reorganization:

- **Existing structure inspected**: files searched; existing functions, classes, modules, services, repositories, hooks, and components considered; reuse candidates; decision.
- **Same-pattern structure scan**: same file, same module, adjacent modules, shared/common/utils, tests, docs, and generated files checked; equivalent patterns listed or explicitly marked absent.
- **Reuse decision**: reuse existing; extend existing; compose existing; adapter needed; new code required; why reuse is insufficient.
- **Function decisions**: new functions; existing functions modified; private or public; responsibility; file location; tests.
- **Object-oriented decisions**: object candidates; object versus function, module operation, or record; identity or value semantics; encapsulated state and invariants; lifecycle; collaborators; composition, delegation, strategy, or inheritance decision; substitutability and contract-test evidence for inheritance; rejected hierarchy or object alternatives.
- **Class decisions**: new classes; existing classes reused or extended; why a class is needed instead of a function; state, invariant, lifecycle, dependency injection, polymorphism, or protocol owned; public or private; tests.
- **File decisions**: files modified; files added; why each new file is needed; owner; public API impact.
- **Directory and module decisions**: directories added; boundary represented; owner; dependency direction; import rules.
- **Shared, common, and utils audit**: any shared utility added; why it is a pure technical utility; confirmation that business logic is absent.
- **Dependency direction**: new imports; allowed by boundary rule; cycles introduced yes or no.
- **Test placement**: unit tests; integration tests; contract tests; confirmation that test location follows project convention.
- **Rejected alternatives**: alternatives considered and why each was rejected for non-trivial structure decisions.
- **Execution linkage**: evidence inventory or handoff reference showing when the structure plan was produced and which validation proves the selected placement works.

# Quality Gate

1. Existing functions, classes, modules, services, repositories, hooks, and components were searched before new code was added.
2. Every new function has single responsibility, natural name, private or public decision, and file location rationale.
3. Every object-oriented structure decision justifies object versus function, module operation, or record.
4. Every new class has a reason that a function is insufficient.
5. Encapsulation choices protect invariants, lifecycle, or collaborator boundaries rather than hiding arbitrary procedural code.
6. Inheritance is avoided unless substitutability, base-contract compatibility, initialization safety, and tests are documented; inheritance for code sharing alone is rejected.
7. Every new file has a cohesive owner and is not a dumping ground.
8. Every new directory represents a real module, layer, adapter, generated boundary, or business capability.
9. No business logic is added to shared, common, or utils.
10. Public API exports are minimal and intentional.
11. New imports respect dependency direction and do not introduce cycles.
12. Tests are placed according to project convention and exercise public behavior.
13. Rejected alternatives are documented for non-trivial structure decisions.
14. Agent-assisted structure additions are tied to execution evidence and handoff boundary.
15. Same-pattern structure scan is documented before adding or moving functions, classes, files, or directories.

# Used By

- backend-change-builder
- frontend-change-builder
- ai-code-review-refactor
- architecture-impact-reviewer
- code-review
- refactoring
- quality-test-gate

# Handoff

Hand off to `module-boundary-design` when ownership or dependency direction is unclear; `layered-architecture-design` when layer responsibility is unclear; `page-component-decomposition` when UI component decomposition is primary; `service-business-logic` when backend service orchestration is primary; `refactoring` when the target structure is chosen and behavior-preserving movement must be sequenced; `code-review` when a completed diff must be assessed against the structure plan.

Hand off to `agent-execution-discipline` when reuse search, placement rationale, same-pattern scan, or validation evidence is missing from an agent-assisted change.

# Completion Criteria

The capability is complete when the implementation has an explicit structure decision before code is written or accepted, all reuse candidates and rejected alternatives are documented, same-pattern structure scan is recorded, new functions/classes/files/directories have ownership and placement rationale, shared utility pollution is ruled out, dependency direction is preserved, and tests are placed at the observable behavior boundary.
