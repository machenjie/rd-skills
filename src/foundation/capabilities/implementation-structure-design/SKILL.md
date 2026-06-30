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

- Do not use for pure formatting, comment-only edits, or reviews with no structural decision.
- Do not justify speculative abstractions; with one current use case, prefer concrete local implementation unless current extension is explicit.
- Do not wrap procedural code in objects for appearance, introduce inheritance for code sharing, or treat minimal structure as fewest files when a real boundary would be lost.

# Stage Fit

Owns implementation-planning; informs coding, code-review, refactoring, testing, release, and handoff. Use it during implementation-planning for reuse, naming, placement, visibility, and test placement; during coding to keep new structure aligned to planned boundaries; and during code-review/refactoring to check reuse, placement, dependency direction, and behavior-preserving movement against the plan before handoff.

# Non-Negotiable Rules

- Search before adding, then climb the reuse ladder before inventing structure. Prefer direct reuse, same-file extension, same-module extension, backward-compatible public API extension, composition, adapter/wrapper, or extraction before new code.
- Run the minimal-correctness ladder before creating a function, class, file, directory, shared utility, dependency, config switch, or public export. A structure is acceptable only when a lower-cost option would be less correct for the current requirement.
- Escalate material structure ambiguity into the SDD Design Choice Gate. If object/function/class/file/directory/module/shared-tool/inheritance/composition/pattern choices alter long-term structure, extension path, public surface, data/security/acceptance behavior, or maintenance ownership, record an SDD `design_decision_points` entry instead of silently choosing.
- Low-risk local structure choices may proceed as safe assumptions only when the record names the first valid reuse-ladder level, local convention, reversibility, and why acceptance is neutral.
- Names are architecture: use repository vocabulary and language convention; variables name values, functions/methods name behavior, and vague buckets such as `common`, `shared`, `helper`, `util`, `manager`, `processor`, or `handler` are structure defects unless justified.
- Object-method-module organization comes before file movement. Every non-trivial structure change, file split, file merge, class addition, method move, or module addition must first classify object candidates, method ownership, relationship type, and module internal composition.
- A class requires identity, value semantics, state, invariant, lifecycle, policy, protocol role, collaborator boundary, dependency injection, polymorphism, or protocol conformance. Otherwise use a function, module-local helper, service operation, or plain data record.
- Method placement requires object responsibility: put a method on an object only when it uses or protects that object's state, invariant, lifecycle, collaborator, or protocol role. Orchestration, pure calculation, mapping, validation, persistence, I/O, and side effects belong in services, module functions, policies, repositories, adapters, or local helpers unless object evidence proves otherwise.
- Encapsulation protects invariants, not arbitrary code. Reject anemic object, helper-bag object, getter/setter data bags, generic manager/processor/helper classes, and god object growth.
- Every object split, merge, addition, or collapse declares relationship type: self-contained object, parent-child object, sibling object, collaborator, service plus policy/repository/adapter, value object, strategy/policy family, interface/protocol plus implementation, inheritance hierarchy, composition/delegation, module-local helper, or collapse/inline.
- Parent-child splits require parent lifecycle/orchestration, child detailed sub-behavior, no child access to parent internals, no pass-through parent, and reduced invariant/lifecycle/collaborator complexity. Sibling splits require independent change reason or lifecycle, no sibling internal access, and explicit shared policy/value/contract/helper.
- Inheritance is exceptional: allow only true substitutable taxonomy, framework-required extension, or protocol conformance with current variants, stable base contract, initialization safety, and per-subtype contract tests. Inheritance for code sharing alone is forbidden; prefer composition, delegation, strategy, or private helper.
- Design pattern decisions are mandatory before accepting factories, builders, strategies, observers, decorators, proxies, facades, commands, state objects, visitors, repositories, object pools, worker pools, pipelines, registries, providers, or abstract/interface layers; every selected pattern must name the current force, rejected simpler alternative, object relationship, method ownership, lifecycle, and tests.
- One-implementation abstractions are rejected unless they protect a current external boundary, test seam, framework contract, or imminent checked-in variant; future-proofing alone is not a current force.
- Structure decisions are performance-aware when they touch hot paths, CPU work, allocation, GC, async/coroutines, blocking or non-blocking IO, locks, pools, fan-out, queues, backpressure, cancellation, stream/body/descriptor cleanup, or network/storage/file/database IO; route those signals to runtime capabilities before choosing object, method, module, file, or pattern shape.
- Module structure is an internal object graph plus public facade, not just files in a directory. Group cohesive domain/value/service/policy/repository/adapter/mapper/helper/test objects with explicit internal dependency direction, minimal public API, and private internals.
- No business logic in shared, common, or utils. Shared utilities are pure technical code only; business terms belong to the owning module or domain capability.
- Files and directories need cohesive owners. File granularity is decided by owner/object/module boundary, not line count; large cohesive files may stay, small boundary files may stay, and fragmentation without a boundary is rejected.
- Default to keep in existing file when private helpers, constants, local types, narrow value objects, predicates, and local mappers share owner, lifecycle, invariant, collaborator family, and reason to change.
- A new file can be the minimal correct choice when it proves a real boundary: different owner, lifecycle, invariant/state set, collaborator family, side-effect boundary, public contract, change rhythm, test boundary, generated/handwritten split, adapter/protocol/repository/client/gateway boundary, or current strategy/policy variants with contract tests.
- Reject anti-fragmentation failures: one-function file, tiny helper file, trivial class file, pass-through glue, split-to-test-private-helper, line-count-only split, naming-convenience split, and micro-file sprawl that worsens navigation cost.
- Small file merge is considered only after confirming no independent object boundary, public contract, value-object invariant, lifecycle, policy/strategy contract, adapter/repository side-effect boundary, dependency-direction protection, or test boundary would be lost. Merge restraint protects real boundaries.
- Function signatures need one purpose, structured parameters, explicit return states, no unjustified boolean traps, no weakly typed bags outside boundaries, and clear error/empty/partial/retry semantics.
- Pure decision logic and external side effects are separated by default; policy and domain code must remain testable without database, network, queue, cache, framework, or UI dependencies.
- For object-method placement work, produce an explicit Object-Method Encapsulation Decision before moving code: accepted domain/value object methods must protect state, invariants, lifecycle, or collaborator boundaries; rejected helpers stay module-local and private; orchestration stays in service/use-case objects; payment, persistence, cache, queue, clock, framework, and network side effects stay in adapters/repositories/services; public behavior tests visibly name the exact words allowed, denied, expired, refund hold, payment failure, external-side-effect, and failure paths without importing private underscore helpers; the decision record must state `no side effects` for pure decisions. When writing candidate-facing docs or test names, prefer positive accepted-placement rationale and avoid persisting rejected anti-pattern labels unless the repository's own documentation standard requires those labels.
- Private stays private, new imports preserve dependency direction and avoid cycles, and tests follow project convention while exercising public behavior rather than private helper structure.
- Structure decisions must attach to execution evidence; agent-assisted changes cite the plan from the Execution Discipline Report.

