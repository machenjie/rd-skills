# Integration Testing Benchmarks And Patterns

Load this reference when choosing integration test tooling, selecting a real-boundary pattern, designing container/emulator/stub setup, or comparing isolation and CI performance tradeoffs. Keep routine routing and closure requirements in `SKILL.md`.

## Benchmark Anchors

- **Testcontainers**: real PostgreSQL, MySQL, Redis, Kafka, MongoDB, LocalStack, and similar dependencies in disposable containers with pinned image versions.
- **Local emulators**: LocalStack, Azurite, in-memory brokers, or provider emulators when production service behavior is not required and emulator limits are stated.
- **WireMock / MockServer / nock**: controlled HTTP stubs with request method, path, header, auth, body, and scenario-state verification.
- **Framework slice tests**: Spring Boot `@SpringBootTest`, `@DataJpaTest`, Nest `@nestjs/testing`, Django/pytest-django, FastAPI/TestClient, Rails request specs, and similar framework-supported slices.
- **Ports and adapters testing**: adapter tests prove repository, HTTP client, queue consumer, and cache adapters against real or calibrated infrastructure while domain logic remains unit-tested.
- **Fowler integration contract tests**: fakes and stubs must honor the real dependency contract or be backed by a contract test.
- **DORA stability pressure**: flaky or excessively slow integration suites reduce deployment confidence; deterministic infrastructure and bounded runtime are quality requirements.

## Boundary Selection Matrix

| Boundary under test | Test approach | Infrastructure | Isolation method |
| --- | --- | --- | --- |
| Controller -> service -> repository -> DB | API/service slice | Testcontainers PostgreSQL/MySQL | Transaction rollback or truncation |
| Repository query/constraint | Persistence slice | Testcontainers DB matching production major version | Transaction rollback; seeded rows per case |
| Service -> cache | Cache slice | Testcontainers Redis or local emulator | Key namespace plus `FLUSHDB` only in owned DB |
| Producer/consumer -> broker -> DB | Queue/event slice | Testcontainers Kafka/RabbitMQ/SQS emulator | Unique topic/queue and per-test message keys |
| HTTP adapter -> provider | Adapter slice | WireMock, MockServer, nock, or sandbox stub | Stub reset per test and request verification |
| Auth enforcement | API/service slice with real filter/principal | Framework test auth or signed test JWT | Stateless identity plus denied-case fixture |
| Transaction rollback | Failure-path integration test | Real DB plus injected exception/constraint | Assert no partial durable state |
| Outbox/event ordering | Service/event slice | DB plus captured event bus or broker | Assert write-before-publish or publish-after-commit policy |

## Integration Test Structure Template

```text
Given / Arrange:
  - Seed owned data through SQL, factory, repository, or message fixture.
  - Start or reset container, emulator, stub, topic, cache namespace, and auth context.
  - Record expected tenant/object scope, idempotency key, and side-effect targets.

When / Act:
  - Call the real endpoint, service boundary, consumer, repository, or adapter.
  - Inject failure when testing timeout, constraint, retry, rollback, or denied auth.

Then / Assert:
  1. Response or return value: status, body fields, headers, error contract.
  2. Durable state: DB/cache/queue/outbox rows, TTLs, offsets, payload fields.
  3. Side effects: emitted event, retry job, DLQ record, cache invalidation, external request body.

Teardown:
  - Roll back, truncate owned tables, delete namespace/topic/cache keys, reset stubs, and stop per-suite infrastructure.
```

## Isolation Patterns

| Pattern | Best for | Tradeoff |
| --- | --- | --- |
| Transaction rollback per test | Repository and service tests without independent commits | Fast, but misses code using separate transactions or async side effects |
| Truncation between tests | DB writes with explicit commits or multiple transactions | Reliable but slower; requires owned table list |
| Unique schema/database | Parallel DB suites and migration-sensitive tests | Strong isolation; setup cost is higher |
| Namespaced cache keys | Redis/cache tests in shared container | Fast; cleanup must avoid broad destructive reset |
| Unique topic/queue per suite | Broker tests and parallel consumers | Avoids message collision; needs lifecycle cleanup |
| Stub reset per test | HTTP adapter tests | Prevents scenario leakage; must verify every expected request |
| Container per suite/class | Most integration suites | Efficient; requires per-test data isolation |

## CI And Performance Controls

- Pin container image major/minor versions to match production-compatible engines.
- Start containers at suite/class/module scope unless test isolation requires a fresh instance.
- Avoid arbitrary sleeps; wait on observable readiness, message arrival, or state transition with bounded polling.
- Run expensive integration suites on changed modules and scheduled full suites when the repository supports affected-test selection.
- Record Docker socket or Docker-in-Docker requirement, ports, memory, CPU, environment variables, and network restrictions.
- Separate local smoke integration checks from full release gates when runtime cost is high, and state what each proves.

## Failure Injection Patterns

- DB constraint violation: seed conflicting data or null/invalid fields and assert no partial writes.
- Transaction rollback: throw after the first durable write and assert final state is unchanged.
- Timeout: stub provider delay beyond configured timeout and assert retry, error taxonomy, and no duplicate side effect.
- Queue retry/DLQ: make handler fail deterministically, assert ack/commit behavior, retry count, and DLQ payload.
- Cache failure: disable or stub cache write/read and assert canonical store remains correct.
- Auth denial: use valid identity without object/tenant permission and assert no state change or data leak.
- Duplicate delivery: send same message or idempotency key twice and assert exactly-once externally visible outcome.

## Fixture Freshness Fields

Record these fields when integration evidence depends on generated data, provider fixtures, or prior evidence:

- source path or fixture owner;
- dependency image/emulator/stub version;
- schema or migration version;
- captured_at or generated_at when using recorded responses;
- redaction status for sensitive payloads;
- validation command and exit code;
- last material edit after the run;
- known limitations and residual owner.
