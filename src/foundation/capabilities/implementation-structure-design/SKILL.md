---
name: implementation-structure-design
description: Designs implementation structure before code is written by forcing semantic naming, reuse, extension, composition, object-method-module organization, object modeling, encapsulation, inheritance, method/class/function/file/directory placement, dependency-direction, shared-utility, and test-placement decisions for every code change.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "101"
changeforge_version: 0.1.1
---

# Mission
Design the internal implementation structure of every code change before writing or modifying code: decide how variables, functions, methods, classes, files, and directories should be named; whether to reuse an existing function, class, module, service, repository, hook, or component; extend an existing abstraction; compose it; wrap it with an adapter; model behavior as an object with identity, value semantics, encapsulated state, invariants, lifecycle, and collaborators; place behavior on a class, service, module function, adapter, or local helper; create a new function; create a new class; create a new file; or create a new directory while preserving local architecture conventions, dependency direction, cohesion, testability, and long-term maintainability.

The goal is to make every implementation look like it belongs in the codebase, not like an isolated AI-generated patch.

# When To Use

Use whenever code is added, moved, extracted, or reorganized: new or renamed functions, methods, classes, components, hooks, services, repositories, adapters, validators, parsers, mappers, DTOs, helpers, files, or directories.

Use when deciding where behavior lives, whether a concept is a domain object, value object, service/use-case object, adapter, strategy, plain data record, function, or module operation, or when inheritance, subclassing, protocols, polymorphic variation, object collaboration, file split/merge, method movement, class creation, or module internal composition is in scope.

Use when responsibility is unclear, similar logic may already exist, AI-generated code proposes new structure, an agent-assisted change needs reuse/placement evidence, a file accumulates mixed responsibilities, or a name uses vague buckets such as `common`, `shared`, `helper`, `util`, `manager`, `processor`, `module`, `component`, or `feature` without a concrete owner.

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