# Industry Benchmarks

Anchor against: domain-driven design module ownership and bounded context rules; layered architecture dependency direction; Clean Architecture dependency inversion; SOLID principles with special attention to single responsibility, interface segregation, and Liskov substitutability; Tell Don't Ask and Law of Demeter object-collaboration heuristics; Gang of Four composition-over-inheritance guidance; Martin Fowler refactoring catalog for extract, move, inline, introduce parameter object, and replace inheritance with delegation decisions; Google Engineering Practices code review guidance for readability, complexity, and local consistency; Architecture Decision Records for non-trivial structure decisions; dependency graph tools such as ArchUnit, Dependency Cruiser, Nx project graph, Bazel visibility, Pants dependency inference, and Go package boundaries; Testing Library and xUnit conventions for behavior-oriented tests placed at the observable boundary.

# Selection Rules

Select this capability as the structure-selection path when an implementation needs a placement decision before code is written or accepted. Use it with:

- `backend-change-builder` for service, repository, controller, validator, job, mapper, transaction, and domain logic placement.
- `frontend-change-builder` for component, hook, state, API client, form validator, route, and shared UI placement.
- `architecture-impact-reviewer` and `module-boundary-design` when placement could alter module boundaries or dependency direction.
- `language-idiom-enforcement` when naming decisions require language-specific casing, visibility, export, package, namespace, doc-comment, or public API convention checks.
- `ai-code-review-refactor` and `code-review` when generated code adds helpers, utilities, abstractions, objects, hierarchies, files, directories, or imports without local-pattern evidence.
- `refactoring` when behavior-preserving movement needs a target structure before extraction, move, split, inline, or collapse steps.

