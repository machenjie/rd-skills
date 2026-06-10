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
- Every new or changed file must have one primary owner or main responsibility; long files, large objects, and unrelated method clusters are structure signals that require split review or justification.
- New functions need a single responsibility and a natural name. If a function name needs "and", "or", "manager", "helper", "misc", "common", or "util", the responsibility is probably unclear.
- A function must have one readable purpose, structured parameters, and explicit return states; boolean flags, weakly typed bags, vague mode/kind switches, and unclear failure/empty/partial returns require signature review.
- Pure decision logic and external side effects must be separated unless a local convention proves the combined boundary is intentional, testable, and contained.
- New classes require state, lifecycle, dependency injection, invariants, polymorphism, or protocol conformance. Do not create a class when a pure function or existing service method is sufficient.
- Class names must identify a real role. Generic `Manager`, `Processor`, `Handler`, `Helper`, or `Util` names require explicit rejection or justification.
- Constructor and collaborator count is responsibility evidence; too many collaborators require object split, orchestration justification, or dependency-boundary cleanup.
- New files require a cohesive owner. A file should group closely related behavior. Do not create one-file-per-function unless the local codebase already follows that pattern.
- File granularity is decided by boundaries, not line count. A large file is not a defect by itself; mixed responsibility is the defect. A small file is not a defect by itself; fragmentation without a boundary is the defect.
- Default to keep in existing file when private helpers, local constants, local types, narrow value objects, owner-internal predicates, and local mappers share the main owner, lifecycle, invariant, collaborator family, and reason to change.
- Every proposed new file must prove at least one true boundary: different primary owner, lifecycle, invariant or state set, collaborator family, side-effect boundary, public contract, change rhythm, test boundary, generated/handwritten boundary, adapter/protocol/repository/client/gateway boundary, or current strategy/policy variants with contract tests.
- Reject anti-fragmentation failures: splitting only to reduce line count, only to test a private helper, one-function file drift, trivial class file drift, pass-through glue files, and any split that makes a business decision require multiple file jumps without an independent owner, lifecycle, public contract, or change reason.
- Do not create a tiny file because it looks more modular, gives a convenient name, shortens a function, lowers file length, makes testing a private helper easier, or avoids deciding the real owner.
- Do not export or publicize a private helper only so tests can import it; test through the owning public behavior unless the helper has a production public or module-internal contract.
- Small files without an independent owner, lifecycle, invariant, collaborator family, public contract, side-effect boundary, test boundary, or change rhythm must be considered for merge back into the unique owner.
- Small files with real boundaries must not be merged merely to reduce file count.
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

The full discovery protocol, decision trees, and record templates live in this capability's `references/` (loaded in the dev profile and by skill authors). The body below carries the decision-critical rules compiled into every consuming professional skill. Resolve every structure decision under six questions: naming, reuse and placement, object and module decomposition, object modeling, placement boundaries, and shared-utility pollution.

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

Professional skills cite the Reuse Ladder Record as evidence, not prose intent: backend attaches service/repository/validator reuse; frontend attaches component/hook/state reuse; AI review marks missing reuse search; test gates verify fixture/helper reuse without private-internal coupling.

## Advanced Refactoring & Extension Reuse

Prefer extending the existing owner over a parallel implementation only when responsibility stays single, existing callers keep their behavior, the change is backward compatible, new parameters are optional or a parameter object, no vague `type`/`kind`/`mode`/`flag`/`strategy` switch is added, and tests cover both old and new behavior. Reject extension when the owner would become ambiguous, the case belongs to a different owner, compatibility cannot be proven, the change requires cross-layer imports, or the name would have to become vague.

When refactoring, escalate only as far as needed: inline cleanup, then function extraction, then object extraction (only for real state/invariant/lifecycle/collaborator ownership), then interface or protocol extraction (only with multiple implementations today or a real external test seam), then inheritance (only with proven substitutability, a stable base contract, and per-subtype contract tests), then reflection or metadata dispatch (only when a framework or schema mapping requires it, with a type-safety boundary and a malformed-metadata fallback). Produce an Extension Safety Record and an Advanced Refactoring Decision. Source/dev-only deep reference for skill authors: `references/advanced-refactoring.md`.

## Naming

