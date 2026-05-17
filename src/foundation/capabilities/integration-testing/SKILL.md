---
name: integration-testing
description: Verifies real boundaries across modules, APIs, databases, services, and infrastructure seams, including failure and rollback paths where relevant.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "60"
changeforge_version: 0.1.0
---

# Mission

Prove that connected components work correctly together across **real boundaries** — real database queries, real serialization, real auth context, real transaction behavior — while keeping external dependencies deterministic through test containers, fakes with contract checks, or controlled stubs; and verifying not only success paths but rollback, timeout, and partial-failure behavior where those failure modes can occur.

# When To Use

Use this capability when a change crosses: a controller-service-repository path (end-to-end inside the backend); a service-to-database boundary (real SQL, real constraints, real transactions); a service-to-cache boundary (Redis key structure, TTL, eviction); a service-to-queue or consumer boundary (message serialization, consumer acknowledgement, DLQ routing); a service-to-external-adapter boundary (HTTP client to a third party, instrumented with WireMock or equivalent); or any change where the real behavior at a seam cannot be validated by unit tests alone.

# Do Not Use When

Do not use this capability to replace fast unit tests for pure business logic — if a rule can be tested without a database or external call, test it without one (unit test; faster feedback). Do not build slow full-stack browser tests here — use `e2e-testing` for complete user journeys. Do not write integration tests against shared staging environments that you do not control — flaky shared dependencies defeat the determinism requirement.

# Non-Negotiable Rules

- **Test the real boundary that carries the risk.** If the risk is "does the SQL query return the right rows under the right conditions," test against a real database in a test container — not a mocked repository. Mocking the repository proves only that you can call the mock correctly.
- **External dependencies must be controlled.** Use Testcontainers (PostgreSQL, Redis, Kafka, MongoDB, LocalStack) for real infrastructure; WireMock or nock for HTTP dependencies; in-process fakes validated against consumer contracts for service dependencies. Never test against shared staging databases in integration test suites.
- **Include failure, timeout, rollback, and partial-write paths.** A transaction that fails midway must roll back completely. A message consumer that throws must not commit the offset. A cache write that fails must not corrupt the canonical store. These paths must be explicitly tested.
- **Isolate test data.** Each test must set up its own data and clean up after itself. Options: transactional rollback (wrap each test in a transaction; roll back at teardown); truncation between tests; separate schema per test run; Testcontainers with one container per test class. Never share mutable state between tests.
- **Assert side effects, not only response status.** A 201 Created response is insufficient. Assert: the database row was created with the correct fields; the event was emitted; the cache was invalidated; no orphaned records were created. Assert the full state contract, not only the HTTP status.
- **Auth context must be realistic.** Controller integration tests must include an authenticated principal with the correct roles and tenant scope. Testing with no auth or with superadmin bypasses the authorization rules that are part of the correct behavior under test.

# Industry Benchmarks

Anchor against: **Testcontainers** (testcontainers.org; Java, Python, Go, .NET, Node.js) — spin up real PostgreSQL/Redis/Kafka/MongoDB containers per test run; identical to production engine version; deterministic; no shared state. **WireMock** (wiremock.org; Java/.NET) — HTTP mock server; scenario/state-based mocking; verify request count; validate request bodies. **nock** (Node.js) — HTTP interceptor for Node; intercepts `http.request`; supports request body assertion; verify all interceptors used. **pytest-django** / **@nestjs/testing** / **Spring Boot @SpringBootTest(webEnvironment=RANDOM_PORT)** with `@Transactional` — transactional test rollback; test slices (@WebMvcTest, @DataJpaTest) for narrow boundary tests. **Robert C. Martin "Clean Architecture"** — Ports & Adapters; adapter tests prove the adapter (repository, HTTP client) works correctly against the real infrastructure; domain tests never touch infrastructure. **Newman (Postman Collection Runner)** — API integration tests from collections; suitable for contract verification after deployment. **Fowler "Integration Contract Tests"** — test doubles must honour the interface contract of the real dependency; if the fake behaves differently from the real service, the test is misleading. **DORA Research** — test stability (low flakiness rate) is a predictor of deployment frequency; flaky integration tests are a deployment bottleneck. **Testcontainers Reuse** (`TESTCONTAINERS_RYUK_DISABLED=true` + `.withReuse(true)`) — container reuse across test runs for performance; safe when each test isolates its own data.

