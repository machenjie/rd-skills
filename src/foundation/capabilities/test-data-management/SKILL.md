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

# Stage Fit

Owns test-data design during test planning, coding, bug-fix, debugging, implementation review, refactoring, testing, repair, release-readiness, and final handoff when fixture, factory, seed, sandbox, file, cache, queue, generated identifier, clock, randomness, or cleanup behavior can affect correctness, privacy, determinism, or flake risk. In planning, it turns current test structure, source schemas, repository graph, project memory, execution trajectory, fixtures, factories, CI behavior, and external sandbox contracts into a scoped data plan with isolation, cleanup, determinism, privacy, and validation obligations. In coding and refactoring, it keeps fixture/factory ownership, deterministic controls, and cleanup scope aligned with the accepted test data plan instead of letting tests copy stale data helpers. In debugging, separate fixture mutation, missing cleanup, nondeterministic clock/random/locale/ID behavior, sandbox drift, CI sharding, and privacy-scan causes before changing tests. In review and testing, reject shared mutable fixtures, production-data copies, hidden test order dependencies, stale project-memory fixture reuse, reset commands that can affect other suites, and test data plans that cannot map data state to validation evidence. In release-readiness, require fresh validation after the final fixture, factory, seed, cleanup, deterministic-control, privacy, sandbox, or volume-data edit. Hand off when the primary question is test-level selection, integration seam behavior, full E2E journey design, or security/privacy approval for regulated non-production data.

# Non-Negotiable Rules

- **Test data must be deterministic and owned by the test or test suite that needs it.** A fixture or factory that produces different values on different runs causes non-reproducible failures. Owned data means: if the test is deleted, the data is also deleted. Shared test records that outlive any individual test are a liability — they accumulate mutations, cause ordering dependencies, and eventually cause cascading failures across the suite.
- **Tests must be isolated by a reliable mechanism that prevents cross-test contamination.** Isolation mechanisms in order of preference: (1) database transaction rollback (wrap each test in a transaction, roll back after — fastest, zero cleanup required); (2) unique namespace or tenant prefix (all records created by the test share a unique prefix; cleaned up by prefix after test); (3) test-specific database schema or container (Testcontainers, ephemeral Docker container spun up per test suite); (4) in-memory database (SQLite in-memory, H2, fakeredis — fastest, no cleanup needed); (5) sandbox account with reset API. The mechanism must be explicit in the test data design, not assumed.
- **No real user data, credentials, PII, or tokens in test data.** Production data in non-production environments is a regulatory compliance risk (GDPR Article 5(1)(b): purpose limitation; Article 25: data minimization by design). Even "anonymized" production copies frequently retain identifiable values in email addresses, usernames, or free-text fields. All test data must be: synthetically generated using a library (Faker.js, faker-ruby, Bogus, Python Faker), or sanitized/pseudonymized using a documented transformation process. Test data files committed to source control must never contain credentials, API keys, session tokens, or any value that would be a security risk if the repository were public.
- **Define cleanup, rollback, reset, or expiration for every persistent side effect.** A test that writes to a database, file system, cache, message queue, or external API must specify how that side effect is reversed or expired. Cleanup categories: (1) database records — transaction rollback or DELETE by test-owned ID; (2) cache keys — delete by test-owned key prefix or TTL; (3) file system objects — delete by test-owned directory or file name; (4) queue messages — purge by test-owned queue name or consume-and-discard; (5) external sandbox accounts — reset via API or TTL-based expiry; (6) email — use a test mailbox with automatic purge or mailhog/mailpit local capture. Missing cleanup causes "test data debt" — over time, CI databases accumulate thousands of orphaned records that slow queries and cause false failures.
- **Control time, randomness, locale, timezone, and generated identifiers when they affect assertions.** Any test that asserts on a timestamp, a random-generated value, or a locale-formatted string must mock or seed the source of that value. `Date.now()`, `Math.random()`, `uuid()`, `Intl.DateTimeFormat`, and system timezone are all test nondeterminism sources. The pattern: inject a deterministic clock (e.g., `jest.useFakeTimers`, `freezegun`, `timecop`), seed the random number generator to a fixed value, and fix the locale and timezone in the test environment configuration.
- **Fixtures must be scoped to the behavior under test, not to database schema completeness.** A fixture that creates a fully-populated user record with 40 columns to test one email-send behavior is over-specified. Over-specified fixtures fail when unrelated columns are added to the table. Fixtures should set only the fields that matter for the assertion, using sensible defaults for everything else. This is the factory pattern: `UserFactory.build({ email: 'alice@example.com' })` — only the email column matters for the email-send test.
- **Closure evidence must name the test-data validator or test command, validator/tool, artifact or report path, output and exit code or manual review result, changed fixture/factory/seed/cleanup/determinism/privacy/sandbox scope, and freshness after the final test-data edit.** Repository graph, project memory, CI history, or prior green runs are discovery inputs, not proof of current test-data safety.