Names are architecture: a name must reveal owner, concept, role, and boundary, and a vague name is a structure defect, not a cosmetic issue. Prefer existing repository vocabulary over invented synonyms, and follow language convention for casing and visibility through `language-idiom-enforcement`. Variables name the value they hold, functions name behavior, and predicates read as booleans. Classify every name into the narrowest accurate category — business/domain, feature, component, module, service, domain/value object, repository, adapter/client, utility, helper, or common/shared — and reject a category when the behavior does not match it (for example, a `utility` that carries order, tenant, invoice, or permission terms is misclassified domain logic). Source/dev-only deep reference for skill authors: `references/naming.md`.

## Object Modeling

Decide object responsibility before creating a class: identity, value semantics, lifecycle, state, invariant, policy, protocol role, or collaboration boundary. A class is justified only when a function or existing service method is insufficient — it must own state or lifecycle, enforce invariants across operations, implement a protocol with real variants today, or model a domain or value object. Place a method on a class only when it uses or protects that class's state, invariant, lifecycle, or collaborator; otherwise use a service, module function, adapter, or local helper, and never let the method force the object to import infrastructure or UI concerns. Encapsulation must protect invariants, not hide a data bag behind getters and setters. Inheritance is exceptional: use it only for a genuinely substitutable type hierarchy with a stable base contract and per-subtype tests, and never for code sharing alone — prefer composition, delegation, or strategy. Reject generic `Manager`, `Processor`, `Handler`, `Helper`, or `Util` class names unless explicitly justified. Source/dev-only deep reference for skill authors: `references/object-modeling.md`.

Choose value object for value-owned equality/validation/normalization/unit safety; domain object for identity/lifecycle/invariants/state transitions; service for collaborator coordination; adapter for external protocol translation; strategy for multiple current algorithms behind a stable interface; module function or local helper for stateless local behavior. Do not create a class just to group functions, make testing easier, or imitate enterprise style.

Reflection or metadata dispatch is allowed only when a framework, schema, plugin protocol, or generated mapping requires it, with typed boundary, malformed-metadata fallback, explicit default behavior, and invalid-metadata tests.

## Object, Signature, And Side-Effect Decomposition

Every file needs one main owner, one primary lifecycle or responsibility, and one coherent collaborator set. Long files, large objects, unrelated method clusters, constructor bloat, and branch-heavy functions are evidence to inspect; line count alone is not the decision. Functions need one readable purpose, structured parameters, clear return contracts, and explicit failure/empty/partial states. Pure calculations, business decisions, state mutation, persistence, external calls, events, logging, metrics, and cache access must be classified so policy and domain code stay testable without infrastructure. Source/dev-only deep reference for skill authors: `references/object-module-decomposition.md`.

A file or directory split is justified by mixed owners, lifecycles, collaborators, reasons to change, layers, adapter protocols, generated/handwritten code, or tests that cannot find their owning behavior; line count alone is only a signal.

## File Granularity And Anti-Fragmentation

Apply anti-fragmentation before accepting any new file. File granularity is determined by owner and boundary, not by line count. Large files are not automatically a problem; mixed responsibility is the problem. Small files are not automatically a problem; fragmentation without a real boundary is the problem.

The default is co-location: keep tightly related private helpers, local constants, local types, narrow value objects, predicates, and owner-internal mappers in the main owner file when they serve one owner, lifecycle, invariant set, collaborator family, and reason to change. A main owner file plus private helpers is a valid structure.

Create a new file only when the split names a real boundary: different primary owner, different lifecycle, different invariant or state set, different collaborator family, different side-effect boundary, different public contract, different change rhythm, different test boundary, generated versus handwritten code, adapter/protocol/repository/client/gateway boundary, or current strategy/policy variants with contract tests. The boundary must explain why the keep in existing file alternative was rejected.

Reject these splits: "looks more modular"; reducing line count alone; lowering function length alone; naming convenience alone; avoiding owner analysis; exposing or extracting private helpers only to test them; one tiny function per file; one trivial class per file; pass-through policy/helper/adapter glue; splitting constants or options used only by one owner; and any micro-file sprawl that makes a reader jump across several files to understand one business decision.

File granularity must improve or preserve navigation cost. If the next maintainer must open more files to understand the same cohesive rule, the split is a navigation cost regression unless a real boundary offsets that cost and the tradeoff is recorded.

## Small File Merge And Merge Restraint

