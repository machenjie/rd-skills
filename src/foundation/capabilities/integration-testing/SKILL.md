---
name: integration-testing
description: Verifies real boundaries across modules, APIs, databases, services, and infrastructure seams, including failure and rollback paths where relevant.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "60"
changeforge_version: 0.1.0
---

# Mission

Prove that connected components work correctly together across **real boundaries**: real database queries, real serialization, real auth context, real transaction behavior, real cache/queue semantics, and controlled external adapters. Keep dependencies deterministic through test containers, contract-calibrated fakes, local emulators, or controlled stubs, and verify success, rollback, timeout, retry, and partial-failure behavior when those failures can occur.

# When To Use

Use this capability when a change crosses: a controller-service-repository path; a service-to-database boundary with real SQL, constraints, tenant filters, or transactions; a service-to-cache boundary with Redis key structure, TTL, or invalidation; a service-to-queue or consumer boundary with message serialization, acknowledgement, retry, or DLQ routing; a service-to-external-adapter boundary with WireMock, nock, MockServer, or equivalent; auth enforcement through a real filter or principal; or any seam where unit tests cannot validate the behavior that can fail in production.

# Do Not Use When

Do not use this capability to replace fast unit tests for pure business logic. If a rule can be tested without a database, queue, cache, or external call, use `unit-testing`. Do not use it for complete browser journeys across deployed services; use `e2e-testing`. Do not use it as the primary compatibility gate for public API or event contracts; use `contract-testing`. Do not run integration suites against shared staging state that the test cannot isolate, reset, or own.

# Stage Fit

Use during implementation, bug-fix regression design, code review, and release readiness when the risky claim depends on real wiring rather than mocked behavior. In planning, it selects the narrowest real boundary that can fail for the named risk. In implementation/review, it rejects mock-only proof for SQL, transaction, cache, queue, auth, serialization, and adapter behavior. In release, it records validation freshness, CI infrastructure requirements, and residual untested seams. Repository graph, project memory, and execution trajectory may identify likely test locations or prior failures, but current source, fixtures, configuration, and command output must confirm the evidence before it is trusted.

# Non-Negotiable Rules

- **Test the real boundary that carries the risk.** If the risk is "does the SQL query return the right rows under the right conditions," test against a real database in a test container, not a mocked repository.
- **External dependencies must be controlled.** Use Testcontainers or local emulators for real infrastructure, WireMock/nock/MockServer for HTTP, and in-process fakes only when they are checked against a contract or calibrated source. Shared staging dependencies are not deterministic integration evidence.
- **Include failure, timeout, rollback, retry, and partial-write paths.** A transaction that fails midway must roll back completely. A consumer that throws must not commit the offset. A cache failure must not corrupt the canonical store.
- **Isolate test data and side effects.** Each test owns setup and cleanup through transaction rollback, truncation, unique schema/namespace, queue topic isolation, cache key namespace, or container lifecycle. Mutable cross-test state is a flake source.
- **Assert state and side effects, not only response status.** Assert response, database row fields, emitted event payload, queue acknowledgement, cache invalidation, retry job, and external request body where each matters to correctness.
- **Auth context must be production-realistic.** Controller and service integration tests include caller identity, roles, tenant/object scope, and denied cases. A superadmin or disabled filter path proves a different behavior.
- **Validation freshness is part of the test result.** If code, migrations, fixtures, config, generated schemas, container image versions, or test data changed after the run, the integration evidence is stale until rerun.

# Industry Benchmarks

