# Object And Module Decomposition

Use this reference when a change adds or modifies a file, object, function, signature, side-effect boundary, collaborator set, stateful object, or large service. It is intentionally loaded only for implementation-planning, code-review, and refactoring cases where structure quality is uncertain.

## Mandatory Precondition: Object-Method-Module Organization

Run Object-Method-Module Organization before any file split or merge. File split/merge is invalid if it cannot name the object relationship or module composition reason first.

Required decision order:

1. Object candidates: domain object, value object, aggregate/root, entity, service/use-case object, policy/specification, strategy, adapter/client/gateway, repository, mapper/assembler, DTO/schema, state machine, module-local helper, or plain function.
2. Method ownership: which object owns each method and which methods are rejected from object placement because they are orchestration, pure calculation, mapping, validation, I/O, persistence, side effect, or infrastructure/UI/framework concern.
3. Relationship type: self-contained object, parent-child, sibling, collaborator, service plus policy, service plus repository, service plus adapter, value object owned by domain/service, strategy/policy family, interface/protocol plus implementation, inheritance hierarchy, composition/delegation, module-local helper, or collapse/inline.
4. Module internal composition: public facade/API, internal object graph, domain/value/service/policy/repository/adapter/mapper/helper/test grouping, internal dependency direction, minimal public API, private internals, file/directory placement, and next-change location.

## File Main Object Decision Tree

1. Name the file's primary owner.
   - Business/domain object, service/use case, adapter/client, repository, mapper, controller, job, component, hook, DTO/schema, test fixture, or pure technical utility.
   - If no owner can be named without `manager`, `processor`, `helper`, `common`, or `misc`, the file does not have a clear main responsibility.

2. Check lifecycle and invariant cohesion.
   - One primary lifecycle: keep together.
   - Multiple independent lifecycles: split.
   - Multiple state or invariant sets that change for different reasons: split by state owner or policy.

3. Check collaborator cohesion.
   - One collaborator family serving the same responsibility: keep together.
   - Different collaborator families such as payment gateway, notification client, repository, cache, and event bus each supporting different method clusters: split into orchestrator plus collaborator objects or adapters.

4. Check method clusters.
   - Methods naturally grouped around one public responsibility: keep.
   - Clusters around cancellation, refund, invoice, shipping, reporting, and export behavior in one file: split into peer objects or child modules.

5. Check role mixing.
   - A file may contain a main object and small private helpers that serve that object.
   - A file must not contain multiple peer primary roles such as controller plus repository, domain policy plus database adapter, API DTO plus persistence model, mapper plus job runner, or test helper plus production helper.

6. Interpret file length as a signal, not the root cause.
   - Long because one cohesive object has explicit states, branches, and comments: inspect but not automatically split.
   - Long because responsibility, state, collaborator count, branch count, test difficulty, or public API surface expanded: split or justify.

7. Decide.
   - Keep as one file when one owner, one lifecycle, one invariant set, one collaborator family, and one reason to change remain true.
   - Split when two or more peer owners, lifecycles, state sets, collaborator sets, method clusters, or public responsibilities exist.
   - Reject a new file when the existing file already owns the responsibility and stays cohesive after the change.

## File Granularity Decision Tree

Use this before creating a new file, accepting an extracted helper file, merging
a small file, or rejecting a proposed merge.

0. Run Object-Method-Module Organization first.
   - New file creation requires object/method/module relationship evidence.
   - Small file merge requires proof the file is not an independent object boundary.
   - File split must state which object or module relationship the extracted file represents.
   - File merge must prove object-method encapsulation does not get worse.

1. Identify owner.
   - Name the primary owner for the behavior or small file.
   - If a small file cannot name an independent owner, prefer merge into the unique owner or private co-location.
   - If the only available name repeats the owner plus `predicate`, `mapper`, `options`, `helper`, or `glue`, treat that as weak owner evidence.

2. Compare lifecycle, invariant, collaborator, and change reason.
   - Same owner, same lifecycle, same invariant set, same collaborator family, and same reason to change: keep together or merge.
   - Two or more real differences across those dimensions: split or keep separate.
   - One weak difference needs stronger evidence from public contract, side-effect boundary, test boundary, or change rhythm before creating or preserving a file.

3. Check public contract.
   - Public API/export exists: keep separate or explicitly define the public surface and compatibility impact.
   - No public API/export and only one owner consumes it: prefer private co-location.
   - Do not export a private helper only so a test can import it.

4. Check side-effect boundary.
   - Adapter/client/repository/gateway/protocol/generated-code boundary: keep separate even if the file is small.
   - Pure owner-internal judgment, mapping, constant grouping, or local predicate: merge or keep private in the owner file.
   - Do not merge side-effect boundaries into pure policy or service code when that hides dependency direction or resource ownership.

