---
name: implementation-structure-design
description: Designs implementation structure before code is written by forcing semantic naming, reuse, extension, composition, object modeling, encapsulation, inheritance, method/class/function/file/directory placement, dependency-direction, shared-utility, and test-placement decisions for every code change.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "101"
changeforge_version: 0.1.1
---

# Mission

Design the internal implementation structure of every code change before writing or modifying code: decide how variables, functions, methods, classes, files, and directories should be named; whether to reuse an existing function, class, module, service, repository, hook, or component; extend an existing abstraction; compose it; wrap it with an adapter; model behavior as an object with identity, value semantics, encapsulated state, invariants, lifecycle, and collaborators; place behavior on a class, service, module function, adapter, or local helper; create a new function; create a new class; create a new file; or create a new directory while preserving local architecture conventions, dependency direction, cohesion, testability, and long-term maintainability.

The goal is to make every implementation look like it belongs in the codebase, not like an isolated AI-generated patch.

# When To Use

Use whenever code is added, moved, extracted, or reorganized, including:

- Adding a new function, method, class, component, hook, service, repository, adapter, command handler, job, validator, parser, mapper, DTO, or helper.
- Adding or renaming a variable, parameter, field, function, method, class, component, hook, service, repository, adapter, command handler, job, validator, parser, mapper, DTO, or helper.
- Deciding where a new behavior should live.
- Deciding whether a name should express a business concept, UI component, technical module, infrastructure adapter, helper, utility, public contract, or local implementation detail.
- Deciding whether a concept should be represented as a domain object, value object, service object, adapter, strategy, plain data record, function, or module-level operation.
- Considering inheritance, subclassing, abstract base classes, traits, interfaces, protocols, polymorphic variation, or object collaboration boundaries.
- Modifying an existing function or class when responsibility boundaries are unclear.
- AI-generated code proposes a new abstraction, utility, file, directory, or helper.
- An agent-assisted change needs proof that reuse search and placement rationale happened before new structure was accepted.
- Similar logic already exists somewhere in the codebase.
- A change could be implemented by reuse, extension, composition, extraction, or new code.
- A file starts accumulating mixed responsibilities.
- A function or class becomes hard to name because its responsibility is unclear.
- A name includes vague buckets such as `common`, `shared`, `helper`, `util`, `manager`, `processor`, `module`, `component`, or `feature` without a concrete ownership reason.

# Do Not Use When

Do not use for pure formatting changes, comment-only edits, or existing code review where no structural decision is needed.

Do not use to justify speculative abstractions. If there is only one current use case, prefer a concrete local implementation unless there is a current, explicit requirement for extension.

Do not wrap procedural code in objects merely to make it look structured. Do not introduce inheritance for code sharing alone.

# Stage Fit

Owns implementation-planning; also informs coding, code-review, and refactoring. Per-stage focus:

- **implementation-planning**: reuse ladder, naming, object/function/file/directory placement, visibility, test placement.
- **coding**: keep new structure minimal and follow the planned boundaries and dependency direction.
- **code-review / refactoring**: check reuse, placement, and dependency direction against the plan.

# Non-Negotiable Rules

- Search before adding. Before creating any new function, class, file, or directory, inspect existing nearby code and project-wide equivalents. Adding duplicate logic without checking existing code is rejected.
- Reuse before abstraction. Prefer direct reuse of an existing function, class, or module when semantics match. Prefer composition over inheritance. Prefer a small local helper over a new shared abstraction.
- Names are architecture. A name must reveal owner, concept, role, and boundary. Vague names hide misplaced responsibilities and must be treated as structure defects, not cosmetic issues.
- Repository vocabulary wins. Prefer existing project terms over generic names. Do not invent a synonym for an established domain, component, module, API, or infrastructure concept.
- Language convention wins for casing and visibility. Naming style must follow the repository and selected language conventions; use `language-idiom-enforcement` for language-specific casing, export, doc-comment, and public API rules.
- Variables name the value they hold, not the type alone. Avoid `data`, `item`, `obj`, `info`, `tmp`, `result`, or `value` unless the scope is tiny and the value is obvious.
- Functions and methods name behavior. Use verb-oriented names for actions and predicate names for boolean checks.
- Method placement requires object responsibility. A method belongs on a class only when it uses or protects that class's state, invariant, lifecycle, collaborator boundary, or protocol role.
- Object thinking comes before class creation. First decide whether there is a real object responsibility: identity, value semantics, lifecycle, state, invariant, policy, protocol role, or collaboration boundary. A class is only one possible implementation vehicle.
- Encapsulation protects invariants, not arbitrary code. Keep state mutation private or internal by default, expose behavior-oriented methods, and reject objects that only hide procedural helper calls behind getters, setters, or generic manager methods.
- Inheritance is exceptional. Use it only for a true substitutable type hierarchy, framework-required extension point, or protocol conformance with current variants and contract tests. Prefer composition, delegation, strategy, or explicit interfaces when variation is behavioral rather than taxonomic.
- No business logic in shared, common, or utils. Shared utilities may contain pure technical utilities only. Business logic belongs to the owning module or domain capability.
- New functions need a single responsibility and a natural name. If a function name needs "and", "or", "manager", "helper", "misc", "common", or "util", the responsibility is probably unclear.
- New classes require state, lifecycle, dependency injection, invariants, polymorphism, or protocol conformance. Do not create a class when a pure function or existing service method is sufficient.
- Class names must identify a real role. Generic `Manager`, `Processor`, `Handler`, `Helper`, or `Util` names require explicit rejection or justification.
- New files require a cohesive owner. A file should group closely related behavior. Do not create one-file-per-function unless the local codebase already follows that pattern.
- File names must match cohesive ownership.
- New directories require a boundary. A directory must represent a business capability, layer, adapter, feature, or generated-code boundary, not a dumping ground.
- Directory names must represent boundaries.
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
- `language-idiom-enforcement` when naming decisions require language-specific casing, visibility, export, package, namespace, doc-comment, or public API convention checks.
- `ai-code-review-refactor` and `code-review` when generated code adds helpers, utilities, abstractions, objects, hierarchies, files, directories, or imports without local-pattern evidence.
- `refactoring` when behavior-preserving movement needs a target structure before extraction, move, split, inline, or collapse steps.

