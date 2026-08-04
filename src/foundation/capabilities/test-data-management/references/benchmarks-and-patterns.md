# Test Data Management Benchmarks And Patterns

Load this reference when fixtures, factories, golden data, generated volume, external sandbox records, privacy, parallel namespaces, or cleanup changes. Do not load it for a single inline value owned entirely by one test.

## Artifact Ownership

| Artifact | Use when | Required controls |
| --- | --- | --- |
| Inline value | One test needs a meaningful deterministic example. | Assertion reason; no unrelated schema completeness. |
| Factory/default/trait | A module owns repeated valid setup or behavior-specific variants. | Minimal defaults, named overrides, sequence/identity policy, consumers, and schema-update owner. |
| Shared seed/reference data | Many tests need immutable approved data. | Read-only contract, version/update owner, reset/isolation proof, and no hidden tenant state. |
| Golden/snapshot/recording | Exact serialized/rendered compatibility is the claim. | Contract/schema version, regeneration command, semantic diff review, freshness, and redaction. |
| Load/parallel dataset | Distribution, volume, or concurrency is under test. | Generator/seed, per-worker/VU slice, collision policy, cleanup, and production-assumption limits. |
| External sandbox record | Real provider behavior is needed. | Unique scope, credentials owner, reset/TTL, quota/cost, retention, and residual state owner. |

## Isolation, Privacy, And Determinism

Inventory relational rows, documents, cache keys, queue messages/DLQ, files/objects, emails/notifications, sessions/browser storage, and external records created by the test. Clean each through transaction, owned namespace, explicit delete, TTL/lifecycle, or disposable resource, and verify the owned scope is empty or declare an accepted residual. When the environment is shared beyond the test's owned namespace, use owned-scope cleanup instead of a global destructive reset.

Control clocks, timezones, locales, random generators, and seeds when assertions depend on them.
Control IDs, run prefixes, sort tie-breakers, async or TTL timers, worker identity, and environment state when collisions depend on them.
Treat one repeated seed as proof only for that seed.

Use synthetic reserved-domain identities and provider-approved test values.
Keep real, usable, or sensitive credentials, tokens, API keys, and session or cookie material out of fixtures and retained output.
Use inert token or cookie values only when a test exercises their protocol semantics.
Relevant semantics include parsing, expiry, signatures, `SameSite`, domain, and path.
Label those values as non-secret fixtures.
Prohibit production dumps by default.
Require an approved purpose, de-identification evidence, minimization, access controls, encryption, retention or deletion, mapping-risk review, and an accountable owner for exceptions.

## Evidence And Proof Limits

Inspect current schemas, factories, fixtures, cleanup hooks, CI sharding, sandbox policy, and generated artifacts.
Do not treat secret scans as proof of de-identification.
Treat namespace cleanup as proof only for the queried namespace.
Keep collision analysis unverified without a parallel run.
Keep synthetic volume unverified without a validated distribution.

Reject mutable global users, schema-complete overfixtures, unseeded asserted output, and copied production samples.
Reject queue, cache, or file cleanup omissions, shared load credentials, and stale goldens.
Reject broad reset commands that can affect another suite.

Route layer selection to test-strategy, real seams to integration-testing, and schema fixtures to contract-testing. Route browser-journey setup to e2e-testing, historical triggers to regression-testing, and regulated data to security-privacy-gate. Route volume budgets to performance-budgeting and restore datasets to backup-recovery.
