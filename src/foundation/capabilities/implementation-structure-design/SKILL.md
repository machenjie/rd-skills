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

## Repository Local Pattern Discovery Protocol

Before adding or renaming any variable, parameter, field, function, method, class, struct, interface, component, hook, service, repository, adapter, helper, utility, file, package, module, or directory, inspect local conventions in this order:

1. Same file:
   - existing helpers;
   - private functions;
   - methods;
   - naming shape;
   - comment style;
   - error handling style;
   - test shape.

2. Same directory:
   - file naming pattern;
   - suffix/prefix convention;
   - public/private split;
   - test file naming;
   - sibling class/function naming;
   - local helper placement.

3. Parent directory or parent module:
   - module ownership;
   - exported API;
   - internal/shared boundary;
   - parent naming pattern;
   - existing package/module style.

4. Sibling modules:
   - equivalent feature/component/service/repository patterns;
   - similar naming and placement decisions.

5. Shared/common/utils:
   - only after proving the behavior is pure technical utility and domain-free;
   - never use shared/common/utils to avoid choosing the owning module.

6. Tests:
   - naming convention;
   - placement convention;
   - test helper/fixture style;
   - test comment style.

7. Generated or registry files:
   - whether new names require index/export/registration updates;
   - generated source-of-truth and regeneration policy.

The Implementation Structure Plan must state:

- files inspected;
- directories inspected;
- existing functions/classes/modules/services/repositories/hooks/components considered;
- detected naming convention;
- detected file naming convention;
- detected test naming convention;
- detected placement convention;
- reuse candidates found;
- rejected locations and why;
- final selected name and location;
- whether comments are required for the new or changed structure.

## Reuse Ladder

When adding behavior, choose the first valid option:

1. Direct reuse:
   - call an existing function, method, class, component, hook, service, repository, adapter, or utility with matching semantics.

2. Same-file extension:
   - extend an existing private helper, local function, or method if responsibility remains single.

3. Same-module extension:
   - extend an existing module-internal function, class, service, repository, adapter, or helper without changing old behavior.

4. Existing public API extension:
   - add a backward-compatible option, overload, parameter object, strategy, or branch only when the public contract remains coherent.

5. Composition:
   - compose existing functions/classes/services into the required behavior.

6. Adapter/wrapper:
   - wrap an existing behavior only when the call boundary, dependency direction, or external API shape requires adaptation.

7. Extraction:
   - extract duplicated or mixed behavior into a clearer private or module-internal abstraction.

8. New code:
   - create a new function/class/file/directory only after all previous levels are rejected with evidence.

Reject new code when an earlier ladder level can satisfy the requirement with lower structural cost.

The plan must include a Reuse Ladder Record:

- direct reuse candidates;
- same-file extension candidates;
- same-module extension candidates;
- existing public API extension candidates;
- composition candidates;
- adapter/wrapper candidates;
- extraction candidates;
- final decision;
- why lower-cost reuse levels were insufficient.

## Extension Reuse Without Behavioral Drift

When an existing function, method, class, service, repository, adapter, component, hook, or module already owns the concept but lacks a case, prefer extending it over creating a parallel implementation only if all conditions hold:

- The original responsibility remains single and naturally named.
- Existing callers keep the same behavior.
- The extension is backward compatible.
- New parameters are optional or represented by a clear parameter object.
- No unrelated mode flags are added.
- No vague `type`, `kind`, `mode`, `flag`, or `strategy` switch is added unless the existing abstraction is already designed for that variation.
- Existing tests still pass.
- New tests cover both old behavior and newly supported behavior.
- Error behavior and edge cases remain compatible.
- The extension does not force the owner to import a forbidden layer.
- The extension does not turn the owner into a generic manager, processor, util, or mixed-responsibility branch pile.

Reject extension reuse when:

- the old function/class would become ambiguous;
- the new case belongs to a different owner;
- compatibility cannot be proven;
- tests cannot cover old and new behavior clearly;
- the extension requires cross-layer imports;
- the name would need to become vague to fit both old and new responsibilities.

The plan must include an Extension Safety Record:

- existing owner;
- missing case being added;
- old behavior preserved or changed;
- compatibility risk;
- tests covering old behavior;
- tests covering new behavior;
- rejected parallel implementation and why;
- confirmation that responsibility remains single.

## Advanced Refactoring Structure Protocol

When refactoring, evaluate these options in order:

1. Inline cleanup:
   - rename;
   - simplify condition;
   - remove duplication inside the same function;
   - reduce nested control flow.

2. Function extraction:
   - extract when a block has a nameable responsibility;
   - keep private if used once or only locally;
   - move to module-internal only when reused by multiple files in the module;
   - do not create a shared utility for one caller.

3. Object extraction:
   Extract a class/object only when at least one is true:
   - it owns state across multiple operations;
   - it protects invariants;
   - it models lifecycle transitions;
   - it coordinates collaborators;
   - it represents a domain object;
   - it represents a value object;
   - it represents a service object;
   - it represents an adapter;
   - it represents a strategy;
   - it represents a protocol participant;
   - it gives a real boundary that a function cannot express clearly.