- Search before adding, then climb the reuse ladder before inventing structure. Prefer direct reuse, same-file extension, same-module extension, backward-compatible public API extension, composition, adapter/wrapper, or extraction before new code.
- Names are architecture: use repository vocabulary and language convention; variables name values, functions/methods name behavior, and vague buckets such as `common`, `shared`, `helper`, `util`, `manager`, `processor`, or `handler` are structure defects unless justified.
- Object-method-module organization comes before file movement. Every non-trivial structure change, file split, file merge, class addition, method move, or module addition must first classify object candidates, method ownership, relationship type, and module internal composition.
- A class requires identity, value semantics, state, invariant, lifecycle, policy, protocol role, collaborator boundary, dependency injection, polymorphism, or protocol conformance. Otherwise use a function, module-local helper, service operation, or plain data record.
- Method placement requires object responsibility: put a method on an object only when it uses or protects that object's state, invariant, lifecycle, collaborator, or protocol role. Orchestration, pure calculation, mapping, validation, persistence, I/O, and side effects belong in services, module functions, policies, repositories, adapters, or local helpers unless object evidence proves otherwise.
- Encapsulation protects invariants, not arbitrary code. Reject anemic object, helper-bag object, getter/setter data bags, generic manager/processor/helper classes, and god object growth.
- Every object split, merge, addition, or collapse declares relationship type: self-contained object, parent-child object, sibling object, collaborator, service plus policy/repository/adapter, value object, strategy/policy family, interface/protocol plus implementation, inheritance hierarchy, composition/delegation, module-local helper, or collapse/inline.
- Parent-child splits require parent lifecycle/orchestration, child detailed sub-behavior, no child access to parent internals, no pass-through parent, and reduced invariant/lifecycle/collaborator complexity. Sibling splits require independent change reason or lifecycle, no sibling internal access, and explicit shared policy/value/contract/helper.
- Inheritance is exceptional: allow only true substitutable taxonomy, framework-required extension, or protocol conformance with current variants, stable base contract, initialization safety, and per-subtype contract tests. Inheritance for code sharing alone is forbidden; prefer composition, delegation, strategy, or private helper.
- Design pattern decisions are mandatory before accepting factories, builders, strategies, observers, decorators, proxies, facades, commands, state objects, visitors, repositories, object pools, worker pools, pipelines, registries, providers, or abstract/interface layers; every selected pattern must name the current force, rejected simpler alternative, object relationship, method ownership, lifecycle, and tests.
- Structure decisions are performance-aware when they touch hot paths, CPU work, allocation, GC, async/coroutines, blocking or non-blocking IO, locks, pools, fan-out, queues, backpressure, cancellation, stream/body/descriptor cleanup, or network/storage/file/database IO; route those signals to runtime capabilities before choosing object, method, module, file, or pattern shape.
- Module structure is an internal object graph plus public facade, not just files in a directory. Group cohesive domain/value/service/policy/repository/adapter/mapper/helper/test objects with explicit internal dependency direction, minimal public API, and private internals.
- No business logic in shared, common, or utils. Shared utilities are pure technical code only; business terms belong to the owning module or domain capability.
- Files and directories need cohesive owners. File granularity is decided by owner/object/module boundary, not line count; large cohesive files may stay, small boundary files may stay, and fragmentation without a boundary is rejected.
- Default to keep in existing file when private helpers, constants, local types, narrow value objects, predicates, and local mappers share owner, lifecycle, invariant, collaborator family, and reason to change.
- A new file must prove a real boundary: different owner, lifecycle, invariant/state set, collaborator family, side-effect boundary, public contract, change rhythm, test boundary, generated/handwritten split, adapter/protocol/repository/client/gateway boundary, or current strategy/policy variants with contract tests.
- Reject anti-fragmentation failures: one-function file, tiny helper file, trivial class file, pass-through glue, split-to-test-private-helper, line-count-only split, naming-convenience split, and micro-file sprawl that worsens navigation cost.
- Small file merge is considered only after confirming no independent object boundary, public contract, value-object invariant, lifecycle, policy/strategy contract, adapter/repository side-effect boundary, dependency-direction protection, or test boundary would be lost. Merge restraint protects real boundaries.
- Function signatures need one purpose, structured parameters, explicit return states, no unjustified boolean traps, no weakly typed bags outside boundaries, and clear error/empty/partial/retry semantics.
- Pure decision logic and external side effects are separated by default; policy and domain code must remain testable without database, network, queue, cache, framework, or UI dependencies.
- Private stays private, new imports preserve dependency direction and avoid cycles, and tests follow project convention while exercising public behavior rather than private helper structure.
- Structure decisions must attach to execution evidence; agent-assisted changes cite the plan from the Execution Discipline Report.

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

The full discovery protocol, decision trees, and record templates live in this capability's `references/` (loaded in the dev profile and by skill authors). The body below carries the decision-critical rules compiled into every consuming professional skill. Resolve every structure decision under seven questions: naming, reuse and placement, object-method-module organization, object and module decomposition, object modeling, placement boundaries, and shared-utility pollution.

## Reuse & Placement

Discover local convention before adding or renaming anything: inspect the same file, same directory, parent module, sibling modules, tests, and generated/registry files in that order, and treat shared/common/utils as a last resort only after proving the behavior is domain-free. Record files inspected, detected naming/test/placement conventions, reuse candidates found, and rejected locations.

Choose the first valid reuse-ladder level and reject new code when a lower-cost level fits: direct reuse, same-file extension, same-module extension, backward-compatible public API extension, composition, adapter/wrapper, extraction, then new code. Produce a Reuse Ladder Record naming candidates, final decision, and why lower-cost levels were insufficient. Source/dev-only deep reference for skill authors: `references/reuse-and-placement.md`.

Professional skills cite the Reuse Ladder Record as evidence, not prose intent: backend attaches service/repository/validator reuse; frontend attaches component/hook/state reuse; AI review marks missing reuse search; test gates verify fixture/helper reuse without private-internal coupling.

## Advanced Refactoring & Extension Reuse

Prefer extending the existing owner over a parallel implementation only when responsibility stays single, existing callers keep their behavior, the change is backward compatible, new parameters are optional or a parameter object, no vague `type`/`kind`/`mode`/`flag`/`strategy` switch is added, and tests cover both old and new behavior. Reject extension when the owner would become ambiguous, the case belongs to a different owner, compatibility cannot be proven, the change requires cross-layer imports, or the name would have to become vague.