5. Check navigation cost.
   - If reading one business decision requires jumping through multiple vague tiny files, merge, inline, or regroup by owner.
   - If merging would make the main owner read as mixed responsibility or hide side effects, keep separate.
   - The chosen shape must make the next related change location more obvious or at least no less obvious.

6. Decide.
   - Keep together when one owner and one reason to change remain clear.
   - Split when a real boundary is named and the keep-in-existing-file alternative is rejected with evidence.
   - Merge into owner when a small file has no independent boundary and only serves one owner.
   - Keep separate with boundary when a small file protects public contract, side effect, value-object invariant, lifecycle, strategy/policy variant, generated code, or dependency direction.
   - Collapse/inline when an extracted function or class adds no name, invariant, test, or navigation value.
   - Reject both split and merge when neither target has a clear owner; require a better owner or module boundary first.

### Good Co-Location Example: Main Owner Plus Private Helpers

```python
# orders/cancellation_service.py

PREMIUM_GRACE_MINUTES = 30


class CancellationService:
    def cancel(self, order, actor, requested_at):
        if not _actor_can_cancel(order, actor):
            return CancellationResult.denied("not_authorized")
        if _inside_premium_grace(order, requested_at):
            return CancellationResult.allowed(refund_hold=False)
        if _has_disputed_payment(order):
            return CancellationResult.allowed(refund_hold=True)
        return self._standard_cancellation_result(order, requested_at)


def _inside_premium_grace(order, requested_at):
    return order.customer_tier == "premium" and requested_at <= order.cancel_by


def _has_disputed_payment(order):
    return order.payment_status == "disputed"
```

This is acceptable when the predicates and constants are private to `CancellationService`, share its owner and lifecycle, and do not need a public policy contract. The file remains one main owner plus private helpers.

### Good Separation Example: Policy With Boundary

```python
# orders/cancellation_policy.py

class CancellationPolicy:
    def decide(self, order, actor, requested_at):
        ...
```

This split is justified when cancellation rules have their own owner, invariants, tests through a policy contract, current policy variants, or change rhythm separate from orchestration. It is not justified only because the service file is long.

### Good Separation Example: Small Adapter Kept Separate

```python
# orders/payment_gateway_client.py

class PaymentGatewayClient:
    def place_refund_hold(self, payment_id, reason):
        ...
```

This file should remain separate even if small because it owns an external protocol, credentials, retries, error translation, and side effects. Merging it into `CancellationService` would hide the adapter/client boundary and break dependency-direction clarity.

### Anti-Examples: Do Not Split

- `order_cancellation_predicate.py` contains one private boolean used only by `CancellationService`.
- `refund_flag_mapper.py` contains one owner-internal mapper with no public contract and no independent lifecycle.
- `policy_options.py` contains two fields and is imported by only one file.
- `premium_grace.py`, `disputed_refund.py`, `refund_mapper.py`, `cancellation_constants.py`, and `policy_options.py` turn one cancellation use case into eight file jumps.
- `order_cancellation_adapter.py` only passes arguments from the service to the policy and adds no external protocol or side-effect boundary.

### Anti-Examples: Do Not Merge

- `payment_gateway_client.py` is merged into `cancellation_service.py` because it has one method, hiding external side effects inside orchestration.
- `CancellationWindow` value object is merged into a service method, scattering its invariant across procedural branches.
- `CancellationPolicy` with independent public behavior tests is folded into `CancellationService.cancel`, making the service both orchestrator and policy owner.
- Several files are collapsed only to reduce file count, leaving one owner file with adapter, value object, policy, repository, and orchestration responsibilities.

## Object Split Decision Tree

1. Parent-child object split.
   - Accepted when one object owns public lifecycle/orchestration and child objects own detailed sub-behavior.
   - Parent responsibilities: public API, lifecycle sequencing, transaction/use-case boundary, error aggregation, collaborator coordination.
   - Child responsibilities: detailed rules, state transitions, value-object invariants, adapter protocol details, or policy variants.
   - Reject when the parent becomes only a pass-through dumping ground, the child reaches into parent internals, the parent forwards every method without adding lifecycle value, or the split does not reduce invariant/lifecycle/collaborator complexity.
   - Tests: parent public behavior proves orchestration; child behavior is proven through public/module-internal contract without internal access.

2. Sibling object split.
   - Accepted when responsibilities are peer capabilities with independent change reasons or lifecycles.
   - Examples: `OrderCancellationPolicy`, `OrderRefundPolicy`, `OrderShippingPolicy`.
   - Siblings must not access each other's internals or hidden state.
   - Shared behavior must go through explicit policy, value object, contract, or module-local helper.
   - Reject when objects are split by method names only or when one sibling needs to know another sibling's private data.
   - Tests: each sibling has public behavior tests, and shared contract/helper behavior is covered at its own boundary.

