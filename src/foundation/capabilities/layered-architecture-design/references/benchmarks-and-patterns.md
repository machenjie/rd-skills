# Layered Architecture Benchmarks And Patterns

Load this reference when layer ownership, dependency direction, transaction/effect placement, exception translation or a bounded layering exception changes. The repository’s selected contract is authoritative; no universal directory or arrow diagram is imposed.

## Layer Ownership

| Responsibility | Typical owner in a layered/clean design | Reject/route when |
| --- | --- | --- |
| Transport/presentation | Parse protocol, map DTO/error, invoke one use case, render response. | It owns domain rules, persistence or provider workflows. |
| Application/use case | Authorize/scoped lookup, orchestrate domain/repository/ports, own transaction and typed outcome. | It duplicates invariant authority or imports delivery details. |
| Domain/value/policy | Own business invariants, identity/value semantics and lifecycle decisions without infrastructure dependencies. | Rule needs storage/network/framework access or domain ownership is unresolved. |
| Repository/adapter/infrastructure | Implement persistence/external protocols, resource lifecycle and failure translation behind inward-owned contracts. | Storage/provider types leak into policy/application/public contracts. |
| Mapper/schema/generated boundary | Translate intentional model/contract shapes and confine generated types. | One model is reused across conflicting invariants or compatibility owners. |

## Dependency, Transaction, And Failure Contract

- Define allowed dependency direction from the current architecture and enforce public-only cross-boundary imports. Domain/policy does not depend on UI/framework/database/SDK details; adapters implement contracts rather than owning them.
- The use case owns transaction/Unit of Work when state must commit together. External effects occur after commit or through an outbox/owned relay unless a documented atomicity model proves another order.
- Translate infrastructure/provider errors at the adapter/repository boundary, application outcomes at the use case, and protocol status/body at presentation. Preserve cause internally without leaking secrets or implementation details.
- Query/read paths state permission, consistency, projection and side-effect behavior; command paths state invariant, persistence, event/effect and rollback behavior.

## Placement, Exceptions, And Enforcement

| Signal | Required treatment |
| --- | --- |
| Business invariant in controller/repository/adapter | Move authority to domain/policy or explicitly route to `domain-logic-implementation`. |
| Orchestration in domain object | Move effect/transaction ordering to application service unless domain truly owns the lifecycle action without infrastructure. |
| Framework/generated type crossing inward | Translate the crossing at a named boundary and expose the intentional stable contract selected for inward use. |
| Simple Transaction Script or Active Record | Allow when rules and transaction scope stay simple under the current framework convention; contain mapping, failure and transaction ownership explicitly. |
| Framework-first legacy area | Contain framework types behind an owned boundary with tests and an expiry/revisit trigger instead of requiring a risky wholesale rewrite. |
| Layer exception | Name need, exact allowed edge, owner, consumer, risk, enforcement, expiry/review trigger and removal path. |
| Static enforcement | Use applicable import/architecture/compiler rules plus source review; run after final edit and cover the intended packages. |

Directory proximity, annotations, diagrams and passing unit tests do not prove layer ownership. Static rules prove only covered imports, not reflection, dynamic/generated/runtime calls or behavior. Record current callers, allowed/forbidden edges, public surface, validation and residual owner.

Route object/file placement to `implementation-structure-design` and cross-module boundaries to `module-boundary-design`. Route concrete use-case/Transaction Script orchestration to `service-business-logic`, persistence to `repository-persistence`, and atomicity to `transaction-consistency`. Route duplicate/retry behavior to `idempotency-retry-design`, model translation to `model-boundary-mapping`, and effects to `data-side-effect-flow-tracing`. Route enforcement tooling to `architecture-enforcement-tooling`.

Reject controller-to-repository shortcuts without an owned use-case contract, domain imports of ORM/HTTP/SDK types, and hidden repository commits. Also reject unproven provider calls inside transactions, raw infrastructure errors at clients, generated models as domain truth, and permanent unowned layering exceptions.