Prefer adjacent capabilities when the main question is broader: `module-boundary-design` for module ownership and public interfaces, `layered-architecture-design` for layer responsibility, `page-component-decomposition` for UI hierarchy, `service-business-logic` for backend orchestration responsibility, and `refactoring` for behavior-preserving movement after the target structure is chosen.

# Risk Escalation Rules

Escalate to `architecture-impact-reviewer` when the decision adds a new module, directory boundary, public export, cross-layer import, service boundary, shared abstraction, class hierarchy, inheritance relationship, polymorphic interface, object collaboration boundary, or dependency direction exception.

Escalate to `security-privacy-gate` when placement affects authorization, authentication, tenant isolation, secrets, sensitive data handling, upload processing, or code that could bypass a trust boundary.

Escalate to `data-api-contract-changer` when placement changes public DTOs, API contracts, generated client surfaces, SDK exports, schemas, event payloads, or versioned configuration.

Escalate to `quality-test-gate` when the selected structure cannot be tested through a public behavior boundary or would require brittle tests against private internals.

Escalate to `agent-execution-discipline` when an agent adds structure without documenting reuse search, rejected alternatives, placement rationale, validation result, and closure boundary.

# Critical Details

The full discovery protocol, decision trees, and record templates live in this capability's `references/` (loaded in the dev profile and by skill authors). The body below carries the decision-critical rules compiled into every consuming professional skill. Resolve every structure decision under five questions: naming, reuse and placement, object modeling, placement boundaries, and shared-utility pollution.

## Reuse & Placement

Discover local convention before adding or renaming anything: inspect the same file, same directory, parent module, sibling modules, tests, and generated/registry files in that order, and treat shared/common/utils as a last resort only after proving the behavior is domain-free. Record files inspected, detected naming/test/placement conventions, reuse candidates found, and rejected locations.

Choose the first valid reuse-ladder level and reject new code when a lower-cost level fits:

1. Direct reuse of an existing function, method, class, component, hook, service, repository, adapter, or utility with matching semantics.
2. Same-file extension of a private helper or method when responsibility stays single.
3. Same-module extension without changing old behavior.
4. Backward-compatible public-API extension only when the contract stays coherent.
5. Composition of existing units.
6. Adapter or wrapper only when the call boundary or external shape requires it.
7. Extraction of duplicated or mixed behavior into a clearer private or module-internal abstraction.
8. New code only after every earlier level is rejected with evidence.

Produce a Reuse Ladder Record naming the candidates at each level, the final decision, and why lower-cost levels were insufficient. Source/dev-only deep reference for skill authors: `references/reuse-and-placement.md`.

## Advanced Refactoring & Extension Reuse

Prefer extending the existing owner over a parallel implementation only when responsibility stays single, existing callers keep their behavior, the change is backward compatible, new parameters are optional or a parameter object, no vague `type`/`kind`/`mode`/`flag`/`strategy` switch is added, and tests cover both old and new behavior. Reject extension when the owner would become ambiguous, the case belongs to a different owner, compatibility cannot be proven, the change requires cross-layer imports, or the name would have to become vague.