Consider small file merge back into the unique owner when a file contains only one tiny private function, trivial class, local predicate, local mapper, constant group, or pass-through glue; is used by only one owner file; has no independent owner, lifecycle, invariant, collaborator family, public contract, side-effect boundary, test boundary, or change rhythm; repeats the owner concept in its filename; makes one business decision require multiple file jumps; exists only so tests can target private helper logic; and merging would reduce import/export surface, lower navigation cost, and make the next-change location clearer.

Reject merging a small file when it has a public API/export, adapter/client/gateway/repository/protocol/generated-code boundary, independent value-object invariant, independent lifecycle or state machine, multiple legitimate current consumers, current strategy/policy variants with contract tests, independent public behavior test boundary, dependency-direction protection, visible side effects, or a separate owner that would make the target file mixed-responsibility if combined.

Merge restraint is as important as anti-fragmentation. Do not collapse adapter code into services, value-object invariants into procedural owners, policy variants into orchestration methods, or side-effect boundaries into pure decision files just to reduce file count. A split merge decision is accepted only when the resulting owner is clearer, dependency direction is preserved, public contracts remain intact, side effects stay visible, and main-flow readability improves or stays no worse.

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
- Excessive file split creates micro-file sprawl: one-function file, trivial helper file, owner-internal mapper/options file, or pass-through policy/helper/adapter file without independent owner, lifecycle, public contract, or change reason.
- Navigation cost regresses because understanding one business decision requires several file jumps with no real boundary payoff.
- A one-function file exists without a boundary beyond naming convenience.
- A trivial class file has no state, invariant, lifecycle, protocol role, or current variant contract.
- A private helper is exported only so tests can import it.
- A small owner-internal file remains separate even though it should merge back into the unique owner.
- A reckless file merge hides a real boundary to reduce file count.
- A lost small-file boundary removes a valid public contract, side-effect boundary, value-object invariant, policy test boundary, or dependency-direction protection.
- An adapter/client/gateway/repository file is merged into a service and hides side effects.
- A value object invariant is merged into a procedural owner and loses explicit protection.
- A policy with contract tests is merged into an orchestration method.
- Fewer files produce a worse main flow, less obvious next-change location, or mixed responsibility.
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
- **Reuse ladder and professional-skill evidence**: how the substantive skill will cite reuse, extension, composition, adapter, extraction, or new-code decisions in its Evidence Contract.
- **Vocabulary, naming, and responsibility taxonomy**: variable, parameter, field, function, method, class, file, directory, package, namespace, component, hook, service, repository, adapter, utility, helper, common/shared, test, generated, and configuration decisions; repository convention followed; owner and boundary explained.
- **Function and method decisions**: new/modified/moved functions and methods; private/public choice; responsibility; file or owning-class rationale; state/invariant/lifecycle/collaborator usage; rejected service/function alternatives; tests.
- **Object-oriented decisions**: object candidates; object versus function, module operation, or record; identity or value semantics; encapsulated state and invariants; lifecycle; collaborators; composition, delegation, strategy, or inheritance decision; substitutability and contract-test evidence for inheritance; rejected hierarchy or object alternatives.
- **Main object / oversized / split decisions**: primary owner, lifecycle, invariant set, collaborator set, method clusters, mixed-role assessment, oversized signal, split type, rejected split rationale, and private helper justification.
- **File Granularity Decision**: proposed new file; keep-in-existing-file alternative; real boundary evidence; owner, lifecycle, invariant, collaborator, and change-reason comparison; import/export before/after; navigation cost before/after; test boundary before/after; private helper co-location decision; rejected micro-file split rationale.
- **Small File Merge Decision**: merge candidate; target owner; keep-separate alternative; real boundary check; public API/export impact; side-effect boundary impact; dependency direction impact; import/export before/after; navigation cost before/after; test boundary before/after; why merge is accepted or rejected.
- **Signature / side-effect / collaborator decisions**: parameter object need, boolean flags, weakly typed bags, mode/kind switches, return and error model, side-effect classification, dependency injection, lifecycle ownership, resource cleanup, state-machine escalation, and dependency direction.
- **Class decisions**: new/reused/extended classes; why a class is needed instead of a function; state, invariant, lifecycle, dependency injection, polymorphism, protocol, visibility, and tests.
- **File, directory, module, shared utility, and dependency decisions**: files/directories modified or added; owner, public API impact, boundary represented, import rules, cycles yes/no, split/no-split rationale, and confirmation that shared/common/utils contain no business logic.
- **Test placement**: unit, integration, and contract tests; confirmation that test location follows project convention and exercises observable behavior.
- **Rejected alternatives**: alternatives considered and why each was rejected for non-trivial structure decisions.
- **Execution linkage**: evidence inventory or handoff reference showing when the structure plan was produced and which validation proves the selected placement works.
- **Comment decisions**: exported/public doc comments, complex internal comments, test scenario/regression comments, critical inline comments, intentional omissions, redundant comments removed, and language/repository style.