### Integration Test Scope Selection Matrix

| Boundary under test | Test approach | Infrastructure required | Isolation method |
| --- | --- | --- | --- |
| Controller → Service → Repository → DB | Full slice test (real DB) | Testcontainers PostgreSQL/MySQL | Transaction rollback per test |
| Repository SQL queries | Repository unit test (real DB) | Testcontainers PostgreSQL | Transaction rollback per test |
| Message consumer → DB | Consumer test with test broker | Testcontainers Kafka or in-process broker | Truncation per test |
| HTTP adapter to external API | HTTP adapter test | WireMock / nock stub server | WireMock stub reset per test |
| Service to cache | Cache integration test | Testcontainers Redis | FLUSHDB per test |
| Auth enforcement | Controller slice test with auth | Real auth filter; test JWT or test principal | N/A — state is stateless |
| Transaction rollback on failure | Failure-path integration test | Testcontainers PostgreSQL | Assert no row committed |
| Event emission | Domain event test | In-process event bus or Testcontainers Kafka | Event capture assertion |

### Integration Test Structure Template

```
Given / Arrange:
  - Seed test data (SQL fixtures, repository.save(), factory function)
  - Configure WireMock stub (if external HTTP)
  - Set auth context (test principal with correct roles and tenant)

When / Act:
  - Call the real HTTP endpoint (or service method directly for narrow tests)
  - Perform the action under test

Then / Assert (minimum 3 assertion layers):
  1. Response: status code, response body fields, headers
  2. Persistent state: query the DB directly; assert row created/updated/deleted
  3. Side effects: events emitted, cache invalidated, external API called (WireMock verify)

Teardown:
  - Transaction rollback OR explicit DELETE/TRUNCATE
  - WireMock reset / nock cleanAll()
  - Testcontainer lifecycle managed at class/suite level (not per test)

Failure-path test structure:
  - Inject failure: WireMock returns 503; DB constraint violation; timeout via stub
  - Assert: rollback — no partial state persisted
  - Assert: retry behavior triggered (if applicable)
  - Assert: error response format matches RFC 7807 contract
  - Assert: DLQ event emitted (if consumer test)
```

# Selection Rules

Select this capability when **correctness at real component seams** is the primary risk. Adjacent routing:

- Prefer `unit-testing` when the logic under test has no dependencies on real infrastructure or external I/O.
- Prefer `contract-testing` when the primary concern is consumer/provider API compatibility across service boundaries.
- Prefer `e2e-testing` when the primary concern is a complete user journey through the deployed application.
- Prefer `test-data-management` when the primary concern is fixture strategy, test database seeding, and cleanup across a large test suite.
- Prefer `regression-testing` when the primary concern is preventing recurrence of specific known bugs.

# Risk Escalation Rules

Escalate when the integration path involves: financial writes (payment records, ledger entries, refunds); authorization enforcement across tenant boundaries; data migration scripts that modify live schema; queue consumer logic that triggers irreversible external actions; rollback correctness on partial transaction failures; or the integration spans two services owned by different teams (contract testing also required).

# Critical Details

The most expensive integration test failure pattern is the "everything is mocked" suite — tests pass; production fails at the real database constraint. Second most expensive: "shared staging DB" — tests pass intermittently because other tests or developers wrote conflicting data. Third: "success-only testing" — the rollback path was never tested; a bug surfaces only when a batch job fails halfway through and leaves orphaned records.

