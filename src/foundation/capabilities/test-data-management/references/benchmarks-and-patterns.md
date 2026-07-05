# Test Data Management Benchmarks And Patterns

Use this reference when `test-data-management` needs more detail than the main `SKILL.md` should carry efficiently. Keep the main body focused on selection, ownership, evidence, output, and quality gates; use this file for fixture/factory ownership, side-effect cleanup, privacy classification, deterministic controls, parallel and volume data, graph/memory/trajectory coupling, and anti-pattern review.

## Benchmark Anchors

- xUnit Patterns: inline, delegated, implicit, shared fixtures; Object Mother and Test Data Builder tradeoffs.
- FactoryBot, factory_boy, Bogus, Faker, and JavaFaker: factory defaults, traits, sequences, lazy attributes, and seeded synthetic data.
- Testcontainers and ephemeral infrastructure: per-suite real dependencies with isolated test state.
- Database Cleaner, pytest transactions, Django transactional tests, and Rails transactional fixtures: rollback, truncation, deletion, and adapter-specific cleanup.
- OWASP and secret-scanning practice: committed fixtures, snapshots, and logs must not contain credentials, tokens, or sensitive identifiers.
- GDPR data minimization and NIST de-identification: production personal data needs lawful basis and documented transformation before non-production use.
- k6 and Gatling data feeders: per-worker or per-virtual-user slicing prevents collisions under load.
- CI sharding and parallel test runners: data namespaces and deterministic seeds must survive different execution order and worker count.

## Fixture Ownership Matrix

| Data artifact | Good owner | Evidence required | Watchouts |
| --- | --- | --- | --- |
| Inline values | Single test | Assertion reason and deterministic value. | Duplicated magic values across suites. |
| Factory default | Owning domain/module test package | Required fields, sensible defaults, sequence strategy. | Over-specified defaults that hide behavior. |
| Factory trait | Behavior-specific test group | Trait purpose, fields changed, consumer tests. | Trait explosion or ambiguous names. |
| Shared read-only seed | Module or integration suite owner | Immutable policy, update owner, reset proof. | Mutable seed state causes order dependencies. |
| Golden file | Contract owner | Schema/version, regeneration command, diff review rule. | Golden hides real PII or stale format. |
| Load-test dataset | Performance test owner | Volume/distribution model, per-worker slicing, cleanup. | Shared rows collide under parallel virtual users. |
| External sandbox records | Integration/E2E owner | Sandbox reset/TTL, unique namespace, quota/cost limit. | Long-lived accounts accumulate state. |

## Side-Effect Cleanup Matrix

| Side effect | Isolation or cleanup | Validation evidence |
| --- | --- | --- |
| Relational DB rows | Transaction rollback, truncation, schema namespace, or delete by test-owned key. | Row count before/after, rollback assertion, or cleanup command output. |
| NoSQL documents/items | Test namespace, TTL, batch delete, or ephemeral table/container. | Query by namespace after cleanup returns zero or accepted residual risk. |
| Cache keys | Unique prefix and delete-by-prefix/TTL; never global flush in shared env. | Key scan for prefix or fake/cache reset proof. |
| Queue messages | Test queue/topic, consumer drain, purge by namespace, or ephemeral broker. | No leftover messages, offset reset, DLQ cleanup proof. |
| Files/object storage | Test temp directory/bucket prefix and recursive delete. | Directory/prefix is empty after teardown. |
| Emails/notifications | Local capture tool or test mailbox with purge. | Mailbox/capture reset evidence. |
| Browser/session storage | Per-test browser context and storage cleanup. | New context or storage empty assertion. |
| External sandbox | Reset API, unique namespace, TTL cleanup job, or quota monitor. | Reset response, cleanup task, or residual owner. |

## Determinism Controls

- Clock: inject fixed clock, freeze time, or pass explicit timestamps; avoid assertions against wall-clock `now`.
- Randomness: seed faker/random libraries and record the seed used for generated assertions.
- Identifiers: use deterministic test-run prefixes, named IDs, or seeded UUID provider.
- Locale and timezone: set environment/test runner locale and timezone where formatting appears in assertions.
- Ordering: specify sort key and tie-breaker instead of relying on insertion order or auto-increment order.
- Async and TTL: avoid arbitrary sleep; use controllable timers, polling with timeout, or fake clock.
- Parallelism: include worker ID, test ID, tenant namespace, or VU index in generated data.

## Privacy And Secret Classification

