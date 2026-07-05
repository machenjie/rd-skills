# Layered Architecture Design Benchmarks And Patterns

Use this reference when `layered-architecture-design` output needs more detail than the `SKILL.md` body should carry efficiently. Keep the main skill body focused on routing, evidence, output contract, and gates; use this file for benchmark anchors, layer responsibility matrices, dependency enforcement examples, business logic placement, graph/memory/trajectory coupling, and anti-pattern review.

## Contents

- Benchmark Anchors
- Layer Responsibility Matrix
- Dependency Direction Enforcement
- Business Logic Placement
- Transaction And Exception Boundaries
- Architecture Exception Review
- Graph, Memory, And Trajectory Coupling
- Review Questions
- Anti-Patterns To Reject
- Handoff Boundaries

## Benchmark Anchors

- Clean Architecture: entities/domain, use cases/application, interface adapters, and frameworks/drivers obey the dependency rule.
- Hexagonal Architecture / Ports and Adapters: the application core is tested through ports without requiring adapters.
- Domain-Driven Design layered architecture: UI/application/domain/infrastructure responsibilities remain distinct; domain owns business behavior.
- Patterns of Enterprise Application Architecture: Service Layer, Repository, Domain Model, Table Module, and Transaction Script are context-dependent choices.
- Onion Architecture: domain core is central; infrastructure depends inward.
- Dependency Inversion Principle: high-level policy depends on abstractions, not low-level infrastructure details.
- Architecture fitness functions: import rules, dependency checks, and CI enforcement keep layer decisions from decaying.
- Framework conventions such as Spring, NestJS, Django, Rails, and .NET can help organize layers but do not prove dependency direction by themselves.
- Test architecture: domain unit tests should run without DB, HTTP server, framework container, queue, filesystem, or external API.

## Layer Responsibility Matrix

| Layer | Owns | Must not contain | Depends on | Typical types |
| --- | --- | --- | --- | --- |
| Presentation | Transport parsing, format validation, auth/session extraction, response mapping. | Business policies, domain state transitions, database queries. | Application. | Controller, handler, resolver, presenter, request/response DTO. |
| Application | Use-case orchestration, transaction boundary, authorization invocation, repository coordination, after-commit event publication. | Business invariants, HTTP details, ORM/driver types. | Domain contracts and injected ports. | UseCase, command handler, query handler, application service, unit of work. |
| Domain | Business invariants, entity lifecycle, value objects, domain services, domain events, calculations. | Framework imports, ORM models, DB sessions, HTTP clients, queues, filesystem, environment config. | Nothing outward; may define ports/contracts. | Entity, aggregate, value object, domain service, repository interface, domain event. |
| Infrastructure | Persistence, external APIs, message producers/consumers, cache/file adapters, framework adapters, exception translation. | Business decisions and domain rule branching. | Domain/application contracts. | Repository implementation, SQL/ORM mapper, HTTP adapter, message adapter, cache adapter. |

## Dependency Direction Enforcement

Correct direction:

```text
Presentation -> Application -> Domain <- Infrastructure
```

Domain may define:

```text
interface OrderRepository {
  findById(id: OrderId): Order | null
  save(order: Order): void
}
```

Infrastructure implements that contract and maps storage models to domain objects. Domain does not import `PostgresOrderRepository`, ORM sessions, database rows, HTTP clients, queue producers, or framework containers.

Enforcement examples:

```text
ArchUnit:
  domain layer may not access presentation, application, or infrastructure packages
  application layer may access domain only
  presentation layer may access application only

Dependency Cruiser:
  forbid from src/domain to src/infrastructure, src/presentation, framework adapters

import-linter:
  contract: domain_no_infrastructure
  forbidden: domain -> infrastructure
```

CI rule: architecture checks are evidence only when the command and final outcome are reported after the final relevant edit. "We follow this convention" is not enforcement.

## Business Logic Placement

| Behavior | Primary layer | Evidence | Watchout |
| --- | --- | --- | --- |
| Parse HTTP body, route param, CLI args, queue envelope. | Presentation. | DTO/request validation and delegation. | Format validation is not a business invariant. |
| Authorize actor for a use case. | Application, using policy/domain inputs. | Policy call before protected data access when required. | Policy implementation may route to auth capability. |
| Coordinate multiple repositories or domain objects. | Application. | Use case name, transaction owner, repository calls. | Application should orchestrate, not own invariant logic. |
| Enforce entity lifecycle transition. | Domain. | Entity/value/domain service method and tests. | Do not duplicate in controllers/services. |
| Compute business price, eligibility, state, or policy. | Domain unless trivial transaction script is justified. | Rule name, owner, test seam. | Avoid rich domain ceremony for simple CRUD. |
| Persist or fetch data. | Infrastructure adapter implementing domain/application port. | Mapping, query, exception translation, integration test. | Do not leak storage models into domain. |
| Publish integration event. | Application/outbox after state is consistent. | Event timing and outbox/after-commit rule. | Domain raises events; it does not publish to Kafka/SNS directly. |

Decision shortcut:

```text
Is it a business invariant, calculation, eligibility rule, lifecycle rule, or policy?
  Put it in domain, unless transaction script is explicitly justified.

Is it use-case orchestration, transaction scope, authorization invocation, or event coordination?
  Put it in application.

Is it transport parsing or response formatting?
  Put it in presentation.

Is it storage, network, queue, file, cache, framework, or environment access?
  Put it in infrastructure.
```

