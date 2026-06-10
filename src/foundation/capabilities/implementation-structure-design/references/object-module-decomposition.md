# Object And Module Decomposition

Use this reference when a change adds or modifies a file, object, function, signature, side-effect boundary, collaborator set, stateful object, or large service. It is intentionally loaded only for implementation-planning, code-review, and refactoring cases where structure quality is uncertain.

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

1. Sibling objects.
   - Use when responsibilities are peer capabilities that can change independently.
   - Examples: `OrderCancellationPolicy`, `OrderRefundPolicy`, `OrderShippingPolicy`.
   - Rule: siblings do not reach into each other's internals.

2. Parent-child objects.
   - Use when one object owns the public lifecycle or orchestration and child objects hide detailed sub-behavior.
   - Parent coordinates; child owns detail. Parent must not become a pass-through dumping ground.

3. Strategy or policy.
   - Use when algorithm or rule families are current, named, and expected to vary.
   - Reject if there is only one implementation and the abstraction exists only because a branch looked untidy.
   - Require contract tests for current variants.

4. Adapter or port.
   - Use for external systems, protocols, SDKs, formats, framework APIs, persistence, network calls, clocks, queues, and side effects.
   - Domain and policy objects depend on ports or data contracts, not concrete infrastructure.

5. Value object.
   - Use when a parameter group, state group, or business value has independent invariants.
   - Use to replace scattered primitives when callers need the invariant, not merely to shorten a parameter list.

6. State machine.
   - Use when an object has more than three meaningful states, non-trivial transitions, invalid transitions, guards, or transition side effects.
   - Pair with `state-machine-modeling` for domain lifecycles.

7. Collaborator object.
   - Use when constructor dependencies, method clusters, or side effects show the current object is coordinating unrelated collaborators.
   - Split by collaborator role only when each collaborator role maps to a responsibility, not just to reduce constructor parameter count cosmetically.

8. Collapse or inline.
   - If a new object has no state, invariant, lifecycle, protocol role, current variation, or meaningful collaborator boundary, collapse to a function, module operation, or existing owner.

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