When refactoring, escalate only as far as needed: inline cleanup, then function extraction, then object extraction (only for real state/invariant/lifecycle/collaborator ownership), then interface or protocol extraction (only with multiple implementations today or a real external test seam), then inheritance (only with proven substitutability, a stable base contract, and per-subtype contract tests), then reflection or metadata dispatch (only when a framework or schema mapping requires it, with a type-safety boundary and a malformed-metadata fallback). Produce an Extension Safety Record and an Advanced Refactoring Decision. Source/dev-only deep reference for skill authors: `references/advanced-refactoring.md`.

## Naming

Names are architecture: a name must reveal owner, concept, role, and boundary, and a vague name is a structure defect, not a cosmetic issue. Prefer existing repository vocabulary over invented synonyms, and follow language convention for casing and visibility through `language-idiom-enforcement`. Variables name the value they hold, functions name behavior, and predicates read as booleans. Classify every name into the narrowest accurate category — business/domain, feature, component, module, service, domain/value object, repository, adapter/client, utility, helper, or common/shared — and reject a category when the behavior does not match it (for example, a `utility` that carries order, tenant, invoice, or permission terms is misclassified domain logic). Source/dev-only deep reference for skill authors: `references/naming.md`.

## Object-Method-Module Organization

Run this decision before every non-trivial structural change, file split, file merge, class addition, moved method, or module addition. File boundaries are downstream of object, method, and module organization; a split or merge is invalid when it cannot name the object relationship or module composition reason. Answer these nine questions before changing boundaries:
1. Object candidates: which domain object, value object, service/use-case object, policy/specification, adapter/client, repository, mapper, DTO/schema, strategy, state machine, module-local helper, plain function, or rejected candidate is involved, and why are rejected candidates rejected?
2. Object responsibility: does each object own identity, value semantics, state, invariant, lifecycle, policy, protocol role, or collaborator boundary? If not, do not create a class.
3. Method encapsulation: which methods belong on which object because they protect state/invariant/lifecycle/collaborator, and which methods stay in services, module functions, adapters, policies, repositories, or helpers because they are orchestration, pure calculation, mapping, validation, I/O, persistence, side effect, or would import infrastructure/UI/framework concerns?
4. Relationship type: declare self-contained object, parent-child object, sibling object, collaborator, service plus policy/repository/adapter, value object, strategy/policy family, interface/protocol plus implementation, inheritance hierarchy, composition/delegation, module-local helper, or collapse/inline.
5. Parent-child object rules: parent owns public lifecycle/orchestration, child owns detailed sub-behavior, child does not reach into parent internals, parent is not pass-through glue, and the split reduces invariant/lifecycle/collaborator complexity.
6. Sibling object rules: siblings are peer capabilities with independent change reason or lifecycle, no sibling internal access, and shared behavior goes through an explicit policy, value object, contract, or module-local helper.
7. Inheritance vs composition: inheritance needs true taxonomy/framework extension/protocol conformance with current variants, LSP/substitutability, base contract, compatible errors/lifecycle/initialization, and subtype contract tests; otherwise use composition, delegation, strategy, or private helper.
8. Module internal composition: for cohesive capability/layer clusters, name public API/facade, internal object graph, domain/value/service/policy/repository/adapter/mapper/helper grouping, internal dependency direction, minimal public API, private internals, placement, tests, and next-change location.
9. Design Pattern Decision: decide whether a pattern is needed; list candidates and direct-code alternative; map the pattern to object relationships, method encapsulation, module/file placement, public API, lifecycle, performance/concurrency/IO impact, tests, and anti-pattern risk. Source/dev-only deep references: `references/object-modeling.md` and `references/object-module-decomposition.md`.

## Performance-Aware Structure Decision