- **Testcontainers startup overhead.** PostgreSQL Testcontainer starts in ~2-5 seconds. Shared across the test class (not spun up per test). Use `@Shared` in Spock, `@ClassRule` in JUnit 4, `@Container` with `@Testcontainers` in JUnit 5, or module-level fixture in pytest. One container per test suite, not per test method.
- **WireMock request body assertion.** WireMock can verify that the HTTP request sent to the external dependency had the correct body — not just that a request was made. Use `verify(postRequestedFor(urlEqualTo("/payments")).withRequestBody(matchingJsonPath("$.amount", equalTo("100"))))`.
- **Transactional rollback vs truncation.** Transactional rollback (wrap test in transaction; roll back) is faster but only works if your code does not explicitly commit mid-test (e.g., uses `REQUIRES_NEW`). Truncation is slower but always safe. Know which applies to your transaction semantics.
- **Auth context precision.** A controller integration test that bypasses auth entirely is testing a different security model than production. Always test with a realistic principal. If your test JWT cannot be verified by the filter, your auth filter is not in the test path.
- **Event assertion.** An event was "emitted" does not mean it was correctly formatted. Assert the event payload fields match the contract. Use an in-process event capture list or a Testcontainers Kafka consumer to read back the emitted message.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| Repository is mocked in "integration" test | Tests only mock interaction, not real SQL; constraint violations, wrong joins never discovered |
| Test against shared staging DB | Flaky; other developers' data causes false failures; not repeatable in CI |
| Only success path tested | Rollback bug undetected; partial write leaves orphaned rows in production |
| No auth context in controller test | Authorization rules never exercised; production enforces auth; test environment does not |
| Assert only HTTP status, not DB state | 201 Created returned but row not actually committed; silent failure in edge cases |
| Container spun up per test method | 100 tests × 5s startup = 500s test suite; unacceptable CI feedback time |
| WireMock not verified | External API called with wrong payload; test passes; production integration broken |

# Failure Modes

- Repository mock returns success; real PostgreSQL rejects NULL constraint; production fails on first insert in deployment.
- Shared staging database has leftover data from another developer's test run; integration test returns wrong rows; false positive.
- Consumer offset committed before processing completes; exception thrown; record lost; no retry; message silently dropped.
- Transaction rollback on failure not tested; payment capture partially committed; refund records missing; financial discrepancy.
- WireMock stub returns 200 for any body; external API called with wrong amount; stub does not verify; production sends wrong charge amount.
- Auth filter bypassed in test; authorization rule never exercised in CI; role-based access bug ships to production.
- Testcontainer spun up per test; 400-test suite takes 30 minutes; developers skip tests locally; CI becomes the only test run.

# Output Contract

Return an integration test plan with:

- `boundary_under_test` (components included; real infrastructure involved; what unit tests cannot cover)
- `infrastructure_dependencies` (Testcontainers: image + version; WireMock stubs; in-process fakes)
- `isolation_strategy` (transactional rollback / truncation / separate schema; rationale)
- `data_setup` (seed SQL / factory functions / repository fixtures; per-test setup method)
- `auth_context` (test principal: roles, tenant_id, scopes; how JWT or security context is injected)
- `success_cases` (action → expected: response, DB state, events, external calls verified)
- `failure_cases` (injected failure → expected: rollback assertion; no partial state; error response format)
- `side_effect_assertions` (DB row fields verified; events payload verified; WireMock request body verified)
- `cleanup` (rollback / truncation / WireMock reset; container lifecycle)
- `performance` (container reuse strategy; parallel test safety; estimated suite runtime)
- `ci_requirements` (Docker-in-Docker / Docker socket; resource requirements; environment variables)

# Quality Gate

The integration test plan is complete only when:

1. Real infrastructure (not mocks) used for the primary boundary under test.
2. External HTTP dependencies controlled via WireMock/nock (not real external endpoints).
3. Test data isolated per test; no shared mutable state between tests.
4. Auth context includes realistic principal with correct roles and tenant scope.
5. Assertions cover response + persistent DB state + emitted events/messages.
6. At least one failure-path test per risky boundary (constraint violation, timeout, rollback).
7. Rollback correctness asserted: after failure, no partial state persists.
8. Container lifecycle managed at suite/class level; not per test method.
9. WireMock stubs verify request body where body content matters to correctness.
10. CI infrastructure requirements documented (Docker availability, resource limits).

# Used By

- quality-test-gate
- integration-change-builder

# Handoff

Hand off to `contract-testing` for cross-service consumer/provider compatibility; `test-data-management` for shared fixture strategy and test database seeding; `transaction-consistency` for distributed transaction rollback behavior; `e2e-testing` for full user journey tests.

# Completion Criteria

The capability is complete when **the real risky seam is exercised with deterministic, isolated infrastructure, both success and failure paths are asserted at the full state level (not just status codes), and the suite runs reliably in CI without shared external dependencies**.
