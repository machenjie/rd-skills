# Test Strategy Benchmarks And Patterns

Use this reference when `test-strategy` needs benchmark-backed layer selection, omission review, affected-test strategy, assertion quality, or anti-pattern detail beyond the compact `SKILL.md` body. Keep the main body focused on routing, output, evidence, and quality gates.

## Benchmark Anchors

- Test Pyramid: keep most deterministic local logic in unit tests, use fewer integration tests, and reserve E2E for critical user journeys.
- Testing Trophy: integration tests often give the best confidence-to-cost ratio for product behavior that crosses components or services.
- Google Testing Blog test sizes: small tests avoid IO; medium tests use local process boundaries or data stores; large tests span systems and are expensive.
- Consumer-Driven Contract Testing: use Pact or equivalent contract evidence when consumers depend on request/response, event, SDK, or generated-client shape.
- Mutation testing: assertion quality is credible when a removed branch, inverted permission, wrong mapping, or swallowed failure would make a test fail.
- OWASP ASVS/API Security: auth, object authorization, input validation, session, and abuse paths need negative and adversarial cases.
- DORA change failure and MTTR: release-blocking validation should map to the failure consequence and rollback/recovery expectation.

## Layer Selection Matrix

| Risk or behavior | Primary proof | Add when | Do not substitute |
| --- | --- | --- | --- |
| Pure calculation, validation, mapping, or state transition | Unit or property test with edge and negative cases. | Mutation/property test for money, permission, or critical calculations. | E2E-only proof. |
| Service orchestration with ports, repositories, or adapters | Service integration or component-level integration with realistic fakes/contracts. | Real DB/cache/queue/provider integration when adapter behavior matters. | Mock-call-only assertions. |
| API, event, SDK, generated client, or public export | Contract test, schema diff, generated-client check, compatibility fixture. | Consumer inventory and old/new version matrix. | Unit-only local handler test. |
| Migration, backfill, destructive data change, or rollback | Forward, rollback, and data-integrity migration test. | Production-like shape, representative volume, backup/recovery handoff. | Clean empty-schema migration only. |
| Frontend user behavior | Component or route test using accessibility/user behavior queries. | E2E smoke for critical cross-route journey. | CSS selector or snapshot-only proof. |
| External provider, webhook, queue, file, email, or sandbox integration | Contract or sandbox integration plus failure simulation. | Retry, idempotency, DLQ, reconciliation, and cleanup proof. | Local mock with impossible provider responses. |
| Security, permission, tenant, export, payment, or abuse path | Denied/invalid/abuse matrix and security review evidence. | Threat model, manual specialist review, or adversarial integration test. | Happy-path allowed role test. |
| Performance, concurrency, capacity, or SLO risk | Benchmark/profile/load/stress evidence tied to threshold. | Race/idempotency or soak proof when shared state changes. | Timing intuition or one small local run. |

## Omission Review Pattern

| Omitted level | Accept when | Reject when |
| --- | --- | --- |
| Unit | Behavior is pure wiring with no branch, rule, mapping, or state transition; integration proof can fail for the same risk. | Local logic, permission, calculation, mapper, or state transition changed. |
| Integration | No real boundary behavior changed, and mocks are contract-aligned. | DB/cache/queue/provider semantics, transactions, serialization, timeouts, or retries matter. |
| Contract | No public API/event/SDK/schema/export consumer can observe the change. | Response shape, error taxonomy, generated client, event payload, or package export changed. |
| E2E | Lower layers prove behavior and no critical journey orchestration changed. | User journey, routing, auth/session, file download, payment, or destructive action changed. |
| Migration/rollback | No data shape, schema, backfill, cleanup, restore, or old/new coexistence change. | Schema/data changes or rollback state is asymmetric. |
| Security | No auth, permission, tenant, input/output encoding, secret, upload, or abuse surface changed. | Security-relevant branch or trust boundary is touched. |
| Performance | No hot path, fan-out, query, concurrency, cache, batch, or payload-size behavior changed. | Latency, throughput, memory, query count, or capacity can regress. |

## Assertion Quality

- Prefer public behavior assertions over private helper calls, mock-call counts, snapshots, or existence checks.
- Name the failure a test must catch: denied role, expired token, duplicate submit, rollback failure, stale cache, timeout, partial failure, bad mapping, or incompatible schema.
- For material behavior, state the mutation-style check: branch removed, permission inverted, mapper field omitted, retry disabled, transaction order changed, or error swallowed.
- Avoid tests that can pass when the behavior is removed because they assert only setup, wiring, or mock interaction.
- Record what each test proves and what it does not prove when using fakes, mocks, snapshots, manual checks, or partial CI commands.

## Anti-Patterns To Reject

| Anti-pattern | Failure | Correction |
| --- | --- | --- |
| "Add tests" task with no behavior or risk. | Agent writes broad happy-path coverage that cannot close release risk. | Convert to risk-to-test map with commands and owners. |
| One green E2E test for a matrix of business rules. | Local branches and denied paths remain untested. | Unit/integration matrix plus one critical journey smoke. |
| Unit-only proof for schema/API/event change. | Consumers or generated clients break outside the module. | Contract/generated-client check plus compatibility fixture. |
| Migration tested only on empty schema. | Existing data, constraints, and rollback fail in production. | Representative forward/rollback/data-integrity test. |
| Coverage percentage used as release evidence. | Critical path can remain unasserted. | Changed-code-to-test map and behavior-sensitive assertions. |
| Stale validation copied from before final edit. | Green report proves old code, not current code. | Rerun mapped validators or disclose not verified. |

## Efficiency Guardrail

Do not load this reference for a trivial low-risk edit with one obvious command. Load it when choosing layers, reviewing omitted levels, evaluating assertion quality, or resolving disagreement about unit vs integration vs contract vs E2E evidence.