Record and route runtime signals before accepting object, method, module, file split/merge, or pattern choices: hot path, CPU-bound work, memory allocation, GC pressure, coroutine/async/event loop, blocking IO, non-blocking IO, lock/mutex/RWLock/atomic, lock held across IO, network IO, storage IO, file IO, DB query/transaction/connection pool, HTTP/SDK client lifecycle, goroutine/thread/task/fiber worker pool, unbounded fan-out, queue/channel/buffer/cache/batch growth, cancellation/timeout/context propagation, backpressure, and response body/stream/file descriptor cleanup.

## Object Modeling

Decide object responsibility before creating a class: identity, value semantics, lifecycle, state, invariant, policy, protocol role, or collaboration boundary. A class is justified only when a function or existing service method is insufficient — it must own state or lifecycle, enforce invariants across operations, implement a protocol with real variants today, or model a domain or value object. Place a method on a class only when it uses or protects that class's state, invariant, lifecycle, or collaborator; otherwise use a service, module function, adapter, or local helper, and never let the method force the object to import infrastructure or UI concerns. Encapsulation must protect invariants, not hide a data bag behind getters and setters. Inheritance is exceptional: use it only for a genuinely substitutable type hierarchy with a stable base contract and per-subtype tests, and never for code sharing alone — prefer composition, delegation, or strategy. Reject generic `Manager`, `Processor`, `Handler`, `Helper`, or `Util` class names unless explicitly justified. Source/dev-only deep reference for skill authors: `references/object-modeling.md`.

Choose value object for value-owned equality/validation/normalization/unit safety; domain object for identity/lifecycle/invariants/state transitions; service for collaborator coordination; adapter for external protocol translation; strategy for multiple current algorithms behind a stable interface; module function or local helper for stateless local behavior. Do not create a class just to group functions, make testing easier, or imitate enterprise style.

Reflection or metadata dispatch is allowed only when a framework, schema, plugin protocol, or generated mapping requires it, with typed boundary, malformed-metadata fallback, explicit default behavior, and invalid-metadata tests.

## Object, Signature, And Side-Effect Decomposition

Every file needs one main owner, one primary lifecycle or responsibility, and one coherent collaborator set. Long files, large objects, unrelated method clusters, constructor bloat, and branch-heavy functions are evidence to inspect; line count alone is not the decision. Functions need one readable purpose, structured parameters, clear return contracts, and explicit failure/empty/partial states. Pure calculations, business decisions, state mutation, persistence, external calls, events, logging, metrics, and cache access must be classified so policy and domain code stay testable without infrastructure. Source/dev-only deep reference for skill authors: `references/object-module-decomposition.md`.

A file or directory split is justified by mixed owners, lifecycles, collaborators, reasons to change, layers, adapter protocols, generated/handwritten code, or tests that cannot find their owning behavior; line count alone is only a signal.

## File Granularity And Anti-Fragmentation

Run Object-Method-Module Organization before accepting any new file, file split, file merge, or extracted helper file. Apply anti-fragmentation after the object/method/module relationship is known. File granularity is determined by object responsibility, module composition, owner, and boundary, not by line count. Large files are not automatically a problem; mixed responsibility is the problem. Small files are not automatically a problem; fragmentation without a real boundary is the problem.

The default is co-location: keep tightly related private helpers, local constants, local types, narrow value objects, predicates, and owner-internal mappers in the main owner file when they serve one owner, lifecycle, invariant set, collaborator family, and reason to change. A main owner file plus private helpers is a valid structure.

Create a new file only when the split first names the object relationship or module internal composition reason, then names a real boundary: different primary owner, different lifecycle, different invariant or state set, different collaborator family, different side-effect boundary, different public contract, different change rhythm, different test boundary, generated versus handwritten code, adapter/protocol/repository/client/gateway boundary, or current strategy/policy variants with contract tests. The boundary must explain why the keep in existing file alternative was rejected.

A file split must say which object, object relationship, or module-internal grouping the new file represents. A split that cannot map to a self-contained object, parent-child, sibling, collaborator, policy/strategy, adapter/repository, value object, inheritance/composition/delegation, module-local helper, or module object cluster is rejected.

Reject these splits: "looks more modular"; reducing line count alone; lowering function length alone; naming convenience alone; avoiding owner analysis; exposing or extracting private helpers only to test them; one tiny function per file; one trivial class per file; pass-through policy/helper/adapter glue; splitting constants or options used only by one owner; and any micro-file sprawl that makes a reader jump across several files to understand one business decision.