Prefer adjacent capabilities when the main question is broader: `module-boundary-design` for module ownership and public interfaces, `layered-architecture-design` for layer responsibility, `page-component-decomposition` for UI hierarchy, `service-business-logic` for backend orchestration responsibility, and `refactoring` for behavior-preserving movement after the target structure is chosen.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| Placement planning | New or moved function, method, class, file, directory, component, hook, service, repository, adapter, helper, or public export. | Select the first valid reuse-ladder level and owner boundary before code. | Inspected files/searches, reuse candidates, rejected locations, placement rationale, test boundary. | `repository-context-map`, `module-boundary-design`, `quality-test-gate` | Skip new structure until same-file, same-module, parent, sibling, and shared/common scans are recorded. |
| Object/module decomposition | Class, method move, object split/merge, pattern, interface, inheritance, or module internal graph is proposed. | Prove object responsibility, relationship direction, method ownership, public facade, and private internals. | Object candidates, state/invariant/lifecycle evidence, relationship map, dependency direction, public behavior tests. | `code-clarity-maintainability`, `design-pattern-selection`, `architecture-impact-reviewer` | Skip inheritance/interface/pattern unless current variants, substitutability, lifecycle, and tests exist. |
| Split/merge/refactor | File split, small-file merge, extraction, collapse, or shared utility change. | Preserve owner clarity, navigation cost, side-effect visibility, and dependency direction. | Keep-in-existing-file alternative, split/merge decision, import/export impact, behavior-preservation validation. | `refactoring`, `code-review`, `cleanup-deletion-governance` | Skip line-count-only, one-function-file, private-helper-export, and shared/common business-logic moves. |
| Agent/AI structure closure | Agent patch adds structure or relies on memory, graph, or prior validation for placement. | Reconcile current source, graph, memory, execution order, and validation freshness before handoff. | Source reread, graph/memory accepted or rejected, same-pattern scan, command outcome, residual risk. | `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, `validation-broker` | Skip completion claims when evidence predates final edits or owner/reviewer split is missing. |

# Proactive Professional Triggers

- **Signal:** New function, class, file, directory, helper, shared utility, export, or dependency is proposed before local pattern discovery and reuse search. **Hidden risk:** duplicate logic, wrong owner, circular dependency, or shared/common pollution becomes permanent structure. **Required professional action:** require repository inspection, same-pattern scan, and reuse ladder decision before editing. **Route to:** `repository-context-map`, `repository-graph-analysis`, `quality-test-gate`. **Evidence required:** inspected paths, search scope, reuse candidates, rejected locations, dependency direction, and public-behavior test boundary.
- **Signal:** Object, method, interface, inheritance, factory, strategy, adapter, or wrapper is accepted because it seems cleaner or future-proof. **Hidden risk:** hidden wrong object boundary or speculative abstraction makes tests preserve implementation shape instead of observable behavior. **Required professional action:** require object responsibility proof, relationship-direction comparison, simpler alternative rejection, and public behavior validation. **Route to:** `code-clarity-maintainability`, `design-pattern-selection`, `testability-seam-design`. **Evidence required:** object-method decision, relationship map, current variants or rejected inheritance, test output, and not-verified residual risk.
- **Signal:** Repository graph, project memory, compaction summary, prior validation, or previous review is used as placement proof after later source, report, generated, or registry edits. **Hidden risk:** stale graph or memory sends code to the wrong owner and closure overclaims validation freshness. **Required professional action:** verify current source, downgrade stale context to selector-only, rerun stale validators, and record residual risk. **Route to:** `project-memory-governance`, `execution-trajectory-analysis`, `validation-broker`. **Evidence required:** accepted/rejected graph or memory claim, current-source comparison, command/report path, validation freshness verdict, and rollback note.

# Risk Escalation Rules

- Escalate to `architecture-impact-reviewer` for new module/directory boundaries, public exports, cross-layer imports, shared abstractions, class hierarchies, polymorphic interfaces, object collaboration boundaries, or dependency-direction exceptions.
- Escalate to `security-privacy-gate` when placement affects auth, tenant isolation, secrets, sensitive data, uploads, or trust-boundary bypass.
- Escalate to `data-api-contract-changer` when placement changes public DTOs, API contracts, generated clients, SDK exports, schemas, events, or versioned config.
- Escalate to `quality-test-gate` when the structure lacks a public behavior test boundary or would require brittle private-internal tests.
- Escalate to `agent-execution-discipline` when an agent adds structure without reuse search, rejected alternatives, placement rationale, validation result, and closure boundary.

# Critical Details

The body carries the decision-critical rules compiled into consuming professional skills. Deep protocol, examples, and record templates stay in `references/` and load only when structure quality is uncertain or a skill author is editing this capability.

Resolve every structure decision through this spine:

1. **Local pattern discovery and reuse**: inspect same file, same directory, parent module, sibling modules, tests, generated/registry files, then shared/common/utils only after proving the behavior is domain-free. Choose the first valid reuse ladder level before new code: direct reuse, same-file extension, same-module extension, backward-compatible public API extension, composition, adapter/wrapper, extraction, then new code.
2. **Naming and taxonomy**: names reveal owner, concept, role, and boundary. Classify each candidate as business/domain, feature, component, module, service, domain object, value object, repository, adapter/client, utility, helper, common/shared, function, method, class, file, or directory.
3. **Object-method encapsulation first**: before a file split, file merge, class addition, moved method, or module addition, produce object candidates, method placement evidence, object responsibility, object relationship map, and rejected alternatives. A method belongs on an object only when it protects state, invariant, lifecycle, collaborator, protocol role, or value semantics.
4. **Relationship and module graph**: declare self-contained object, parent-child object, sibling object, collaborator, service plus policy/repository/adapter, value object, strategy/policy family, interface/protocol plus implementation, inheritance vs composition, delegation, module-local helper, collapse/inline, module internal composition, module object graph, module public facade, module private internals, and internal dependency direction.
5. **File granularity and anti-fragmentation**: line count is only a signal. Keep in existing file when owner, lifecycle, invariant set, collaborator family, and reason to change stay together. Split only for a real object/module boundary; reject micro-file sprawl, one-function file, tiny helper file, trivial class file, private-helper export, navigation cost regression, object boundary missing during file split, and object boundary lost during file merge.
6. **Small file merge and merge restraint**: consider small file merge only when no public contract, side-effect boundary, value-object invariant, lifecycle, strategy/policy contract, dependency-direction protection, or test boundary would be lost. Reject reckless file merge and lost small-file boundary even when fewer files look simpler.
7. **Side-effect and runtime-aware placement**: keep pure decisions separate from persistence, external APIs, events, logs, metrics, cache, clock, randomness, filesystem, process, and environment access. Route hot path, async, lock, pool, fan-out, queue, backpressure, cancellation, cleanup, network/storage/file/database IO, and pattern runtime risk to runtime and reliability capabilities before accepting placement.
8. **Execution linkage**: attach reuse search, same-pattern scan, placement rationale, validation, and residual risk to the Execution Discipline Report.

# Reference Loading Policy

- `references/reuse-and-placement.md` — L1/L2 discovery protocol, reuse ladder, Reuse Ladder Record, and function-placement tree.
- `references/advanced-refactoring.md` — L2/L3 extension safety, advanced refactoring escalation, inheritance/reflection safety records.
- `references/naming.md` — L1/L2 naming taxonomy for variables, functions, methods, classes, files, directories, utilities, helpers, and common/shared.
- `references/object-modeling.md` — L2/L3 object candidate matrix, method placement matrix, object relationship map, inheritance vs composition, anemic object/helper-bag object/god object failure modes.
- `references/object-module-decomposition.md` — L2/L3/L4 module internal composition, module object graph, file granularity, anti-fragmentation, split merge decision, side-effect boundary, collaborator, and Structure Evidence Record.
- `references/placement-boundaries.md` — L1/L2 file, directory, frontend, backend, public/private/export, and shared-utility placement trees.

The output contract below is inline-only and must be satisfied in the handoff even when no deep reference is loaded.

# Failure Modes

- **Reuse/search failure:** duplicate code, invented synonyms, public exports for one module, shared/common business logic, helper placed in `common` to avoid ownership, and tests coupled to private helpers instead of public behavior.
- **Object responsibility failure:** class before object responsibility, anemic object, helper-bag object, god object, getter/setter data bag, generic manager/processor/helper, inheritance for code sharing without substitutability/base contract/subtype tests, and caller branching on subclasses.
- **Split failure:** object boundary missing during file split, one-function file, tiny helper file, trivial class file, pass-through glue, micro-file sprawl, line-count-only split, navigation cost regression, and private helper export only for tests.
- **Merge failure:** reckless file merge, object boundary lost during file merge, lost small-file boundary, adapter/repository side effect hidden in service, value object invariant folded into procedural code, policy with tests collapsed into orchestration, and fewer files producing mixed responsibility.
- **Module graph failure:** module public facade and module private internals not separated, module object graph unclear, internal dependency direction unclear, arbitrary directory collection, unrelated object families in one module, and internals imported from outside.
- **Placement failure:** new directory without boundary, frontend feature-local behavior globalized with hidden assumptions, backend service importing forbidden infrastructure, and refactor extraction leaving duplication or naming drift.
- **Execution-coupling failure:** reuse, placement, or split evidence comes from stale memory, stale graph output, or validation that predates final edits, so handoff claims completion for unverified structure.
- **Pattern-runtime failure:** factory, repository, proxy, observer, singleton, worker, pool, or command structure hides IO, locks, lifecycle, retries, cleanup, backpressure, or cancellation from the caller and from tests.

# Output Contract

Return an Implementation Structure Plan for every non-trivial code addition, move, extraction, or reorganization:

- **Existing structure inspected / same-pattern structure scan / reuse decision**: files searched; existing functions/classes/modules/services/repositories/hooks/components considered; same file/module/adjacent modules/shared/common/utils/tests/docs/generated files checked; reuse ladder decision and rejected lower-cost options.
- **Vocabulary, naming, and responsibility taxonomy**: variable, parameter, field, function, method, class, file, directory, package, namespace, component, hook, service, repository, adapter, utility, helper, common/shared, test, generated, and configuration decisions; repository convention followed.
- **Function, method, signature, side-effect, and collaborator decisions**: new/modified/moved functions and methods; visibility; file or owning-class rationale; parameter/return/error model; side-effect classification; dependency injection; lifecycle/resource ownership; state-machine escalation; rejected alternatives; tests.
- **Object-Method Encapsulation Decision**: object candidates; selected object type; methods owned by object; methods rejected from object; state/invariant/lifecycle/collaborator evidence; public behavior tests; rejected function/class/helper/service/adapter/repository/policy/module-function/plain-record alternatives.
- **Object Relationship Map**: parent-child / sibling / collaborator / policy / strategy / adapter / value object / inheritance / composition / delegation / module-local helper / collapse-inline; relationship direction; allowed collaboration; forbidden internal access; tests proving relationship.
- **Design Pattern Decision Record**: selected pattern or direct-code decision; pattern candidates; rejected patterns and simpler alternative; object relationship, method placement, module/file placement, public API, lifecycle/ownership, side-effect visibility, invariant protection, tests, deletion path, and residual risk.
- **Minimal Correctness Decision**: simplicity ladder result; stdlib/platform/existing-code/local-code/dependency choice; direct-code versus abstraction decision; deleted or rejected structure; shortcut ceiling and upgrade trigger when applicable.
- **Inheritance vs Composition Decision**: inheritance considered yes/no; taxonomy evidence; substitutability evidence; base contract; subtype contract tests; rejected composition/delegation or rejected inheritance rationale.
- **Module Internal Composition Plan**: module owner/capability; public API/facade; internal object graph; domain/value/service/policy/repository/adapter/mapper/helper grouping; internal dependency direction; file/directory placement; test placement; next-change location.
- **Performance-Aware Structure Decision**: runtime signals present or absent; route to `language-performance-safety`, `concurrency-control`, `profiling`, `solution-optimality-evaluation`, `cache-design`, `idempotency-retry-design`, `async-job-design`, or `reliability-observability-gate`; pattern performance tradeoff; pattern rejected for performance or complexity.
- **Main object / oversized / split decisions**: primary owner, lifecycle, invariant set, collaborator set, method clusters, mixed-role assessment, oversized signal, split type, rejected split rationale, and private helper justification.
- **File Granularity Decision**: proposed new file; keep-in-existing-file alternative; object/module relationship; real boundary evidence; owner/lifecycle/invariant/collaborator/change-reason comparison; import/export, navigation cost, and test boundary before/after; private helper co-location; rejected micro-file split rationale.
- **Small File Merge Decision**: merge candidate; target owner; keep-separate alternative; real boundary check; public API/export, side-effect boundary, dependency direction, import/export, navigation cost, and test boundary impact; why merge is accepted or rejected.
- **File, directory, module, shared utility, dependency, test, comment, and execution linkage decisions**: modified/added paths; owner and public API impact; import/cycle rules; shared/common audit; test placement through observable behavior; useful comments; evidence inventory or handoff reference.
- **SDD Design Choice Gate linkage**: material structure choices that require user/owner preference; safe-assumption rationale for low-risk local decisions; no-choice rationale tied to repository convention, source constraints, or reuse evidence.

# Evidence Contract
Close a structure decision only when it states the **mode selected**, boundaries inspected, professional judgment, reuse and placement rationale, behavior preservation for moved or extended code, validation commands or review artifacts with exit code when available, what evidence proves and does not prove, residual risk, and the next gate or handoff.

# Quality Gate

1. Existing and same-pattern structure was searched, names follow repository/language conventions, and new structure uses the first valid reuse-ladder level.
2. Material structure choices are represented as SDD design decision points, resolved user choices, or safe assumptions with local/reversible/conventional/acceptance-neutral rationale.
3. Every function/method/class/file/directory has a single owner, visibility choice, placement rationale, dependency-direction check, public/private decision, and observable test boundary.
4. Every new class proves function/module-local helper/service operation/plain record is insufficient; every new method proves object state/invariant/lifecycle/collaborator/protocol ownership; every moved method proves old/new owner relationship.
5. Every object/class decision distinguishes domain object, value object, service, adapter, strategy, module function, local helper, record, composition, delegation, inheritance, and rejected alternatives before adding a class.
6. Encapsulation, polymorphism, reflection, and inheritance protect real invariants, substitutability, protocol, or framework/schema boundaries; every inheritance hierarchy has substitutability, base contract, initialization safety, lifecycle compatibility, and per-subtype contract tests or is replaced by composition/delegation.
7. Every design pattern has a current force, rejected simpler alternative, object relationship, method ownership, performance/concurrency/IO/lifecycle impact, and public behavior or contract tests.
8. Any structure change that introduces async, locks, pools, network/storage/file/database IO, blocking calls, fan-out, queues, backpressure, cancellation, or stream/body/descriptor cleanup routes to runtime and concurrency capabilities before placement is accepted.
9. Object Pool requires profile evidence; Singleton/global state requires lifecycle, thread-safety, test reset, and shutdown cleanup; Observer/PubSub requires unsubscribe, bounded fan-out, backpressure, and error isolation.
10. Proxy, Adapter, and Repository declare IO, timeout, retry, resource cleanup, and side-effect visibility; Command, Worker, and Queue declare idempotency, retry, backpressure, cancellation, and partial failure.
11. Every split file maps to an object relationship or module internal composition decision; every parent-child object or sibling object split declares relationship direction, allowed collaboration, forbidden internal access, and tests.
12. File granularity records keep-in-existing-file alternative, real boundary evidence, owner/lifecycle/invariant/collaborator/change-reason comparison, import/export before/after, navigation cost before/after, test boundary before/after, private helper co-location, and rejected micro-file split rationale.
13. Anti-fragmentation rejects one-function file, trivial class file, tiny helper file, pass-through glue, micro-file sprawl, and split-driven navigation cost regression when no real boundary exists.
14. Small file merge is considered for files without real boundary; small files with valid object boundary, public contract, value-object invariant, lifecycle, policy/strategy contract, adapter/repository side-effect boundary, dependency-direction protection, or test boundary are protected by merge restraint.
15. Merging cannot erase object boundary, hide side effects, break dependency direction, break public contract, create mixed responsibility, or lose a test boundary.
16. Every module is a cohesive object-method-helper cluster with module public facade, module private internals, module object graph, internal dependency direction, next-change location, and test boundary; arbitrary directory collections do not count.
17. Business/domain logic stays out of shared/common/utils, signatures avoid boolean traps and weak bags, pure decisions stay separate from side effects, tests exercise public behavior, and evidence records link the structure decision to validation.

# Used By

Used by `backend-change-builder`, `frontend-change-builder`, `ai-code-review-refactor`, `architecture-impact-reviewer`, `code-review`, `refactoring`, and `quality-test-gate`.

# Handoff

Hand off to `module-boundary-design` for unclear ownership/API/dependency direction; `layered-architecture-design` for layer responsibility; `architecture-impact-reviewer` for inheritance, class hierarchy, polymorphic interface, or object collaboration boundary risk; `page-component-decomposition` for UI decomposition; `service-business-logic` for backend orchestration; `refactoring` after target structure is chosen; `code-review` for completed diffs; and `agent-execution-discipline` when reuse search, placement rationale, same-pattern scan, or validation evidence is missing.

# Completion Criteria

The capability is complete when the implementation has an explicit structure decision before code is written or accepted, all reuse candidates and rejected alternatives are documented, same-pattern structure scan is recorded, names follow repository vocabulary and language convention, object-method-module organization is recorded before file split or merge, each new or moved item is classified by responsibility taxonomy, object-oriented decisions justify object versus function/module/record, method placement is justified by state/invariant/lifecycle/collaborator usage, object relationships and forbidden internal access are declared, inheritance choices have substitutability and contract tests or are replaced by composition/delegation, modules describe cohesive internal object graphs with public facade and private internals, new functions/classes/files/directories have ownership and placement rationale, file granularity rejects excessive file split and micro-file sprawl without real boundaries, small file merge is considered when a file lacks an independent boundary, merge restraint protects small files with real boundaries, shared utility pollution is ruled out, dependency direction is preserved, and tests are placed at the observable behavior boundary.

Design pattern decisions are complete only when they either select direct code or select a pattern with current force, rejected simpler alternative, object relationship, method placement, module/file placement, public API impact, lifecycle, runtime impact, side-effect visibility, invariant protection, tests, deletion path, and residual risk.

Performance-aware structure decisions are complete only when hot path, async/coroutine/event-loop, lock, pool, fan-out, queue, backpressure, cancellation, cleanup, and network/storage/file/database IO risks are routed to `language-performance-safety`, `concurrency-control`, `profiling`, `solution-optimality-evaluation`, `idempotency-retry-design`, `async-job-design`, `cache-design`, or `reliability-observability-gate` as appropriate.
