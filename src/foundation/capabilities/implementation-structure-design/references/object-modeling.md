# Object Modeling — Full Decision Trees

Deep reference for the `## Object Modeling` and `## Object-Method-Module Organization` rules in `implementation-structure-design`.
The capability body carries the decision-critical summary; this file carries the full object, method, relationship, class, and inheritance decision rules. It is loaded in the `dev` profile and by skill authors when structure quality is uncertain.

## Object Candidate Classification Matrix

| Candidate | Use when | Reject when | Method placement rule | File/module placement impact | Test boundary |
| --- | --- | --- | --- | --- | --- |
| Domain object | Identity, lifecycle, state transitions, and business invariants belong together. | It only carries data or delegates all decisions to services. | Put invariant and lifecycle methods here; keep infrastructure out. | Lives in the owning domain/module internals or public domain API when it is a module contract. | Public domain behavior and invalid transition tests. |
| Value object | Equality, validation, normalization, unit safety, or a business value invariant is independent of identity. | It is only a DTO wrapper or shortens a parameter list with no invariant. | Put normalization, comparison, validation, and derived value behavior here. | May stay co-located when narrow and owner-internal; split when invariant is reused or independently tested. | Construction, equality, invalid value, and normalization tests. |
| Aggregate/root if applicable | A domain root enforces consistency across child entities/value objects. | The consistency boundary is not current or persistence is the only reason. | Put aggregate-level invariant and child lifecycle coordination here. | Owns child objects internally; repository talks to aggregate root, not arbitrary internals. | Aggregate behavior tests plus repository contract tests if persisted. |
| Entity | Identity persists across changes and lifecycle matters, but it is not the aggregate root. | The value is replaceable and equality by value is enough. | Put entity-local invariant and state transition behavior here. | Usually internal to a module or aggregate; avoid public cross-module entity leakage. | Identity, lifecycle, and invariant tests through aggregate/module API. |
| Service/use-case object | Behavior coordinates collaborators, transactions, policies, repositories, adapters, or events. | It becomes a god object or hides domain invariants that belong to objects/policies. | Put orchestration here; keep pure invariant methods on domain/value/policy owners. | Public facade or application layer entry point for the module. | Public use-case behavior, side-effect orchestration, and failure path tests. |
| Policy/specification | Named rule or decision can be evaluated independently and has rule authority. | It has one trivial branch only, writes infrastructure, or merely shortens a service method. | Put pure decision methods here; no persistence or external calls. | Split when policy has independent tests, variants, or change rhythm; otherwise co-locate as private helper. | Decision table tests and contract tests for policy variants. |
| Strategy | Multiple current algorithms share one stable interface and callers should not branch. | There is one implementation, variation is speculative, or names hide unrelated behavior. | Put algorithm-specific behavior in concrete strategies; shared contract in interface/protocol. | Keep family in the owning module; expose only the strategy contract if consumers need it. | Interface contract tests across all current strategies. |
| Adapter/client/gateway | External SDK, protocol, network, filesystem, queue, clock, cache, or framework boundary is isolated. | It only passes through to a local object with no external protocol or side effect. | Put protocol translation, retries, error translation, and resource handling here. | Separate file/module boundary is usually justified even if small. | Adapter contract, error translation, timeout/retry, and side-effect tests. |
| Repository | Persistence queries and transaction-facing data access are isolated. | It contains business rules or callers need persistence internals. | Put persistence methods and query contracts here; keep decisions in domain/service/policy. | Infrastructure or data-access boundary; public surface is repository contract only. | Repository contract tests and transaction/query behavior tests. |
| Mapper/assembler | It translates between DTO/domain/persistence/view models with explicit shape changes. | Mapping is one private field rename used by one owner. | Put pure model translation here; keep validation and side effects elsewhere. | Co-locate when owner-internal; split when mapping is public, cross-boundary, or reused. | Round-trip, missing field, compatibility, and boundary-shape tests. |
| DTO/schema | It represents transport, storage, event, or generated contract shape. | It starts carrying business invariants or lifecycle behavior. | Put serialization and schema validation only when local convention expects it. | Place at API/data/contract boundary; do not leak persistence DTOs as domain objects. | Schema/contract compatibility and validation tests. |
| State machine | States, transitions, guards, invalid transitions, and transition side effects are meaningful. | States are cosmetic or fewer than the current code can express clearly. | Put transition guards and transition result behavior here; side effects stay in orchestrator/adapters unless the local model owns them. | May be domain object, policy, or module-internal helper depending on ownership. | Transition table, invalid transition, lifecycle compatibility, and side-effect orchestration tests. |
| Module-local helper | Stateless or narrow behavior serves exactly one module/object and has no public contract. | It is exported for tests, reused across unrelated modules, or carries independent invariants. | Keep helper private; do not pretend it is a class. | Co-locate with owner or keep in internal helper file only when navigation improves. | Test through owning public behavior unless it has a real module-internal contract. |
| Plain function | Pure, stateless behavior has a clear input/output contract and no object responsibility. | It needs lifecycle, state, invariant ownership, protocol role, or collaborator boundary. | Keep as function; do not wrap in a helper-bag object. | Co-locate with module owner or expose only if production callers need it. | Pure function tests or public behavior tests through owner. |

## Method Placement Matrix