File granularity must improve or preserve navigation cost. If the next maintainer must open more files to understand the same cohesive rule, the split is a navigation cost regression unless a real boundary offsets that cost and the tradeoff is recorded.

## Small File Merge And Merge Restraint

Before merging a small file, confirm it is not an independent object boundary or module-internal public contract. Consider small file merge back into the unique owner when a file contains only one tiny private function, trivial class, local predicate, local mapper, constant group, or pass-through glue; is used by only one owner file; has no independent owner, lifecycle, invariant, collaborator family, public contract, side-effect boundary, test boundary, or change rhythm; repeats the owner concept in its filename; makes one business decision require multiple file jumps; exists only so tests can target private helper logic; and merging would reduce import/export surface, lower navigation cost, and make the next-change location clearer.

Reject merging a small file when it has a public API/export, adapter/client/gateway/repository/protocol/generated-code boundary, independent value-object invariant, independent lifecycle or state machine, multiple legitimate current consumers, current strategy/policy variants with contract tests, independent public behavior test boundary, dependency-direction protection, visible side effects, or a separate owner that would make the target file mixed-responsibility if combined.

Merge restraint is as important as anti-fragmentation. Do not collapse adapter code into services, value-object invariants into procedural owners, policy variants into orchestration methods, or side-effect boundaries into pure decision files just to reduce file count. A split merge decision is accepted only when object-method encapsulation does not get worse, the resulting owner is clearer, dependency direction is preserved, public contracts remain intact, side effects stay visible, and main-flow readability improves or stays no worse.

## Placement Boundaries

A new file needs a cohesive owner and a convention-compliant name; add to an existing file when it already owns the responsibility, and reject a filename that introduces a new suffix, prefix, pluralization, or layer word the surrounding directory does not use. A new directory must represent a business capability, layer, adapter, feature, or generated-code boundary — never a convenience folder. Keep private code private and do not export "just in case." New imports must respect module-boundary and layered-architecture dependency direction and introduce no cycles. Frontend placement decides feature-local versus shared for components, hooks, validators, state, API clients, and routes; feature-local state does not move to a global store without real cross-feature ownership. Backend placement decides controller, service, domain, repository, adapter, validator, mapper, DTO, and job ownership; business rules never live in transport handlers, generic utilities, or persistence adapters. Source/dev-only deep reference for skill authors: `references/placement-boundaries.md`.

## Shared-Utility Pollution

Shared, common, and utils packages may hold pure technical, domain-free utilities only. Business logic — order, tenant, invoice, booking, cancellation, entitlement, permission, workflow, or any other domain term — belongs to the owning module or domain capability, never to a shared bucket used to avoid choosing an owner. A helper placed in `common` to dodge the ownership decision is a structure defect. Audit every shared utility added: confirm it is domain-free and that no business vocabulary appears in its name or body.

# Failure Modes

- Reuse/search failures: duplicate code, invented synonyms, public exports for one module, shared/common business logic, helper placed in `common` to avoid ownership, and tests coupled to private helpers instead of public behavior.
- Object failures: class before object responsibility, anemic object, helper-bag object, god object, getter/setter data bag, generic manager/processor/helper, inheritance for code sharing without substitutability/base contract/subtype tests, and caller branching on subclasses.
- Split failures: object boundary missing during file split, one-function file, tiny helper file, trivial class file, pass-through glue, micro-file sprawl, line-count-only split, navigation cost regression, and private helper export only for tests.
- Merge failures: reckless file merge, object boundary lost during file merge, lost small-file boundary, adapter/repository side effect hidden in service, value object invariant folded into procedural code, policy with tests collapsed into orchestration, and fewer files producing mixed responsibility.
- Module failures: module public facade and module private internals not separated, module object graph unclear, internal dependency direction unclear, arbitrary directory collection, unrelated object families in one module, and internals imported from outside.
- Placement failures: new directory without boundary, frontend feature-local behavior globalized with hidden assumptions, backend service importing forbidden infrastructure, and refactor extraction leaving duplication or naming drift.

