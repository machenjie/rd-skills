---
name: test-data-management
description: Designs deterministic, isolated, privacy-safe, cleanup-aware test data through fixtures, factories, seeds, and reset rules.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "63"
changeforge_version: 0.1.0
---

# Mission

**Design test data so that every test value is deterministic, isolated to its test or suite, synthesized or sanitized to protect privacy, and accompanied by an explicit cleanup or reset mechanism** — preventing flaky tests caused by shared mutable state, test ordering dependencies caused by leaked data, privacy breaches caused by real user data in non-production environments, and non-reproducible failures caused by uncontrolled randomness or time-dependence.

# When To Use

Use this capability when: a test suite needs database records, fixtures, factories, or seeded data; a change introduces new database tables, columns, or relationships that require test data migration; tests involve file system objects, message queue messages, cache entries, email delivery, webhook payloads, or external sandbox accounts that persist beyond the test lifecycle; parallel test execution is being introduced and data isolation must be guaranteed; a test uses randomness, current time, generated identifiers, or locale-sensitive values that affect assertion correctness; or production data is being proposed as a source for test data and must be reviewed for privacy compliance.

# Do Not Use When

Do not use this capability for: testing business logic that requires no external state (pure functions, value object validation — use in-memory unit tests with no data layer); designing the test level strategy (which tests to write at which layer — use `test-strategy`); integration or end-to-end test design beyond the data layer (use `integration-testing` or `e2e-testing`).

# Non-Negotiable Rules

- **Test data must be deterministic and owned by the test or test suite that needs it.** A fixture or factory that produces different values on different runs causes non-reproducible failures. Owned data means: if the test is deleted, the data is also deleted. Shared test records that outlive any individual test are a liability — they accumulate mutations, cause ordering dependencies, and eventually cause cascading failures across the suite.
- **Tests must be isolated by a reliable mechanism that prevents cross-test contamination.** Isolation mechanisms in order of preference: (1) database transaction rollback (wrap each test in a transaction, roll back after — fastest, zero cleanup required); (2) unique namespace or tenant prefix (all records created by the test share a unique prefix; cleaned up by prefix after test); (3) test-specific database schema or container (Testcontainers, ephemeral Docker container spun up per test suite); (4) in-memory database (SQLite in-memory, H2, fakeredis — fastest, no cleanup needed); (5) sandbox account with reset API. The mechanism must be explicit in the test data design, not assumed.
- **No real user data, credentials, PII, or tokens in test data.** Production data in non-production environments is a regulatory compliance risk (GDPR Article 5(1)(b): purpose limitation; Article 25: data minimization by design). Even "anonymized" production copies frequently retain identifiable values in email addresses, usernames, or free-text fields. All test data must be: synthetically generated using a library (Faker.js, faker-ruby, Bogus, Python Faker), or sanitized/pseudonymized using a documented transformation process. Test data files committed to source control must never contain credentials, API keys, session tokens, or any value that would be a security risk if the repository were public.
- **Define cleanup, rollback, reset, or expiration for every persistent side effect.** A test that writes to a database, file system, cache, message queue, or external API must specify how that side effect is reversed or expired. Cleanup categories: (1) database records — transaction rollback or DELETE by test-owned ID; (2) cache keys — delete by test-owned key prefix or TTL; (3) file system objects — delete by test-owned directory or file name; (4) queue messages — purge by test-owned queue name or consume-and-discard; (5) external sandbox accounts — reset via API or TTL-based expiry; (6) email — use a test mailbox with automatic purge or mailhog/mailpit local capture. Missing cleanup causes "test data debt" — over time, CI databases accumulate thousands of orphaned records that slow queries and cause false failures.
- **Control time, randomness, locale, timezone, and generated identifiers when they affect assertions.** Any test that asserts on a timestamp, a random-generated value, or a locale-formatted string must mock or seed the source of that value. `Date.now()`, `Math.random()`, `uuid()`, `Intl.DateTimeFormat`, and system timezone are all test nondeterminism sources. The pattern: inject a deterministic clock (e.g., `jest.useFakeTimers`, `freezegun`, `timecop`), seed the random number generator to a fixed value, and fix the locale and timezone in the test environment configuration.
- **Fixtures must be scoped to the behavior under test, not to database schema completeness.** A fixture that creates a fully-populated user record with 40 columns to test one email-send behavior is over-specified. Over-specified fixtures fail when unrelated columns are added to the table. Fixtures should set only the fields that matter for the assertion, using sensible defaults for everything else. This is the factory pattern: `UserFactory.build({ email: 'alice@example.com' })` — only the email column matters for the email-send test.

