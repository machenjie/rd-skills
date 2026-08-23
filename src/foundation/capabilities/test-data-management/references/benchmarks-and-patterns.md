# Test Data Management Benchmarks And Patterns

Load this Reference for a named fixture ownership, isolation, privacy, determinism, volume, external sandbox, or cleanup decision; skip a single inline value owned by one test.

## Artifact Ownership

| Artifact | Use and controls |
| --- | --- |
| Inline value | One deterministic example; state its assertion reason. |
| Factory/default/trait | Repeated valid setup; name minimal defaults, overrides, identity policy, consumers, and schema owner. |
| Shared seed | Immutable shared data; require version owner, reset/isolation proof, and no hidden tenant state. |
| Golden/snapshot | Serialized/rendered compatibility; bind schema version, regeneration command, semantic diff, freshness, and redaction. |
| Load/parallel set | Volume/distribution/concurrency; bind generator/seed, worker slice, collision policy, cleanup, and production limits. |
| External sandbox record | Provider behavior; bind unique scope, credential owner, reset/TTL, quota/cost, retention, and residual owner. |

## Isolation, Privacy, And Determinism

- Inventory created rows, documents, keys, queue/DLQ items, files, notifications, sessions, and external records; clean only an owned transaction, namespace, resource, or TTL scope and prove or disclose residue.
- Control clocks, zones, locales, randomness, IDs, prefixes, ordering, timers, workers, and environment state when the oracle depends on them; a repeated seed proves only that seed.
- Use synthetic reserved-domain identities and provider-approved values.
- Label inert secret/cookie fixtures and preserve tested parsing, expiry, signature, `SameSite`, domain, or path semantics.
- Keep usable credentials and production samples out. Any protected-data exception needs approved purpose, de-identification, minimization, access/encryption, retention/deletion, mapping-risk review, and owner.

## Evidence And Proof Limits

- Inspect current schemas, factories, fixtures, cleanup hooks, CI sharding, sandbox policy, and generated artifacts.
- Secret scans do not prove de-identification; namespace cleanup proves only that namespace.
- Keep collision and volume claims unverified without parallel and validated-distribution evidence.
- Reject mutable global users, schema-complete overfixtures, unseeded asserted output, stale goldens, unowned side effects, shared load credentials, and resets reaching another suite.
- Route proof-level choice to `test-strategy`, real seams to integration testing, schema fixtures to contract testing, browser journeys to e2e testing, regressions to regression testing, regulated data to `security-privacy-gate`, volume budgets to performance budgeting, and restore data to backup recovery.