3. Inheritance versus composition.
   - Inheritance is accepted only for true substitutable taxonomy, framework-required extension, or protocol conformance with current variants.
   - Prove base preconditions, postconditions, error behavior, lifecycle compatibility, initialization safety, LSP/substitutability, and per-subtype contract tests.
   - Reject inheritance for code reuse alone, caller branching by subtype, incompatible initialization, or speculative future variants.
   - Prefer composition, delegation, strategy, or private helper extraction when behavior variation is not taxonomic.

4. Strategy or policy family.
   - Use when algorithm or rule families are current, named, and expected to vary behind a stable contract.
   - Reject if there is only one implementation and the abstraction exists only because a branch looked untidy.
   - Require contract tests for current variants and a selection boundary that does not leak subtype decisions to callers.

5. Adapter or port.
   - Use for external systems, protocols, SDKs, formats, framework APIs, persistence, network calls, clocks, queues, and side effects.
   - Domain and policy objects depend on ports or data contracts, not concrete infrastructure.
   - Keep small adapter/client/repository files separate when they protect side effects, retry/error behavior, resource ownership, or dependency direction.

6. Value object.
   - Use when a parameter group, state group, or business value has independent invariants, equality, normalization, or unit safety.
   - Use to replace scattered primitives when callers need the invariant, not merely to shorten a parameter list.
   - Co-locate a narrow value object when it is owner-internal; split when it has independent invariant tests or current consumers.

7. State machine.
   - Use when an object has more than three meaningful states, non-trivial transitions, invalid transitions, guards, or transition side effects.
   - Pair with `state-machine-modeling` for domain lifecycles.
   - Keep side effects in orchestration/adapters unless the local domain model explicitly owns transition effects.

8. Collaborator object.
   - Use when constructor dependencies, method clusters, or side effects show the current object is coordinating unrelated collaborators.
   - Split by collaborator role only when each collaborator role maps to a responsibility, not just to reduce constructor parameter count cosmetically.
   - Reject if the new collaborator only relays calls or creates circular collaboration.

9. Object plus private helper co-location.
   - Keep private predicates, mappers, constants, narrow helper functions, and owner-internal value normalization near the object when they share owner, lifecycle, invariant set, collaborator family, and reason to change.
   - Do not export these helpers for tests; test through owner public behavior unless a module-internal production contract exists.

10. Object cluster to module.
   - When several objects/functions/helpers form one business capability or layer, group them as a module object cluster instead of one directory per object.
   - The cluster needs a public facade/API, private internals, internal dependency direction, object graph, test boundary, and next-change location.

11. Object graph cycle check.
   - Draw calls/imports among selected objects and helpers.
   - Reject cycles where siblings call each other's internals, child objects reach into parent internals, policies call services, domain/value objects import adapters, or helpers depend on their owners.
   - Break cycles with a service orchestrator, interface/port, policy/value object, module-local helper, event, or dependency inversion.

12. Collapse or inline.
   - If a new object has no state, invariant, lifecycle, protocol role, current variation, or meaningful collaborator boundary, collapse to a function, module operation, local helper, or existing owner.
   - Collapse helper-bag classes, anemic objects, pass-through adapters without external boundary, and speculative strategies with one implementation.

## Module Object Cluster Decision Tree

1. Identify module capability or layer.
   - Name the business capability, bounded context, feature, adapter boundary, layer, or generated-code boundary.
   - Reject a module whose only owner is a technical bucket such as shared/common/utils unless it is pure technical utility.

2. List objects and functions inside the module.
   - Include public API/facade, domain objects, value objects, services/use cases, policies/specifications, repositories, adapters/clients, mappers/assemblers, DTOs/schemas, module-local helpers, and tests.

3. Classify each item.
   - Public API, internal domain, internal value, application/use-case, policy/specification, repository, infrastructure adapter, mapper/DTO, module-local helper, test, generated, or obsolete/collapse.

4. Decide internal folders/files using repository convention.
   - Common labels such as api/public, domain/internal, application/usecase, infrastructure/adapter, and tests may be useful, but do not force them when the repository uses another convention.
   - Prefer the smallest structure that keeps public contracts visible and internals private.

5. Decide public API.
   - Expose the public facade, commands/queries/DTOs/events/contracts consumers need today.
   - Do not expose internal policies, repositories, adapters, mappers, helpers, or concrete child objects just in case.

6. Decide internal dependency direction.
   - Public facade/application orchestrates domain/policies/repositories/adapters.
   - Domain/value/policy code must not depend on infrastructure, UI, framework, or persistence details.
   - Repositories/adapters implement contracts and isolate side effects.
   - Helpers depend inward or stay leaf-local; they must not create cycles.

7. Decide next-change location.
   - For each likely adjacent change, name the file/object/module location a maintainer should edit first.
   - If the answer is "search many files" or "shared/common," the cluster is not cohesive enough.