When refactoring, escalate only as far as needed: inline cleanup, then function extraction, then object extraction (only for real state/invariant/lifecycle/collaborator ownership), then interface or protocol extraction (only with multiple implementations today or a real external test seam), then inheritance (only with proven substitutability, a stable base contract, and per-subtype contract tests), then reflection or metadata dispatch (only when a framework or schema mapping requires it, with a type-safety boundary and a malformed-metadata fallback). Produce an Extension Safety Record and an Advanced Refactoring Decision. Source/dev-only deep reference for skill authors: `references/advanced-refactoring.md`.

## Naming

Names are architecture: a name must reveal owner, concept, role, and boundary, and a vague name is a structure defect, not a cosmetic issue. Prefer existing repository vocabulary over invented synonyms, and follow language convention for casing and visibility through `language-idiom-enforcement`. Variables name the value they hold, functions name behavior, and predicates read as booleans. Classify every name into the narrowest accurate category — business/domain, feature, component, module, service, domain/value object, repository, adapter/client, utility, helper, or common/shared — and reject a category when the behavior does not match it (for example, a `utility` that carries order, tenant, invoice, or permission terms is misclassified domain logic). Source/dev-only deep reference for skill authors: `references/naming.md`.

## Object Modeling

Decide object responsibility before creating a class: identity, value semantics, lifecycle, state, invariant, policy, protocol role, or collaboration boundary. A class is justified only when a function or existing service method is insufficient — it must own state or lifecycle, enforce invariants across operations, implement a protocol with real variants today, or model a domain or value object. Place a method on a class only when it uses or protects that class's state, invariant, lifecycle, or collaborator; otherwise use a service, module function, adapter, or local helper, and never let the method force the object to import infrastructure or UI concerns. Encapsulation must protect invariants, not hide a data bag behind getters and setters. Inheritance is exceptional: use it only for a genuinely substitutable type hierarchy with a stable base contract and per-subtype tests, and never for code sharing alone — prefer composition, delegation, or strategy. Reject generic `Manager`, `Processor`, `Handler`, `Helper`, or `Util` class names unless explicitly justified. Source/dev-only deep reference for skill authors: `references/object-modeling.md`.

## Placement Boundaries

A new file needs a cohesive owner and a convention-compliant name; add to an existing file when it already owns the responsibility, and reject a filename that introduces a new suffix, prefix, pluralization, or layer word the surrounding directory does not use. A new directory must represent a business capability, layer, adapter, feature, or generated-code boundary — never a convenience folder. Keep private code private and do not export "just in case." New imports must respect module-boundary and layered-architecture dependency direction and introduce no cycles. Frontend placement decides feature-local versus shared for components, hooks, validators, state, API clients, and routes; feature-local state does not move to a global store without real cross-feature ownership. Backend placement decides controller, service, domain, repository, adapter, validator, mapper, DTO, and job ownership; business rules never live in transport handlers, generic utilities, or persistence adapters. Source/dev-only deep reference for skill authors: `references/placement-boundaries.md`.

## Shared-Utility Pollution

Shared, common, and utils packages may hold pure technical, domain-free utilities only. Business logic — order, tenant, invoice, booking, cancellation, entitlement, permission, workflow, or any other domain term — belongs to the owning module or domain capability, never to a shared bucket used to avoid choosing an owner. A helper placed in `common` to dodge the ownership decision is a structure defect. Audit every shared utility added: confirm it is domain-free and that no business vocabulary appears in its name or body.

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
- **Vocabulary and naming decisions**: variable, parameter, field, function, method, class, file, directory, package, namespace, component, hook, service, repository, adapter, utility, and helper naming decisions; repository convention followed; rejected names and why.
- **Responsibility taxonomy**: classify each new or moved item as business/domain, feature, component, module, service, domain object, repository, adapter/client, utility, helper, common/shared, test, generated, or configuration; explain owner and boundary.
- **Function decisions**: new functions; existing functions modified; private or public; responsibility; file location; tests.
- **Method decisions**: new methods; existing methods modified or moved; owning class rationale; state/invariant/lifecycle/collaborator usage; rejected service/function alternatives.
- **Object-oriented decisions**: object candidates; object versus function, module operation, or record; identity or value semantics; encapsulated state and invariants; lifecycle; collaborators; composition, delegation, strategy, or inheritance decision; substitutability and contract-test evidence for inheritance; rejected hierarchy or object alternatives.
- **Class decisions**: new classes; existing classes reused or extended; why a class is needed instead of a function; state, invariant, lifecycle, dependency injection, polymorphism, or protocol owned; public or private; tests.
- **File decisions**: files modified; files added; why each new file is needed; owner; public API impact.
- **Directory and module decisions**: directories added; boundary represented; owner; dependency direction; import rules.
- **Shared, common, and utils audit**: any shared utility added; why it is a pure technical utility; confirmation that business logic is absent.
- **Dependency direction**: new imports; allowed by boundary rule; cycles introduced yes or no.
- **Test placement**: unit tests; integration tests; contract tests; confirmation that test location follows project convention.
- **Rejected alternatives**: alternatives considered and why each was rejected for non-trivial structure decisions.
- **Execution linkage**: evidence inventory or handoff reference showing when the structure plan was produced and which validation proves the selected placement works.
- **Comment decisions**:
  - exported/public declarations requiring doc comments;
  - non-exported complex functions/classes/methods requiring comments;
  - tests requiring scenario/regression comments;
  - critical internal logic requiring inline comments;
  - comments intentionally omitted because naming and local context are sufficient;
  - redundant comments removed;
  - comment style matched to language and repository convention.