# Output Contract

Return an Implementation Structure Plan for every non-trivial code addition, move, extraction, or reorganization:

- **Existing structure inspected / same-pattern structure scan / reuse decision**: files searched; existing functions/classes/modules/services/repositories/hooks/components considered; same file/module/adjacent modules/shared/common/utils/tests/docs/generated files checked; reuse ladder decision and rejected lower-cost options.
- **Vocabulary, naming, and responsibility taxonomy**: variable, parameter, field, function, method, class, file, directory, package, namespace, component, hook, service, repository, adapter, utility, helper, common/shared, test, generated, and configuration decisions; repository convention followed.
- **Function, method, signature, side-effect, and collaborator decisions**: new/modified/moved functions and methods; visibility; file or owning-class rationale; parameter/return/error model; side-effect classification; dependency injection; lifecycle/resource ownership; state-machine escalation; rejected alternatives; tests.
- **Object-Method Encapsulation Decision**: object candidates; selected object type; methods owned by object; methods rejected from object; state/invariant/lifecycle/collaborator evidence; public behavior tests; rejected function/class/helper/service/adapter/repository/policy/module-function/plain-record alternatives.
- **Object Relationship Map**: parent-child / sibling / collaborator / policy / strategy / adapter / value object / inheritance / composition / delegation / module-local helper / collapse-inline; relationship direction; allowed collaboration; forbidden internal access; tests proving relationship.
- **Design Pattern Decision Record**: selected pattern or direct-code decision; pattern candidates; rejected patterns and simpler alternative; object relationship, method placement, module/file placement, public API, lifecycle/ownership, side-effect visibility, invariant protection, tests, deletion path, and residual risk.
- **Inheritance vs Composition Decision**: inheritance considered yes/no; taxonomy evidence; substitutability evidence; base contract; subtype contract tests; rejected composition/delegation or rejected inheritance rationale.
- **Module Internal Composition Plan**: module owner/capability; public API/facade; internal object graph; domain/value/service/policy/repository/adapter/mapper/helper grouping; internal dependency direction; file/directory placement; test placement; next-change location.
- **Performance-Aware Structure Decision**: runtime signals present or absent; route to `language-performance-safety`, `concurrency-control`, `profiling`, `solution-optimality-evaluation`, `cache-design`, `idempotency-retry-design`, `async-job-design`, or `reliability-observability-gate`; pattern performance tradeoff; pattern rejected for performance or complexity.
- **Main object / oversized / split decisions**: primary owner, lifecycle, invariant set, collaborator set, method clusters, mixed-role assessment, oversized signal, split type, rejected split rationale, and private helper justification.
- **File Granularity Decision**: proposed new file; keep-in-existing-file alternative; object/module relationship; real boundary evidence; owner/lifecycle/invariant/collaborator/change-reason comparison; import/export, navigation cost, and test boundary before/after; private helper co-location; rejected micro-file split rationale.
- **Small File Merge Decision**: merge candidate; target owner; keep-separate alternative; real boundary check; public API/export, side-effect boundary, dependency direction, import/export, navigation cost, and test boundary impact; why merge is accepted or rejected.
- **File, directory, module, shared utility, dependency, test, comment, and execution linkage decisions**: modified/added paths; owner and public API impact; import/cycle rules; shared/common audit; test placement through observable behavior; useful comments; evidence inventory or handoff reference.

# Evidence Contract
Close a structure decision only when it states the **mode selected**, boundaries inspected, professional judgment, reuse and placement rationale, behavior preservation for moved or extended code, validation commands or review artifacts with exit code when available, what evidence proves and does not prove, residual risk, and the next gate or handoff.

# Quality Gate