| Data category | Default treatment | Escalate when |
| --- | --- | --- |
| Names, emails, addresses, phone numbers | Synthetic values under reserved domains such as `example.test`. | Free text or copied production samples appear. |
| Credentials, tokens, API keys, cookies | Never in fixtures; use fake tokens or secret manager test credentials. | Any credential-like value is committed or printed. |
| Payment card, bank, tax, health, government IDs | Use provider-approved test values only. | Real regulated data or realistic-but-unapproved values appear. |
| Tenant/customer/account IDs | Synthetic IDs with namespace and no real customer mapping. | IDs map to real users/accounts or support screenshots. |
| Production dump | Prohibited by default. | Owner-approved sanitized transformation, retention, access control, and scan evidence exist. |
| Reference catalog data | Immutable approved reference data. | It contains personal, tenant, contract, or confidential business data. |

## Graph, Memory, And Trajectory Coupling

Treat graph, memory, and execution trajectory as discovery inputs until current source confirms them.

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current tests, fixtures, factories, seed files, cleanup hooks, schemas, and CI runner config are inspected. | Graph proximity is treated as proof that fixture ownership or cleanup is safe. |
| Project memory | Prior fixture pattern names unchanged modules, schemas, cleanup commands, and flake history with freshness evidence. | Memory predates schema, parallel runner, fixture refactor, or sandbox policy changes. |
| Execution trajectory | Cleanup, test, secret scan, or parallel run executed after the final test-data edit. | Output predates current fixture/seed/cleanup changes or covers only one happy path. |
| CI history | Flake or failure signal maps to current test names, runner, shard, and date range. | Signal lacks reproducible command or current fixture path. |
| Generated artifacts | Golden files, snapshots, seeded datasets, and generated fixtures were regenerated or inspected. | Generated files were not refreshed after schema/factory changes. |

Strong outputs state which graph, memory, and trajectory inputs were accepted, rejected, or left unknown.

## Validation Evidence Patterns

- Fixture ownership: list consumer tests for each shared fixture/factory and state who updates it when schema changes.
- Cleanup proof: run the cleanup command or assert no records/keys/files/messages remain under the test namespace.
- Determinism proof: run the same test twice with the same seed or document the deterministic controls used.
- Parallel proof: run with multiple workers/shards or provide a namespace/collision analysis with not-verified limits.
- Privacy proof: scan fixture/golden/test data paths for secrets and known PII patterns or record why scanning was not available.
- Sandbox proof: reset API result, quota/retention owner, and cleanup window for external test accounts.
- Volume proof: dataset generation command, row count, distribution assumptions, per-VU slice rule, and retention cleanup.

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| Global shared mutable user fixture. | Test order dependency and hard-to-debug flakes. | Factory-created per-test user or immutable reference seed. |
| Schema-complete fixture with dozens of irrelevant fields. | Unrelated schema changes break tests and obscure intent. | Minimal factory defaults plus behavior-specific overrides. |
| `flushall`, truncate, or drop command in shared CI. | Other suites lose state mid-run. | Namespace cleanup or isolated container/schema. |
| Unseeded Faker or random UUID in asserted output. | Non-reproducible snapshots and logs. | Seeded generator or explicit deterministic ID. |
| Production data copied to fixtures. | Privacy exposure and irreversible repository leak. | Synthetic generator or governed sanitized dataset. |
| Queue/cache/file side effects omitted from teardown. | Later tests read stale state or delayed jobs. | Side-effect inventory and per-layer cleanup. |
| Load test users share one credential. | Virtual users collide and hide capacity behavior. | Per-VU data slice with unique accounts and cleanup. |
| Old fixture reused from memory without source check. | Stale fields and cleanup assumptions persist. | Confirm current schema, tests, cleanup hooks, and validation freshness. |

## Handoff Boundaries

- Use `test-strategy` when the unresolved question is which test layers are required.
- Use `integration-testing` when the real DB/cache/queue/API seam behavior needs execution design.
- Use `contract-testing` when fixtures must align to API/provider schemas.
- Use `e2e-testing` when full browser journey data setup and teardown must be designed.
- Use `regression-testing` when test data protects a known historical failure.
- Use `security-privacy-gate` when regulated data, production dumps, credentials, or retention policies are in scope.
- Use `performance-budgeting` when generated data volume, distribution, or test runtime has budget impact.
- Use `backup-recovery` when production-scale data integrity drills or restore datasets are the primary concern.