# Industry Benchmarks

Anchor against: **xUnit Patterns (Gerard Meszaros)** — Fixture types: inline, delegated, implicit, shared; Object Mother pattern; Builder pattern. **FactoryBot (Ruby)** — declarative factory definitions; trait-based variation; `build` vs. `create` strategy; sequences for unique values; lazy attribute evaluation. **Faker.js / Python Faker / JavaFaker** — locale-aware synthetic data; seeded determinism (`faker.seed(42)`); realistic names, emails, addresses without real PII. **Testcontainers (Java, Go, Python, Node.js)** — ephemeral Docker containers for integration test databases, message brokers, caches; guaranteed isolation; no shared state between test suites. **Database Cleaner (Ruby) / django-pytest-transactions** — strategies: truncation, transaction rollback, deletion; strategy selection by database adapter. **GDPR — Article 5(1)(b) and Article 25** — purpose limitation; data minimization by design; prohibition on using real personal data in test environments without explicit lawful basis. **NIST SP 800-188 (De-identification of Personal Information)** — pseudonymization and anonymization standards for non-production data. **k6 / Gatling test data management** — parameterized data files (`users.csv`); shared virtual user data isolation; per-VU data slices to prevent concurrent collision.

### Test Data Strategy Selection Matrix

| Strategy | Isolation | Determinism | Cleanup | PII Risk | Parallel-Safe | Best For |
| --- | --- | --- | --- | --- | --- | --- |
| In-memory (SQLite, H2, fakeredis) | Full | Full | None needed | Zero | Yes | Unit/fast integration; pure logic tests |
| Transaction rollback | Per-test | Full | Auto on rollback | Low (no real data) | Yes (separate TX per test) | Integration tests on real schema |
| Namespace/prefix isolation | Per-test | Full | DELETE by prefix | Low | Yes | Multi-tenant systems; stateless test DBs |
| Testcontainers / ephemeral container | Per-suite | Full | Container teardown | Zero | Yes (separate containers) | Full integration; message brokers; caches |
| Shared seeded DB (read-only) | Suite-level | Full | None (immutable) | Medium (sanitize) | Yes (reads only) | Reference data; catalog lookups |
| Sandbox account (external API) | Per-test-run | Partial | API reset or TTL | Low | Risk: concurrent tests may collide | E2E tests against third-party APIs |
| Production data copy | None | N/A | N/A | **HIGH — prohibited** | N/A | **Never — privacy violation** |

### Isolation Mechanism Decision Tree

```
Does the test write to a persistent store (DB, cache, file, queue)?
  NO  → In-memory or pure function; no isolation mechanism needed
  YES → Is the store a relational database?
        YES → Does the ORM/test framework support transaction rollback?
              YES → Use transaction rollback strategy (fastest)
              NO  → Use unique namespace prefix + DELETE cleanup
        Is the store a cache (Redis, Memcached)?
              YES → Use unique key prefix per test; delete by prefix in teardown
        Is the store a message queue?
              YES → Use test-specific queue name; purge in teardown; or use in-memory broker
        Is the store a file system?
              YES → Use test-specific temp directory (os.tmpdir/test-id); delete in teardown
        Is it an external third-party API?
              YES → Use sandbox mode; does sandbox support reset API?
                    YES → Call reset in teardown
                    NO  → Use unique identifiers with TTL expiry; document cleanup SLA
```

# Selection Rules

Select this capability when **data setup, isolation, or cleanup is a source of test risk or flakiness**. Route to `test-strategy` for deciding which test levels are required for a change. Route to `integration-testing` for integration test design beyond data management. Route to `e2e-testing` for end-to-end test data concerns. Route to `security-privacy-gate` when test data handling touches regulated personal data.

# Risk Escalation Rules

Escalate when: production data is proposed as test data (GDPR/privacy violation — must block and require synthetic data); a test environment has access to production credentials or tokens (credential exposure risk — must isolate); test data involves payment card numbers, SSNs, health records, or other regulated categories (PCI-DSS, HIPAA, GDPR — specific pseudonymization requirements); parallel test execution is introduced without explicit isolation verification (data contamination risk — must verify isolation mechanism is parallel-safe); or a data reset/cleanup operation is destructive (drops tables, truncates in shared environments) and could affect other teams or CI pipelines.

# Critical Details