8. Decide split/no-split for submodule.
   - Split a submodule only when a sub-cluster has a separate public contract, owner, lifecycle, dependency direction, side-effect boundary, test boundary, or independent change rhythm.
   - Keep inside the module when objects/functions are private to one capability and the public facade remains coherent.

## Function And Signature Structure Decision Tree

1. Purpose.
   - A function should have one readable purpose expressed by its name.
   - A function that validates, decides, mutates, persists, maps, logs, emits events, and formats output needs an orchestration justification or decomposition.

2. Parameter count.
   - One to three parameters is usually readable.
   - Four or more parameters require review for command/request/options/parameter object.
   - Introduce a parameter object when parameters travel together, have defaults, validation, or a business name.

3. Boolean traps.
   - Reject call sites like `run(order, true, false)` unless the booleans are unmistakable and local.
   - Prefer named options, distinct methods, or explicit policy objects.

4. Weak types.
   - `any`, `Object`, `map[string]interface{}`, `interface{}`, untyped dictionaries, and generic bags are allowed at untrusted or serialization boundaries only.
   - Convert to typed DTO, command, domain object, or value object before business logic.

5. Return contract.
   - Public returns must express success, failure, empty, partial, retryable, and terminal states explicitly.
   - Do not force callers to infer failure from `null`, empty strings, magic values, or swallowed exceptions.

6. Error model.
   - A caller should know whether to retry, display, compensate, ignore, or escalate.
   - Error shape must preserve cause without leaking internal or sensitive data.

7. Model separation.
   - DTO, domain object, persistence model, view model, and generated schema are separate responsibilities.
   - Mixing them is allowed only with a local convention and no conflicting invariants, persistence leakage, or public contract drift.

## Side Effect Boundary Decision Tree

Classify each line or helper by effect:

- Pure calculation.
- Business decision or policy.
- In-memory state mutation.
- Persistence.
- External API call.
- Message or event emission.
- Logging or metrics.
- Cache read or write.
- Clock, randomness, file system, process, or environment access.

Decision rules:

1. Pure logic and side effects are separated by default.
2. Policy and rule objects do not write databases, call external APIs, enqueue messages, or mutate caches.
3. Domain objects do not directly depend on framework, HTTP, database, SDK, queue, or UI types.
4. Repository, adapter, client, job, and gateway objects isolate external side effects.
5. Service or use-case objects orchestrate validation, policy, transaction, adapter calls, and events, but must not grow without limit.
6. Logging and metrics may sit in orchestration or adapter layers but must not hide decisions or alter behavior.
7. Cache access is a side effect; it needs source-of-truth, invalidation, and fallback ownership.

Split when a pure decision cannot be tested without a database, network, queue, cache, framework, clock, or global singleton.

## Collaborator And Dependency Injection Decision Tree

1. Constructor dependency count.
   - Zero to three collaborators is usually readable.
   - Four to six requires a responsibility review.
   - More than six is strong evidence of an oversized object unless the object is explicitly an orchestrator with a stable use-case boundary.

2. Direct construction.
   - Creating value objects locally is fine.
   - Directly creating infrastructure clients, repositories, clocks, random generators, SDKs, or framework services inside business logic hides side effects and blocks tests.

3. Global singleton and service locator use.
   - Reject when it hides dependencies, lifecycle, tenant/user context, credentials, or resource ownership.
   - Accept only when local framework convention requires it and tests can still control behavior.

4. Collaborator boundary.
   - Collaborators should belong to the same responsibility boundary.
   - If collaborators serve different method clusters, split the object or move methods.

5. Lifecycle and resources.
   - State who creates, owns, shares, and closes each collaborator.
   - External resources need close/dispose/cancel behavior and error-path cleanup.

6. Dependency direction.
   - Domain and policy objects depend inward on stable contracts.
   - Adapters depend outward on SDKs and protocols.
   - Orchestrators depend on public module APIs, not internals.

## Structure Evidence Record

For every non-trivial new or changed file/object/function/signature, record:

- Main file owner and rejected alternate owners.
- Oversized file/object/function assessment.
- Split decision: none, sibling, parent-child, strategy/policy, adapter/port, value object, state machine, collaborator object, collapse/inline.
- File granularity decision: keep together, split, merge into owner, keep separate with boundary, collapse/inline, or reject both split and merge.
- Split/merge decision evidence: owner/lifecycle/invariant/collaborator/change-reason comparison, public contract, side-effect boundary, import/export before/after, navigation cost before/after, test boundary before/after, and rejected alternative.
- Signature decision: parameters, boolean traps, weak types, return contract, error model.
- Side-effect boundary decision.
- Collaborator count and lifecycle owner.
- State, invariant, and lifecycle decision.
- Public behavior tests that prove the new structure.