4. Interface or protocol extraction:
   Extract only when:
   - multiple implementations exist now;
   - a test seam is needed for an external dependency;
   - framework/plugin boundaries require it;
   - dependency inversion removes a real architectural violation;
   - the interface expresses stable behavior rather than one implementation.

5. Inheritance:
   Use only when:
   - subtypes are genuinely substitutable;
   - the base class has a stable contract;
   - initialization and lifecycle are safe;
   - contract tests cover every subtype;
   - callers do not need to branch on concrete subtype;
   - inheritance is not being used merely for helper reuse.

   Reject inheritance when composition, delegation, strategy, or extraction is simpler.

6. Reflection or metadata-driven dispatch:
   Use only when:
   - framework integration requires it;
   - plugin discovery requires it;
   - schema/annotation/metadata mapping avoids repetitive boilerplate safely;
   - compile-time alternatives would create worse duplication or coupling.

   Reflection must include:
   - type-safety boundary;
   - failure behavior;
   - discoverability notes;
   - test coverage;
   - security consideration if inputs influence reflection;
   - fallback when metadata is missing or malformed.

The plan must include an Advanced Refactoring Decision:

- why inline cleanup is insufficient;
- why function extraction is insufficient or sufficient;
- why object/class/interface is justified or rejected;
- state/invariant/lifecycle/collaborator decision;
- composition vs inheritance decision;
- substitutability evidence if inheritance is used;
- reflection safety decision if reflection is used;
- public behavior tests used to prove the refactor.

## Naming Taxonomy

Use the narrowest accurate category. Do not use these words interchangeably:

| Category | Means | Belongs In | Naming Guidance | Reject When |
| --- | --- | --- | --- | --- |
| Business / Domain | Core business concept, rule, invariant, lifecycle, permission, event, or policy | Domain module, application service, use case, policy, state machine | Use business vocabulary from requirements and existing domain model | It is only formatting, parsing, transport, or persistence mechanics |
| Feature | User-visible capability or product workflow slice | Feature module, route/page area, feature-local component/state/tests | Name after the user outcome or workflow, not implementation mechanics | It is reused by unrelated features or has no product behavior |
| Component | UI composition unit with props, slots, state, render behavior, accessibility contract | Feature-local UI folder or design-system/component package | Name by rendered role and product meaning | It contains data access, business rules, or global state ownership |
| Module | Coherent code boundary with owner, public API, allowed dependencies | Module/package directory | Name after owned capability or technical layer | It is just a folder for convenience |
| Service | Application orchestration, use case coordination, transaction boundary, external operation boundary | Application/backend service layer | Name after use case or owned operation | It only wraps one repository call or hides procedural helpers |
| Domain Object / Value Object | Object with identity or value semantics, invariants, lifecycle, or behavior | Domain model | Name after the concept it protects | It is a DTO, record, or getter/setter bag |
| Repository | Persistence boundary and query/write contract | Infrastructure or data access layer behind an interface | Name after aggregate/resource being persisted | It leaks ORM/persistence types into domain logic |
| Adapter / Client | External system, framework, transport, provider, or infrastructure boundary | Infrastructure/integration/adapter directory | Name after external system and role | It contains business rules instead of translation, retry, or failure handling |
| Utility | Pure technical, domain-free helper reused across modules | Shared/common utility package | Name by technical transformation; no business terms | It contains order, tenant, invoice, permission, workflow, or other domain terms |
| Helper | Small local implementation detail private to a file/module | Same file or module-internal area | Prefer private/local names and keep scope narrow | It becomes public, reused widely, or hides a missing domain/service concept |
| Common / Shared | Stable cross-module technical contract or primitive | Shared/common package with clear ownership | Use only for domain-free primitives or intentional public contracts | It is used to avoid choosing the owning module |

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

Object design is a structural decision, not a name-only exercise. A good object name exposes stable responsibility and the boundary it protects. A bad object name such as generic manager, processor, helper, or util usually signals scattered procedural logic, a hidden data bag, or a hierarchy that future callers must understand to avoid invalid use.

Inheritance must be treated as a public contract. Every subtype must preserve base-class preconditions, postconditions, error behavior, and lifecycle expectations. If inheritance is only used to share helper code, replace it with composition, delegation, extraction, or a private helper.

## Method Placement Decision Tree

```text
Considering a method on an existing or new class?
|-- Does the method use or protect object state, invariants, lifecycle, or collaborators?
|   |-- Yes: Method placement may be appropriate.
|   `-- No
|-- Is the method behavior naturally expressed in the object's vocabulary?
|   |-- Yes: Keep near the object if dependency direction allows it.
|   `-- No: Use a service, module function, adapter, or local helper.
|-- Would adding the method force the object to import infrastructure or UI concerns?
|   |-- Yes: Reject; place orchestration in a service or adapter.
|   `-- No
|-- Does it make the class a generic manager/processor/helper?
|   |-- Yes: Split by responsibility or move behavior to the correct owner.
|   `-- No: Accept with tests through public behavior.
```

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