# Quality Gate

1. Existing variables, functions, classes, modules, services, repositories, hooks, and components were searched before new code was added.
2. Every new or changed non-trivial variable, parameter, field, function, method, class, file, and directory name follows repository vocabulary, language convention, and semantic responsibility.
3. Every new function has single responsibility, natural name, private or public decision, and file location rationale.
4. Every new method has owning-class rationale and uses or protects object state, lifecycle, invariants, collaborators, or protocol role.
5. Every object-oriented structure decision justifies object versus function, module operation, or record.
6. Every new class has a reason that a function is insufficient and avoids vague manager/processor/helper/util naming unless explicitly justified.
7. Encapsulation choices protect invariants, lifecycle, or collaborator boundaries rather than hiding arbitrary procedural code.
8. Inheritance is avoided unless substitutability, base-contract compatibility, initialization safety, and tests are documented; inheritance for code sharing alone is rejected.
9. Every new file has a cohesive owner, a convention-compliant name, and is not a dumping ground.
10. Every new directory represents a real module, layer, adapter, generated boundary, feature, or business capability.
11. Business/domain logic is classified and kept out of shared, common, and utils.
12. Public API exports are minimal and intentional.
13. New imports respect dependency direction and do not introduce cycles.
14. Tests are placed according to project convention and exercise public behavior.
15. Rejected alternatives are documented for non-trivial structure decisions.
16. Agent-assisted structure additions are tied to execution evidence and handoff boundary.
17. Same-pattern structure scan is documented before adding, renaming, or moving variables, functions, methods, classes, files, or directories.
18. Every added or renamed file includes same-directory and parent-module naming convention evidence.
19. A new file is rejected when the same responsibility belongs in an existing cohesive file.
20. A filename is rejected when it uses a new suffix, prefix, pluralization, layer word, or abbreviation not used by the surrounding directory without explicit justification.
21. Every new function/class/file/directory includes a Reuse Ladder Record.
22. Every extension of existing logic includes an Extension Safety Record.
23. Every advanced refactor includes an Advanced Refactoring Decision.
24. Every new exported/public function, method, class, interface, struct, component, hook, constant, variable, or module API has a language-standard doc comment.
25. Every non-trivial class/function/method with business rules, state transitions, compatibility behavior, concurrency, retry, transaction, idempotency, external API quirks, performance tradeoff, or security-sensitive logic has concise comments where needed.
26. Every non-trivial test explains the behavior, regression, edge case, fixture contract, or integration scenario being protected.
27. No comment merely restates obvious code.
28. If comments are needed to explain confusing code, the plan first considers renaming, extraction, or simplification.

# Used By

- backend-change-builder
- frontend-change-builder
- ai-code-review-refactor
- architecture-impact-reviewer
- code-review
- refactoring
- quality-test-gate

# Handoff

Hand off to `module-boundary-design` when ownership, public object contract, module API, or dependency direction is unclear; `layered-architecture-design` when layer responsibility is unclear; `architecture-impact-reviewer` when inheritance, class hierarchy, polymorphic interface, or object collaboration boundary affects module or architectural contracts; `page-component-decomposition` when UI component decomposition is primary; `service-business-logic` when backend service orchestration is primary; `refactoring` when the target structure is chosen and behavior-preserving movement must be sequenced; `code-review` when a completed diff must be assessed against the structure plan.

Hand off to `agent-execution-discipline` when reuse search, placement rationale, same-pattern scan, or validation evidence is missing from an agent-assisted change.

# Completion Criteria

The capability is complete when the implementation has an explicit structure decision before code is written or accepted, all reuse candidates and rejected alternatives are documented, same-pattern structure scan is recorded, names follow repository vocabulary and language convention, each new or moved item is classified by responsibility taxonomy, object-oriented decisions justify object versus function/module/record, method placement is justified by state/invariant/lifecycle/collaborator usage, encapsulation and inheritance choices are tested through observable behavior, new functions/classes/files/directories have ownership and placement rationale, shared utility pollution is ruled out, dependency direction is preserved, and tests are placed at the observable behavior boundary.