| Method type | Belongs in | Reject object placement when |
| --- | --- | --- |
| State/invariant method | Domain object, value object, entity, aggregate, or state machine that owns the invariant. | It only reads unrelated data or requires infrastructure/UI imports. |
| Lifecycle transition method | Domain object, aggregate/root, entity, or state machine. | The service merely sequences collaborators and the object has no lifecycle authority. |
| Policy decision method | Policy/specification or domain object when the rule is intrinsic to that object. | The rule needs database, network, cache, framework, or UI access. |
| Orchestration method | Service/use-case object or module public facade. | It is pushed into a domain/value object and forces side-effect dependencies inward. |
| Side-effect adapter method | Adapter/client/gateway/job/repository as appropriate. | It hides external calls inside a domain object, policy, or generic helper. |
| Persistence method | Repository or data-access adapter. | It is placed on domain objects just because the domain has the data. |
| Mapping method | Mapper/assembler, DTO/schema boundary, or module-local helper when narrow. | It becomes a method on a domain object and imports transport or persistence shapes. |
| Pure helper | Plain function or module-local helper. | It is wrapped in a class only to group functions or make tests import it. |
| Validation method | Value object/domain object for invariant validation; DTO/schema for boundary validation; policy for business eligibility. | One validator mixes transport shape, persistence constraints, and domain policy without an owner. |

## Relationship Matrix

| Relationship | Accepted conditions | Rejected conditions | Tests | File placement |
| --- | --- | --- | --- | --- |
| Parent-child | Parent owns public lifecycle/orchestration; child owns detailed sub-behavior; split reduces invariant/lifecycle/collaborator complexity. | Parent becomes pass-through; child reaches into parent internals; split only follows method names. | Parent public behavior plus child behavior through allowed boundary. | Child may be module-internal file when independently named; otherwise co-locate. |
| Sibling | Peer capabilities have independent change reasons or lifecycles. | Siblings access each other's internals or share hidden mutable state. | Public behavior per sibling plus shared contract/policy tests. | Same module or sibling files under existing convention. |
| Collaborator | One object depends on another through an explicit role or contract. | Collaboration is hidden global access or imports internal concrete details. | Collaboration behavior and dependency-direction checks. | Collaborator lives behind public/module-internal contract. |
| Strategy/policy family | Multiple current variants share a stable interface and can be selected without caller branching. | Single speculative implementation or unrelated algorithms share one vague interface. | Contract tests across all variants. | Family stays in owning module; expose only the stable contract. |
| Adapter/port | External protocol, SDK, framework, persistence, clock, cache, queue, filesystem, or network is isolated. | Adapter is pass-through glue around local code. | Adapter contract and failure-mode tests. | Separate boundary is valid even when small. |
| Inheritance hierarchy | True substitutable taxonomy, framework-required extension, or protocol conformance with current variants. | Code reuse only, caller branches by subtype, lifecycle or initialization differs incompatibly. | Base contract and subtype contract tests. | Keep hierarchy local to module unless public taxonomy is intentional. |
| Composition/delegation | Behavior variation is collaborative or technical reuse, not taxonomy. | Delegation hides ownership or creates circular calls. | Delegated behavior tests and dependency-direction checks. | Collaborator/helper file only when boundary is real; otherwise co-locate. |
| Module-local helper | Helper serves one owner and has no external contract. | Exported for tests or used as dumping ground. | Owner public behavior tests. | Private co-location or internal helper file under local convention. |

## Inheritance Decision Tree

```text
Considering inheritance?
|-- Is there a true taxonomy where every subtype is substitutable for the base?
|   |-- No: reject inheritance; use composition, delegation, strategy, or helper.
|   `-- Yes
|-- Are there current variants, not speculative future variants?
|   |-- No: reject inheritance until variation exists.
|   `-- Yes
|-- Is the base contract stable: preconditions, postconditions, errors, lifecycle?
|   |-- No: reject or define an interface/protocol contract first.
|   `-- Yes
|-- Can every subtype be used without caller branching on concrete type?
|   |-- No: reject; polymorphism is cosmetic.
|   `-- Yes
|-- Is initialization safe and compatible across subtypes?
|   |-- No: reject or use factories/composition.
|   `-- Yes
|-- Is the only benefit shared code?
|   |-- Yes: reject; extract private helper or delegate collaborator.
|   `-- No
|-- Are base contract tests and per-subtype contract tests present?
|   |-- No: reject until tests prove substitutability.
|   `-- Yes: inheritance accepted with rationale and fallback plan.
```

Output inheritance accepted/rejected rationale must state taxonomy evidence, current variants, base contract, subtype substitutability, initialization safety, rejected composition/delegation alternatives, and contract tests. If any step is not proven, prefer composition/delegation or a strategy family when current variants need runtime selection.

## Anti-Patterns

- Anemic object: a class with fields plus getters/setters but no invariant, lifecycle, or behavior authority.
- Data bag with getters/setters: procedural code still owns the decisions while the class only stores values.
- Helper-bag object: a class created to group stateless functions or private helpers.
- Generic `Manager`, `Processor`, or `Handler`: vague ownership that hides service, policy, adapter, repository, or module responsibilities.
- God object: one object owns unrelated method clusters, collaborator families, states, and reasons to change.
- Base class for code reuse only: inheritance chosen instead of extraction, composition, or delegation.
- Sibling objects that reach into each other's internals instead of using explicit contracts.
- Parent object that is only a pass-through to children and adds no lifecycle or orchestration value.
- Strategy with one implementation and no current variant contract.
- Object split that increases navigation cost without an independent object boundary.
- Method moved to an object only because the filename looked right, without state/invariant/lifecycle/collaborator evidence.