Anchor against real-boundary testing with Testcontainers/local emulators, HTTP adapter stubbing with WireMock/nock/MockServer, framework slice tests such as Spring Boot/Nest/Django/FastAPI, adapter testing from ports-and-adapters practice, contract-calibrated fakes, DORA stability pressure, and suite-level container reuse. Load [references/checklist.md](references/checklist.md) for quick planning, [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for tool and boundary matrices. Use `examples/example-output.md` only in source-authoring context when the expected output shape is unclear.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Persistence slice | Repository, ORM, migration-adjacent query, tenant predicate, constraint, or transaction path. | Prove real SQL/constraint/transaction semantics and rollback. | DB image/version, fixture owner, query/row assertions, rollback or cleanup proof. | `repository-persistence`, `transaction-consistency` | Mocked repository proof. |
| API/service slice | Controller/service/repository wiring, auth filter, validation, error response, or serialization. | Prove request-to-state behavior through real framework wiring. | HTTP/service call, realistic principal, response/body/header, persisted state, denied case. | `backend-change-builder`, `security-privacy-gate` when auth/data sensitive | Superadmin-only or filter-disabled tests. |
| Queue/cache/event slice | Consumer, producer, Redis/cache, event bus, outbox, retry, offset, DLQ, or invalidation path. | Prove side-effect ordering, acknowledgement, retry, idempotency, and cleanup. | Broker/cache setup, message fixture, ack/commit point, side-effect assertion, failure injection. | `message-queue-design`, `data-side-effect-flow-tracing` | Publish/consume mocks only. |
| External adapter slice | HTTP provider, SDK, webhook, file/object storage, payment/identity sandbox, or local emulator. | Prove adapter request/response mapping and failure translation without live uncontrolled calls. | Stub/emulator source, request-body verification, timeout/error case, redaction boundary. | `integration-change-builder`, `contract-testing` | Real third-party production calls. |
| Regression and release proof | Prior integration defect, CI flake, environment mismatch, stale validation, or release gate. | Reproduce the risky seam, stabilize deterministic infrastructure, and map evidence to final changed paths. | Red/green or historical case, same-pattern scan, final command, freshness, residual risk. | `regression-testing`, `validation-broker`, `execution-trajectory-analysis` | One green happy-path smoke as full proof. |

# Selection Rules

Select this capability when **correctness at real component seams** is the primary risk. Adjacent routing:

- Prefer `unit-testing` when logic has no dependency on real infrastructure or external I/O.
- Prefer `contract-testing` when the primary concern is consumer/provider API compatibility across service boundaries.
- Prefer `e2e-testing` when the primary concern is a complete user journey through the deployed application.
- Prefer `test-data-management` when the primary concern is fixture strategy, test database seeding, synthetic data, or cleanup across a large suite.
- Prefer `regression-testing` when the primary concern is preventing recurrence of a specific known bug; combine it with this capability when the bug depends on a real seam.

# Risk Escalation Rules

Escalate when the integration path involves financial writes, authorization across tenant/object boundaries, migration or rollback correctness, queue consumers that trigger irreversible actions, outbox/event ordering, cache as a derived state source, external payment/identity/provider sandboxes, partial transaction failures, or services owned by different teams. Add `contract-testing` when an external contract must remain compatible, `security-privacy-gate` when sensitive data/auth is involved, and `transaction-consistency` when rollback/isolation semantics are the main risk.

# Proactive Professional Triggers

- **Signal:** An "integration" test mocks the repository, ORM, cache, queue, auth filter, or HTTP adapter that carries the named risk. **Hidden risk:** the test validates a fake path while the real seam can fail on constraints, serialization, tenancy, offset, or request shape. **Required professional action:** replace or supplement with a real-boundary test and record what remains mocked. **Route to:** `integration-testing`, `testability-seam-design`. **Evidence required:** boundary map, real dependency or calibrated stub, assertion layers, and residual mocked seam.
- **Signal:** A test uses shared staging data, shared queue topics, global cache keys, or uncontrolled sandbox state. **Hidden risk:** order-dependent flakes and false positives hide real failures. **Required professional action:** define owned fixture setup, namespace, cleanup, and parallel-safety rules. **Route to:** `test-data-management`, `agent-tool-permission-sandbox`. **Evidence required:** data/side-effect inventory, cleanup command, isolation mechanism, and CI parallelism note.
- **Signal:** A service, consumer, or adapter test covers only success while rollback, timeout, retry, DLQ, partial write, or denied auth can occur. **Hidden risk:** the first production failure leaves durable inconsistent state. **Required professional action:** inject the failure at the seam and assert final durable state plus error contract. **Route to:** `transaction-consistency`, `failure-contract-design`, `message-queue-design`. **Evidence required:** failure injection, final DB/cache/queue/event state, retry/DLQ or no-partial-state assertion.
- **Signal:** Project memory, repository graph, or an earlier trajectory says a boundary was tested before later migrations, fixtures, generated schemas, config, or adapter code changed. **Hidden risk:** stale evidence is reused for a different wiring graph. **Required professional action:** reconcile current changed paths with graph/memory/trajectory claims and rerun affected validators after the final edit. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, `validation-broker`. **Evidence required:** accepted/rejected prior claim, changed-path-to-test map, command outcome, freshness after final edit.
- **Signal:** An integration command needs Docker, network, cloud sandbox, local emulator, connector, secret-bearing config, or destructive cleanup. **Hidden risk:** test execution leaks credentials, mutates uncontrolled state, or is not reproducible by CI. **Required professional action:** record permission/sandbox boundary, dry-run or revert path, redaction rule, and CI requirement before running or accepting the evidence. **Route to:** `agent-tool-permission-sandbox`, `delivery-release-gate`, `security-privacy-gate` when sensitive. **Evidence required:** tool/action class, permission state, sandbox boundary, secret redaction, cleanup/revert path.

# Critical Details

The most expensive integration test failure pattern is the "everything is mocked" suite: tests pass, production fails at the real database constraint. Second: shared staging state, where tests pass or fail depending on someone else's data. Third: success-only testing, where the rollback or retry path is first exercised during an incident.

- **Container lifecycle.** PostgreSQL, Redis, Kafka, MongoDB, or LocalStack containers usually belong at suite/class/module scope, not per test method. Reuse containers only when test data isolation remains explicit.
- **Transactional rollback versus truncation.** Transaction rollback is faster but does not cover code paths that commit independently. Truncation or unique schemas are slower but safer for out-of-band commits, queues, and caches.
- **HTTP stub verification.** WireMock/nock/MockServer should verify request method, path, headers, auth, and body fields that affect correctness; a catch-all 200 stub is not adapter proof.
- **Auth precision.** A test JWT, principal, or security context must pass through the same authorization path as production enough to prove roles, tenant/object scope, and denied cases.
- **Event and queue proof.** "Published" is incomplete; assert payload contract, ordering where material, ack/commit point, retry or DLQ behavior, and idempotency for duplicate delivery.
- **CI realism.** Record Docker socket/Docker-in-Docker, image versions, emulator ports, resource limits, parallelism, and environment variables so local evidence can be reproduced in CI.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| Repository is mocked in "integration" test | Real SQL, constraints, joins, isolation, and tenant predicates are untested. |
| Test against shared staging DB | Order-dependent flakes and false positives from uncontrolled data. |
| Only success path tested | Rollback, retry, DLQ, and compensation bugs surface only under incident pressure. |
| Auth filter disabled in controller test | Authorization rules are absent from the evidence. |
| Assert only HTTP status | 201 response can pass while no row, event, or cache state is correct. |
| Container spun up per test method | CI runtime becomes too slow; developers skip the suite. |
| Catch-all HTTP stub | Adapter sends wrong payload but test still passes. |

# Failure Modes

- **Mocked persistence:** repository mock returns success while real PostgreSQL rejects a NULL, unique, tenant, or foreign-key constraint.
- **Shared state flake:** shared database, queue, cache, or sandbox data changes under the test and creates non-reproducible pass/fail results.
- **Lost message:** consumer commits the offset before durable processing, then throws; retry and DLQ never happen.
- **Partial write:** transaction rollback is untested and a payment, refund, outbox, or audit record is left inconsistent.
- **Wrong adapter payload:** HTTP stub returns 200 for any body; production provider rejects the real request shape.
- **Auth bypass:** filter or principal is replaced with a privileged shortcut, so denied tenant/object access is never tested.
- **Cache divergence:** database write succeeds but invalidation fails; stale cache becomes the behavior users see.
- **Slow suite spiral:** one container per test or uncontrolled sleeps make the integration suite too slow or flaky for routine CI use.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 routing, mode selection, output, and gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete plan for DB, cache, queue, auth, transaction, adapter, rollback, timeout, or fixture isolation. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when choosing tooling, selecting a boundary pattern, designing container/emulator/stub setup, or comparing isolation and CI performance tradeoffs. Use `examples/example-output.md` only in source-authoring context when the required answer shape is unclear. Do not load references for pure unit tests or trivial routing decisions where no real seam is in scope.

# Output Contract

Return an integration test plan with:

- `mode_selected` (persistence slice / API-service slice / queue-cache-event slice / external adapter slice / regression-release proof)
- `boundary_under_test` (components included, real infrastructure involved, and what unit tests cannot cover)
- `source_evidence` (current source, existing tests, fixtures, config, migrations, repository graph, project memory, execution trajectory, and freshness limits)
- `infrastructure_dependencies` (Testcontainers/local emulator image + version, WireMock/nock/MockServer stubs, in-process fake, or controlled sandbox)
- `isolation_strategy` (transactional rollback, truncation, unique schema/namespace, topic/cache key isolation, container lifecycle, and rationale)
- `data_setup` (seed SQL, factories, repository fixtures, message fixtures, cache keys, per-test setup owner)
- `auth_context` (principal, roles, tenant_id/object scope, scopes, denied-case identity, and how auth is injected)
- `success_cases` (action -> response, DB/cache state, event/message payload, external call verification)
- `failure_cases` (injected constraint, timeout, 4xx/5xx, retry, DLQ, rollback, partial-write, or denied-auth failure -> expected final state)
- `side_effect_assertions` (persistent state, emitted events, queued jobs, ack/commit, cache invalidation, external request body)
- `graph_memory_execution_coupling` (repository graph, project memory, prior summary, and trajectory claims accepted, rejected, stale, partial, or not verified)
- `validation_freshness` (commands, exit codes, artifacts, changed inputs covered, last material edit, stale checks, and not-run status)
- `tool_permission_boundary` (Docker/shell/network/sandbox/connector action class, permission state, cleanup or revert path, and sensitive output redaction rule)
- `performance` (container reuse strategy, parallel safety, suite runtime estimate, resource limits, and CI requirements)
- `what_evidence_proves` (the specific wiring, state transition, rollback, retry, or side effect covered by the real-boundary run)
- `what_evidence_does_not_prove` (browser behavior, production scale, uncontrolled third-party behavior, unknown consumers, or unrelated release readiness)
- `residual_risk` (untested external boundary, production-scale gap, flaky signal, unsupported environment, owner, and next gate)

# Evidence Contract

An integration test is accepted only when the output includes:

- **Integration boundary:** real components exercised together and the seam risk they prove.
- **External boundaries mocked or controlled:** dependencies stubbed, faked, containerized, sandboxed, or explicitly not verified.
- **Data and side-effect state:** fixture ownership, durable state, cleanup, queue/cache/event state, and isolation.
- **Environment isolation:** ephemeral container, local emulator, namespace, transaction rollback, truncation, or cleanup command.
- **Parallel safety:** whether concurrent tests can run without shared-state collisions and why.
- **Failure path:** timeout, transaction rollback, retry, invalid state, denied auth, dependency error, or partial-write behavior when relevant.
- **Boundaries inspected:** source, tests, fixtures, configs, migrations, graph, memory, trajectory, and CI settings used or skipped with reason.
- **Validation evidence:** command, exit code, artifact/output, changed inputs covered, and freshness after final edits.
- **What evidence proves:** wiring and behavior across the selected real boundary.
- **What evidence does not prove:** full browser behavior, production scale, third-party production behavior, alternate services, unknown consumers, or unrelated release readiness.
- **Residual risk and next gate:** untested boundary, owner, compensating control, and handoff target.

# Quality Gate

The integration test plan is complete only when:

1. Real infrastructure or a contract-calibrated controlled substitute is used for the primary boundary under test.
2. External HTTP/provider dependencies are controlled through stubs, local emulators, or approved sandbox paths; uncontrolled production calls are excluded.
3. Test data and side effects are isolated per test or suite with explicit cleanup and parallel-safety rules.
4. Auth context includes realistic principal, roles, tenant/object scope, and denied-case coverage where auth matters.
5. Assertions cover response plus durable state plus emitted events/messages/cache/external request side effects where applicable.
6. At least one failure-path test exists for each risky boundary that can fail through constraint violation, timeout, retry, rollback, partial write, DLQ, or denied auth.
7. Rollback and no-partial-state correctness are asserted after injected failure.
8. Container/emulator/stub lifecycle is suite-aware and efficient enough for CI.
9. HTTP stubs verify request body, auth/header, and path values where those values affect correctness.
10. CI infrastructure requirements are documented, including Docker/emulator availability, ports, resource limits, environment variables, and parallelism.
11. Graph, memory, and execution-trajectory evidence is source-confirmed or marked stale/not verified before it affects the plan.
12. Validation evidence names the command, exit code, inputs covered, final-edit freshness, and what the run does and does not prove.
13. Tool permission/sandbox boundaries, cleanup/revert path, and redaction rules are recorded for shell, Docker, network, connector, sandbox, or secret-bearing actions.

# Benchmark Coverage

This capability covers real database/cache/queue/container testing, API-service slice tests, auth-aware controller tests, transaction rollback proof, event/consumer acknowledgement and DLQ behavior, HTTP adapter stubs, local emulators, contract-calibrated fakes, fixture isolation, CI reproducibility, and validation freshness. Detailed tool matrices and isolation patterns live in [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md).

# Routing Coverage

Route here when the primary risk is provider-internal behavior across a real seam: persistence, cache, queue, auth, transaction, event, adapter, or service wiring. Route away when the main risk is pure logic (`unit-testing`), consumer-visible compatibility (`contract-testing`), complete browser/user journey (`e2e-testing`), fixture ownership (`test-data-management`), or historical defect recurrence without a real-seam design gap (`regression-testing`).

# Used By

- quality-test-gate
- integration-change-builder

# Handoff

Hand off to `contract-testing` for cross-service consumer/provider compatibility; `test-data-management` for shared fixture strategy and test database seeding; `transaction-consistency` for transaction isolation, rollback, and distributed write semantics; `message-queue-design` for ack/retry/DLQ policy; `security-privacy-gate` for auth, tenant, sensitive data, or sandbox risks; `validation-broker` for changed-path-to-validator mapping; and `e2e-testing` for full user journey tests.

# Completion Criteria

The capability is complete when **the real risky seam is exercised with deterministic, isolated infrastructure, both success and failure paths are asserted at the full state level, validation is fresh against the final changed inputs, and the suite can run reliably in CI without uncontrolled external dependencies**.