- **The most dangerous test data pattern: shared mutable fixtures.** A shared fixture record that is mutated by one test and read by another creates a test ordering dependency. The test suite passes when run in alphabetical order, fails when run in random order, and takes hours to debug. The fix: make every test that needs mutable state own its own copy (factory-created within the test, cleaned up after).
- **Faker-seeded determinism prevents non-reproducible failures.** Calling `faker.name()` without seeding produces a different name on every run. When a test asserts on a formatted display name, a non-seeded faker call produces a different assertion value on every run. Fix: `faker.seed(12345)` or use a factory with a fixed default value for the asserted field.
- **Cleanup must cover every side effect layer, not just the database.** A test that creates a database record AND writes a cache key AND enqueues a background job has three side effects. Rolling back the database transaction does not clear the cache key or dequeue the background job. The cleanup plan must enumerate all three side effects and specify how each is reversed.
- **External sandbox accounts accumulate state over time if not explicitly reset.** A test suite that creates sandbox payment customers in Stripe without resetting them will eventually hit API rate limits or accumulate thousands of test customers that make debugging impossible. Every sandbox account must have either an API reset call in teardown or a TTL-based cleanup job.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| `SELECT * FROM users WHERE email = 'alice@test.com'` hardcoded in test | Fails if alice's row was mutated by a previous test; ordering dependency | `user = UserFactory.create(email: 'alice@test.com')` — owned by this test |
| Random `uuid()` as test user ID with no seed | Different ID on every run; snapshot tests fail; logs are unsearchable | Fixed ID per test (`test-user-001`) or seeded UUID generator |
| Test copies 500k rows from production to staging | Real names, emails, phone numbers; GDPR Article 25 violation | Synthetic data via Faker.js seeded to match volume and distribution |
| `redis.flushall()` in teardown on shared CI Redis | Clears other tests' data mid-run; causes cascading failures across test suite | Unique key prefix per test (`test:{test_run_id}:{key}`); delete by prefix only |
| Integration test hits external payment sandbox without reset | Stripe sandbox accumulates 50k test customers; rate limit hit; test suite blocked | `stripe.customers.del(testCustomerId)` in teardown; or use Stripe mock library |
| Fixture creates 40-column record for test asserting on one field | Fixture fails when unrelated column added; 39 fields carry no test value | Factory: `OrderFactory.build({ status: 'pending' })` — only status matters |

# Failure Modes

- Tests pass when run alone; fail when run after another test that mutated a shared fixture.
- Non-seeded random data causes snapshot test to produce a new snapshot on every run.
- Cache key written in test persists after transaction rollback; next test reads stale value.
- Background job enqueued in test runs after test teardown; modifies state of next test.
- Sandbox payment account accumulates test data over 6 months; rate limit blocks CI.
- Real email address in test data committed to repository; repository made public; PII exposed.

# Output Contract

Return a test data plan with:

- `data_strategy` (per test suite: strategy type from selection matrix, justification)
- `isolation_mechanism` (per persistent side effect: mechanism, parallel-safe confirmation)
- `factory_definitions` (per domain entity: required fields, optional fields with defaults, sequences for unique values)
- `cleanup_checklist` (per side effect layer: DB, cache, file, queue, email, external sandbox — cleanup method and owner)
- `determinism_controls` (clock mock, faker seed, locale/timezone freeze, identifier strategy)
- `privacy_classification` (per data category: synthetic/sanitized/approved-reference; no real PII)
- `volume_and_performance` (if load test data: parameterized data files, per-VU slice strategy)
- `flake_risks` (ordering dependencies, race conditions, external API reliability, TTL expiry race)

# Quality Gate

The test data plan is complete only when:

1. Every test suite has an explicit isolation mechanism with parallel-safe confirmation.
2. All factory definitions specify required fields and unique-value sequences.
3. Cleanup checklist covers all side effect layers (DB, cache, file, queue, email, sandbox).
4. No real PII, credentials, or tokens appear in test data.
5. Clock, randomness, and locale are controlled for all time/random-sensitive assertions.
6. External sandbox accounts have a teardown or TTL-based cleanup strategy.
7. Fixtures are scoped to the behavior under test (no over-specified fixtures).
8. Tests are confirmed to pass in any execution order (no ordering dependencies).
9. Privacy classification is documented for every data category used in tests.
10. Volume data for load tests uses parameterized files with per-VU data slice isolation.

# Used By

- quality-test-gate
- data-middleware-change-builder

# Handoff

Hand off to `integration-testing` for test execution design; `e2e-testing` for end-to-end test data flows; `backup-recovery` for data integrity drills that require production-scale data; `security-privacy-gate` when regulated data handling in test environments requires formal review.

# Completion Criteria

The capability is complete when **every test value is deterministic, isolated to its owning test, synthesized or sanitized to protect privacy, and accompanied by an explicit cleanup mechanism for every persistent side effect it creates**.