1. Existing and same-pattern structure was searched, names follow repository/language conventions, and new structure uses the first valid reuse-ladder level.
2. Every function/method/class/file/directory has a single owner, visibility choice, placement rationale, dependency-direction check, public/private decision, and observable test boundary.
3. Every new class proves function/module-local helper/service operation/plain record is insufficient; every new method proves object state/invariant/lifecycle/collaborator/protocol ownership; every moved method proves old/new owner relationship.
4. Every object/class decision distinguishes domain object, value object, service, adapter, strategy, module function, local helper, record, composition, delegation, inheritance, and rejected alternatives before adding a class.
5. Encapsulation, polymorphism, reflection, and inheritance protect real invariants, substitutability, protocol, or framework/schema boundaries; every inheritance hierarchy has substitutability, base contract, initialization safety, lifecycle compatibility, and per-subtype contract tests or is replaced by composition/delegation.
6. Every design pattern has a current force, rejected simpler alternative, object relationship, method ownership, performance/concurrency/IO/lifecycle impact, and public behavior or contract tests.
7. Any structure change that introduces async, locks, pools, network/storage/file/database IO, blocking calls, fan-out, queues, backpressure, cancellation, or stream/body/descriptor cleanup routes to runtime and concurrency capabilities before placement is accepted.
8. Object Pool requires profile evidence; Singleton/global state requires lifecycle, thread-safety, test reset, and shutdown cleanup; Observer/PubSub requires unsubscribe, bounded fan-out, backpressure, and error isolation.
9. Proxy, Adapter, and Repository declare IO, timeout, retry, resource cleanup, and side-effect visibility; Command, Worker, and Queue declare idempotency, retry, backpressure, cancellation, and partial failure.
10. Every split file maps to an object relationship or module internal composition decision; every parent-child object or sibling object split declares relationship direction, allowed collaboration, forbidden internal access, and tests.
11. File granularity records keep-in-existing-file alternative, real boundary evidence, owner/lifecycle/invariant/collaborator/change-reason comparison, import/export before/after, navigation cost before/after, test boundary before/after, private helper co-location, and rejected micro-file split rationale.
12. Anti-fragmentation rejects one-function file, trivial class file, tiny helper file, pass-through glue, micro-file sprawl, and split-driven navigation cost regression when no real boundary exists.
13. Small file merge is considered for files without real boundary; small files with valid object boundary, public contract, value-object invariant, lifecycle, policy/strategy contract, adapter/repository side-effect boundary, dependency-direction protection, or test boundary are protected by merge restraint.
14. Merging cannot erase object boundary, hide side effects, break dependency direction, break public contract, create mixed responsibility, or lose a test boundary.
15. Every module is a cohesive object-method-helper cluster with module public facade, module private internals, module object graph, internal dependency direction, next-change location, and test boundary; arbitrary directory collections do not count.
16. Business/domain logic stays out of shared/common/utils, signatures avoid boolean traps and weak bags, pure decisions stay separate from side effects, tests exercise public behavior, and evidence records link the structure decision to validation.

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

The capability is complete when the implementation has an explicit structure decision before code is written or accepted, all reuse candidates and rejected alternatives are documented, same-pattern structure scan is recorded, names follow repository vocabulary and language convention, object-method-module organization is recorded before file split or merge, each new or moved item is classified by responsibility taxonomy, object-oriented decisions justify object versus function/module/record, method placement is justified by state/invariant/lifecycle/collaborator usage, object relationships and forbidden internal access are declared, inheritance choices have substitutability and contract tests or are replaced by composition/delegation, modules describe cohesive internal object graphs with public facade and private internals, new functions/classes/files/directories have ownership and placement rationale, file granularity rejects excessive file split and micro-file sprawl without real boundaries, small file merge is considered when a file lacks an independent boundary, merge restraint protects small files with real boundaries, shared utility pollution is ruled out, dependency direction is preserved, and tests are placed at the observable behavior boundary.

Design pattern decisions are complete only when they either select direct code or select a pattern with current force, rejected simpler alternative, object relationship, method placement, module/file placement, public API impact, lifecycle, runtime impact, side-effect visibility, invariant protection, tests, deletion path, and residual risk.

Performance-aware structure decisions are complete only when hot path, async/coroutine/event-loop, lock, pool, fan-out, queue, backpressure, cancellation, cleanup, and network/storage/file/database IO risks are routed to `language-performance-safety`, `concurrency-control`, `profiling`, `solution-optimality-evaluation`, `idempotency-retry-design`, `async-job-design`, `cache-design`, or `reliability-observability-gate` as appropriate.