## Transaction And Exception Boundaries

| Concern | Correct owner | Evidence | Failure if wrong |
| --- | --- | --- | --- |
| Unit of work | Application/use case. | Transaction scope names participating repositories and rollback rule. | Repository-local transactions cause partial commits. |
| Domain invariant failure | Domain. | Domain exception or result type independent of DB/framework. | Application duplicates rules and drifts. |
| Infrastructure driver exception | Infrastructure adapter. | Adapter maps driver exception to application/domain error. | Application catches database/vendor types. |
| Event publication | Application/outbox. | Published after commit or stored in outbox inside transaction. | Consumer sees event before source record exists. |
| External API call | Infrastructure adapter invoked by application. | Idempotency/compensation routed when side effect is unsafe. | Transaction cannot roll back external effect. |

## Architecture Exception Review

Layering is a tool, not a religion. Exceptions are acceptable when they are explicit:

| Exception | Accept when | Required containment |
| --- | --- | --- |
| Transaction Script | CRUD/simple workflow has no meaningful invariants or state machine. | Use-case scope, no duplicate business rules, test at service/API boundary. |
| Active Record | Local framework convention is established and domain complexity is low. | No hidden cross-aggregate rules; repository/domain split not pretended. |
| Framework-first modules | Team uses framework modules consistently and tests stay fast. | Domain-like behavior still has an infrastructure-free seam or accepted residual risk. |
| Legacy adapter leak | Short-lived migration bridge. | Owner, expiry/review trigger, and tests that prevent spread. |

Reject exceptions that are unnamed, permanent by accident, copied from old memory, or used to avoid choosing an owner.

## Graph, Memory, And Trajectory Coupling

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current imports, package layout, controllers, services, domain objects, adapters, tests, and architecture check config were inspected. | Graph proximity is used as proof that dependency direction is enforced. |
| Project memory | Prior layering decision names unchanged packages, conventions, enforcement, and date/freshness evidence. | Memory predates framework migration, module split, adapter rewrite, or architecture rule removal. |
| Execution trajectory | Architecture checks and tests ran after the final layer-related edit. | Evidence predates final edits or only covers one happy path. |
| Generated clients/ORM models | Generated boundaries are current and intentionally confined to adapters/DTOs. | Generated types leak into domain or were not regenerated after schema changes. |
| Test evidence | Domain tests run without infrastructure; application tests mock ports; infrastructure tests use real adapter dependencies. | Tests require full framework startup to exercise domain behavior. |

Strong outputs state which graph or memory evidence was accepted, rejected, or left unknown.

## Review Questions

1. Which entry points exist, and what do they parse, validate, and delegate?
2. Which named use cases own orchestration, transaction scope, authorization invocation, and event timing?
3. Which rules are true business invariants, and which domain object/service owns them?
4. Which repository interfaces or ports exist, and where are they defined?
5. Which infrastructure adapters implement those ports and translate vendor exceptions?
6. Which imports prove or disprove dependency direction?
7. Which architecture rule runs in CI, and what does it forbid?
8. Which tests prove domain behavior without DB/framework/network startup?
9. Which layer exceptions are deliberate, owned, and time-bounded?
10. Which source, graph, memory, trajectory, generated, or test evidence remains unverified?

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| Controller branches on business status. | Rule duplicates across delivery mechanisms. | Move orchestration to application and invariant to domain. |
| Domain imports ORM model or DB session. | Domain tests require infrastructure. | Define port/interface and adapter mapping. |
| Application catches `psycopg2`, `Hibernate`, or vendor HTTP exceptions. | Application layer depends on infrastructure details. | Map at adapter boundary. |
| Repository opens its own transaction for each call. | Multi-repository use case can partially commit. | Application unit of work owns transaction. |
| Domain event publishes directly to queue/broker. | Domain depends on infrastructure. | Domain raises event; application/outbox publishes after consistency point. |
| Pass-through service everywhere. | Adds ceremony without behavior protection. | Collapse or justify boundary with current consumers. |
| Rich domain model for trivial CRUD. | Overhead without invariant benefit. | Use transaction script with explicit simplicity rationale. |
| Architecture enforced only by review comments. | Layer drift accumulates. | Add tool rule or name residual risk. |
| Project memory copied without import/test check. | Stale pattern becomes new violation. | Confirm current source and validation freshness. |

## Handoff Boundaries

- Use `module-boundary-design` when business capability ownership, public API, private internals, or cross-module imports are primary.
- Use `architecture-style-selection` when choosing between layered, modular monolith, microservice, event-driven, serverless, or other macro styles.
- Use `service-business-logic` for concrete application service orchestration, transaction sequencing, authorization-first order, events, and external effects.
- Use `domain-logic-implementation` for entity/value/domain service invariants and domain events.
- Use `repository-persistence` for persistence mapping, repository implementation, query behavior, and adapter integration tests.
- Use `transaction-consistency` and `idempotency-retry-design` for distributed transaction, retry, duplicate side-effect, saga, or outbox depth.
- Use `architecture-enforcement-tooling` and `quality-test-gate` for executable import rules, CI integration, and validation freshness.