# Mode Matrix

Select the test-data mode before defining fixtures or cleanup.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Fixture and factory ownership | New/changed factories, fixtures, seeds, golden data, snapshots, or shared test helpers. | Keep data local to the behavior and avoid shared mutable business fixtures. | Owning suite/module, fields used by assertions, default/trait strategy, deletion/update path. | `test-strategy`, `unit-testing`, `code-clarity-maintainability` | Schema-complete fixtures and global object mothers. |
| Persistent side-effect isolation | Tests write DB/cache/file/queue/email/sandbox state or run in parallel. | Prevent cross-test contamination and destructive reset scope. | Side-effect inventory, isolation mechanism, cleanup command, parallel-safety proof. | `integration-testing`, `e2e-testing`, `agent-tool-permission-sandbox` | `flushall`, truncate, or shared reset without owner/scope. |
| Privacy-safe synthetic data | Production copy, sanitized dump, PII, credentials, tokens, payment/health data, or user free text appears. | Block real sensitive data and require synthetic or governed sanitized data. | Data classification, generation/sanitization rule, approved reference data, secret scan or not-verified disclosure. | `security-privacy-gate`, `data-api-contract-changer` | "Anonymized" data without transformation proof. |
| Determinism and flake repair | Time, randomness, UUID, locale, timezone, ordering, external sandbox state, or TTL causes flake risk. | Make reproduced failures and parallel runs deterministic. | Clock/random/ID/locale controls, run-order evidence, seed owner, flake signature. | `regression-testing`, `quality-test-gate`, `execution-trajectory-analysis` | Blind retries or arbitrary sleeps. |
| Volume and performance data | Load, soak, migration, data-quality, benchmark, or per-virtual-user datasets are needed. | Match scale/distribution without leaking production data or causing collisions. | Volume model, synthetic distribution, per-worker/per-VU slicing, cleanup/retention, validator. | `performance-budgeting`, `backup-recovery`, `bigdata-product-extension` when analytics data is primary | Unbounded production dump or shared CSV mutation. |

# Industry Benchmarks

Anchor against xUnit Patterns fixture taxonomy, FactoryBot/builders/traits, seeded Faker libraries, Testcontainers and ephemeral infrastructure, Database Cleaner and transaction rollback strategies, GDPR purpose limitation and data minimization, NIST de-identification guidance, and k6/Gatling per-virtual-user data slicing. Keep this body focused on selection, evidence, output, and quality gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for fixture ownership patterns, side-effect cleanup matrices, privacy classification, deterministic control examples, graph/memory/trajectory coupling, and anti-pattern review.

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

# Proactive Professional Triggers

- **Signal:** A fixture, factory, seed, golden file, or shared test helper is reused from project memory, repository graph proximity, or prior agent trajectory. **Hidden risk:** stale schema, changed defaults, hidden mutation, or unreviewed repair path becomes copied test debt. **Required professional action:** confirm against current source, tests, schema, fixture owners, and validation freshness before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected reuse, freshness limit, and evidence limits.
- **Signal:** Test data persists outside one test process through DB, cache, file, queue, email, browser storage, object storage, or external sandbox. **Hidden risk:** cleanup misses a side-effect layer and creates order-dependent flakes. **Required professional action:** inventory side effects and define cleanup/reset/TTL per layer. **Route to:** `integration-testing`, `e2e-testing`, `quality-test-gate`. **Evidence required:** side-effect map, isolation mechanism, teardown command, parallel-safety statement.
- **Signal:** Production data, sanitized dump, user text, email, token, credential, card, health, location, or tenant data is proposed for non-production tests. **Hidden risk:** privacy or secret exposure through fixtures, snapshots, logs, or committed files. **Required professional action:** block real sensitive data unless governed transformation and owner approval are explicit. **Route to:** `security-privacy-gate`, `secret-configuration-security`. **Evidence required:** data classification, generator/sanitizer, secret-scan or not-verified disclosure, retention.
- **Signal:** A test uses wall-clock time, random values, UUIDs, auto-increment order, locale, timezone, current date, async delay, or TTL in assertions. **Hidden risk:** failures cannot be reproduced and CI order/region changes alter results. **Required professional action:** inject deterministic clock/random/ID/locale controls and record seed ownership. **Route to:** `testability-seam-design`, `regression-testing`. **Evidence required:** deterministic control map, seed, timezone/locale setting, flake proof or residual risk.
- **Signal:** Parallel execution, sharding, load tests, or per-worker data files are introduced. **Hidden risk:** workers collide on shared IDs, mutate shared data, or exhaust sandbox quotas. **Required professional action:** define namespace/per-worker/per-VU slicing and cleanup. **Route to:** `performance-budgeting`, `quality-test-gate`, `agent-tool-permission-sandbox` for destructive cleanup commands. **Evidence required:** worker ID strategy, dataset partitioning, quota/collision check, cleanup owner.
- **Signal:** Prior validation, repository graph, CI history, project memory, or execution trajectory says fixtures are isolated, deterministic, or privacy-safe before a fixture, seed, schema, cleanup hook, sandbox policy, or test runner changes. **Hidden risk:** stale evidence hides a new flake, leak, cleanup gap, or cross-worker collision. **Required professional action:** rerun, replace, or downgrade the proof and record validation freshness. **Route to:** `validation-broker`, `plan-execution-consistency`. **Evidence required:** changed path, validator/report path, exit code or manual artifact, what stale evidence no longer proves, and residual risk owner.
- **Signal:** Cleanup uses truncate, drop, purge, flush, delete-by-prefix, sandbox reset, or bulk fixture regeneration. **Hidden risk:** a test-data repair can destroy another suite's state or erase evidence needed to diagnose a flake. **Required professional action:** classify cleanup scope and require dry-run, namespace, rollback, or bounded destructive-command evidence before execution. **Route to:** `agent-tool-permission-sandbox`, `validation-broker`. **Evidence required:** command, target namespace, dry-run or rollback path, affected suites, exit code, and redaction rule.