# Evidence Contract
Close a structure decision only when it states the **mode selected**, boundaries inspected, professional judgment, reuse and placement rationale, behavior preservation for moved or extended code, validation commands or review artifacts with exit code when available, what evidence proves and does not prove, residual risk, and the next gate or handoff.

# Quality Gate

1. Existing and same-pattern variables, functions, classes, modules, services, repositories, hooks, components, tests, docs, shared/common/utils, and generated files were searched before new structure was added.
2. Every non-trivial name follows repository vocabulary, language convention, semantic responsibility, and local file/directory convention.
3. Every new function or method has single responsibility, natural name, visibility choice, location rationale, and owning-class rationale when placed on an object.
4. Every object/class decision distinguishes object, value object, domain object, service, adapter, strategy, module function, and local helper before adding a class.
5. Encapsulation, inheritance, polymorphism, and reflection protect real invariants, substitutability, protocol, or framework/schema boundaries and are tested through observable behavior.
6. Every changed file has one primary owner; oversized files, objects, functions, collaborator bloat, and multi-state logic carry split assessment based on responsibility, state, collaborators, branches, testability, and change reason.
7. Every new file has a cohesive owner, convention-compliant name, and real boundary; every new directory represents a module, layer, adapter, generated boundary, feature, or business capability.
8. Anti-fragmentation check rejects one-function file, trivial class file, tiny helper file, pass-through glue, and micro-file sprawl when no real boundary exists.
9. Every new file records the keep in existing file alternative, proposed new file, real boundary evidence, owner/lifecycle/invariant/collaborator/change-reason comparison, import/export before/after, navigation cost before/after, test boundary before/after, and rejected micro-file split rationale.
10. Small files without a real owner, lifecycle, invariant, collaborator, public contract, side-effect boundary, test boundary, or change rhythm must be considered for merge back into the unique owner.
11. Small files with a real boundary must not be merged merely to reduce file count.
12. Splitting cannot increase navigation cost unless the real boundary benefit is larger and recorded.
13. Merging cannot create mixed responsibility, hide side effects, break dependency direction, break public contract, or erase a valid test boundary.
14. Every split or merge records the rejected alternative.
15. Business/domain logic is classified and kept out of shared, common, and utils; public API exports are minimal and intentional.
16. New imports respect dependency direction and do not introduce cycles.
17. Tests are placed by project convention and exercise public behavior, not private helper structure.
18. Function signatures avoid unjustified boolean traps, weakly typed bags, and vague mode/kind switches; public returns express failure, empty, partial, and retry states.
19. Pure decision logic is separated from persistence, external APIs, events, cache mutation, logging side effects, and framework dependencies unless local convention justifies the boundary.
20. Reuse Ladder, Extension Safety, Advanced Refactoring, rejected alternatives, and agent-assisted evidence records are documented for non-trivial structure decisions.
21. Public/exported APIs have language-standard comments; non-trivial business, compatibility, concurrency, retry, transaction, idempotency, external API, performance, security, and test logic has concise comments where needed.

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

The capability is complete when the implementation has an explicit structure decision before code is written or accepted, all reuse candidates and rejected alternatives are documented, same-pattern structure scan is recorded, names follow repository vocabulary and language convention, each new or moved item is classified by responsibility taxonomy, object-oriented decisions justify object versus function/module/record, method placement is justified by state/invariant/lifecycle/collaborator usage, encapsulation and inheritance choices are tested through observable behavior, new functions/classes/files/directories have ownership and placement rationale, file granularity rejects excessive file split and micro-file sprawl without real boundaries, small file merge is considered when a file lacks an independent boundary, merge restraint protects small files with real boundaries, shared utility pollution is ruled out, dependency direction is preserved, and tests are placed at the observable behavior boundary.