# Critical Details

- **The most dangerous test data pattern: shared mutable fixtures.** A shared fixture record that is mutated by one test and read by another creates a test ordering dependency. The test suite passes when run in alphabetical order, fails when run in random order, and takes hours to debug. The fix: make every test that needs mutable state own its own copy (factory-created within the test, cleaned up after).
- **Faker-seeded determinism prevents non-reproducible failures.** Calling `faker.name()` without seeding produces a different name on every run. When a test asserts on a formatted display name, a non-seeded faker call produces a different assertion value on every run. Fix: `faker.seed(12345)` or use a factory with a fixed default value for the asserted field.
- **Cleanup must cover every side effect layer, not just the database.** A test that creates a database record AND writes a cache key AND enqueues a background job has three side effects. Rolling back the database transaction does not clear the cache key or dequeue the background job. The cleanup plan must enumerate all three side effects and specify how each is reversed.
- **External sandbox accounts accumulate state over time if not explicitly reset.** A test suite that creates sandbox payment customers in Stripe without resetting them will eventually hit API rate limits or accumulate thousands of test customers that make debugging impossible. Every sandbox account must have either an API reset call in teardown or a TTL-based cleanup job.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 test-data selection, ownership, and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete test data plan, when cleanup/privacy/determinism coverage is uncertain, or before implementation starts. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when fixture ownership, isolation strategy, privacy classification, deterministic controls, side-effect cleanup, volume data, or graph/memory/trajectory reuse needs depth. Use [examples/example-output.md](examples/example-output.md) only when output shape is unclear. Do not load references for pure routing or trivial wording work where the output contract and quality gate are enough.

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

- **Shared mutable fixture:** Tests pass when run alone but fail after another test mutates a shared fixture, creating hidden ordering dependency.
- **Unseeded generated data:** Non-seeded random values, UUIDs, timestamps, or locale-formatted values make snapshots, logs, and assertions change on every run.
- **Cache cleanup gap:** Cache key written in a test persists after database transaction rollback, so the next test reads stale state.
- **Delayed side effect:** Background job, queue message, email, or file write created in a test runs after teardown and mutates another test's state.
- **Sandbox accumulation:** External sandbox account accumulates test records for months, hits quota or rate limits, and blocks CI or hides cleanup failures.
- **Committed sensitive fixture:** Real email address, token, credential, tenant ID, or user text lands in source-controlled test data and becomes a privacy or secret exposure.
- **Parallel worker collision:** Sharded or parallel tests share an ID namespace, sandbox account, fixture row, or load-test dataset and overwrite each other's data.
- **Stale fixture proof:** Project memory or old validation says factories are isolated, but schema, cleanup, runner, or seed behavior changed after that proof.

# Output Contract

Return a test data plan with:

- `mode_selected` (fixture/factory ownership, persistent side-effect isolation, privacy-safe synthetic data, determinism/flake repair, or volume/performance data)
- `data_scope` (test suites, behaviors, owning module, persistent stores, external sandboxes, excluded data sources, and cleanup boundary)
- `source_evidence` (current tests, fixtures, factories, seeds, schemas, repository graph, project memory, execution trajectory, CI behavior, and freshness limits)
- `data_strategy` (per test suite: strategy type from selection matrix, justification)
- `isolation_mechanism` (per persistent side effect: mechanism, parallel-safe confirmation)
- `factory_definitions` (per domain entity: required fields, optional fields with defaults, sequences for unique values)
- `cleanup_checklist` (per side effect layer: DB, cache, file, queue, email, external sandbox — cleanup method and owner)
- `determinism_controls` (clock mock, faker seed, locale/timezone freeze, identifier strategy)
- `privacy_classification` (per data category: synthetic/sanitized/approved-reference; no real PII)
- `volume_and_performance` (if load test data: parameterized data files, per-VU slice strategy)
- `flake_risks` (ordering dependencies, race conditions, external API reliability, TTL expiry race)
- `fixture_ownership_map` (each fixture/factory/seed/golden file owner, consumer tests, mutation policy, deletion/update path)
- `changed_data_to_validation_map` (each fixture/factory/seed/cleanup/determinism/privacy decision mapped to test, validator, scan, or residual risk)
- `validation_commands` (test-data, fixture, secret-scan, cleanup, parallel-run, or manual-review command; validator/tool; artifact/report path; relevant output; exit code or manual result; changed test-data scope; and freshness verdict)
- `handoff_boundaries` (what belongs to test strategy, integration/E2E design, security/privacy, data migration, backup/recovery, or performance gates)
- `reuse_and_freshness_judgment` (accepted/rejected graph, memory, or execution-trajectory evidence and why)
- `evidence_limits` (what was not verified: production-like volume, external sandbox cleanup, CI sharding, secret scans, real parallel execution, or long-lived TTL behavior)

# Evidence Contract

Close a test-data-management change only when the output names selected mode, data scope, current source/test/fixture evidence inspected, boundaries inspected, graph/memory/execution reuse judgment, data ownership, isolation mechanism, cleanup coverage for every side-effect layer, privacy classification, deterministic controls, parallel-safety status, changed-data-to-validation map, validation evidence, handoff boundaries, residual risk, and evidence limits. A fixture list or "use factories" statement is not sufficient evidence.

State what evidence proves, what evidence does not prove, reuse and placement rationale for any fixture/factory/seed/golden/sandbox choice, behavior preservation for existing tests and CI runners, and the next gate before handoff. Validation evidence must include command names, validator/tool, artifact/report path, relevant output, exit code or manual review result, changed test-data scope, and freshness after the final material edit; stale graph-only, memory-only, or prior green-run proof must be downgraded to residual risk.

# Benchmark Coverage

Behavior improvement should be validated structurally: weak test-data plans usually reuse shared mutable fixtures, omit cleanup for cache/files/queues/sandboxes, rely on production-like dumps without privacy proof, use unseeded random/time values, hide fixture ownership in shared helpers, or skip parallel-safety evidence. Improved outputs must name mode, source evidence, fixture ownership, side-effect cleanup, privacy controls, deterministic controls, validation mapping, and handoff boundaries while keeping detailed examples in references.

# Routing Coverage

Route here when the primary work is fixture/factory/seed/golden-data ownership, deterministic generated data, test database state, cleanup/reset rules, privacy-safe synthetic data, side-effect cleanup, sandbox data, load-test data slicing, or flake repair caused by shared data. Guard against over-routing by handing off when the primary concern is test layer selection (`test-strategy`), real boundary behavior (`integration-testing`), complete browser/user journey setup (`e2e-testing`), API compatibility fixtures (`contract-testing`), historical bug protection (`regression-testing`), regulated data approval (`security-privacy-gate`), or production-scale recovery drills (`backup-recovery`).

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
11. Selected mode, data scope, source evidence, fixture ownership, and cleanup boundary are explicit.
12. Repository graph, project memory, and execution trajectory evidence are current-source confirmed or marked not verified.
13. Every fixture, factory, seed, side-effect cleanup, deterministic control, and privacy decision maps to validation evidence or named residual risk.
14. Validation commands, validators, artifacts/reports, output and exit code or manual result, changed test-data scope, and freshness are recorded for every accepted fixture, factory, seed, cleanup, deterministic-control, privacy, sandbox, parallel-safety, and volume-data claim.
15. Handoff boundaries and evidence limits are explicit so the plan is not over-claimed as test strategy, integration proof, privacy approval, live parallel proof, or production-scale validation.

# Used By

- quality-test-gate
- data-middleware-change-builder

# Handoff

Hand off to `integration-testing` for test execution design; `e2e-testing` for end-to-end test data flows; `backup-recovery` for data integrity drills that require production-scale data; `security-privacy-gate` when regulated data handling in test environments requires formal review.

# Completion Criteria

The capability is complete when **every test value is deterministic, isolated to its owning test, synthesized or sanitized to protect privacy, and accompanied by an explicit cleanup mechanism for every persistent side effect it creates**.
