---
name: contract-testing
description: Requires API, schema, event, and external contract changes to protect consumer expectations and compatibility through executable contract evidence.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "61"
changeforge_version: 0.1.0
---

# Mission

Turn every API, schema, event, and integration boundary into an **executable compatibility gate** — with consumer-driven expectations that run in CI, breaking-change detection before deployment, and a clear compatibility evolution strategy — so that independent provider and consumer release cycles never produce silent regressions in production.

# When To Use

Use this capability when a change adds, modifies, or removes: HTTP/REST endpoints, gRPC/Protobuf methods or messages, AsyncAPI event/command payloads, webhook contracts, message schema (Kafka, SQS, SNS), database-exposed views or stored procedures, SDK method signatures, DTO transfer shapes, OpenAPI operation request/response, external third-party integration contracts, pagination contracts, versioned URL segments (`/v2/`), or error response shapes.

# Do Not Use When

Do not use this capability for testing provider business logic (internal service behavior behind the boundary — use integration tests for that), testing undocumented behavior that must not become a supported contract, or unit-testing rendering or client UI behavior (use UI/component tests). Do not use consumer-driven contract testing for one-sided contracts where only one team controls both provider and consumer.

# Stage Fit

At each stage, use during planning, coding, debugging, bug-fix repair, code-review, refactoring, testing, release readiness, and handoff when a consumer-visible contract must remain executable and version-aware. Re-enter after schema, OpenAPI/AsyncAPI/proto, SDK, generated client, pact broker, schema registry, vendor fixture, deployment-version evidence, project memory, repository graph, or execution trajectory changes. Skip when the change is provider-internal behavior with no supported consumer-visible contract surface.

# Non-Negotiable Rules

- **Consumer expectations are explicit and executable.** Consumer pact or expectation files are committed to source control and are verifiable against the actual provider. "We assume it still works" is not a contract test.
- **Breaking change detection runs in CI before merge.** Contract compatibility must be checked on every pull request that modifies a contract surface — not after deployment.
- **Error, null, and optional-field behavior is contracted.** Contracts cover: error responses (status code, body shape, error code), nullable/optional fields that consumers depend on, pagination structure, unknown field handling (additionalProperties / unknown gRPC fields), enum expansion rules, and ordering guarantees. Omitting these produces silent client failures.
- **Backward incompatible changes require explicit versioning.** A change is backward-breaking if it removes a field, changes a field type, changes a required/optional status, removes a status code, renames a discriminator, changes a sort order, or removes an enum value. Breaking changes require a new version (`/v2/`, Protobuf field deprecation + reserved, AsyncAPI `x-version`) and a migration plan with sunset timeline.
- **External vendor contracts use verified, not assumed, behavior.** Mock a third-party API only from its published spec (OpenAPI, AsyncAPI), recorded live responses in a sandbox, or pinned captured examples — not from memory or inference. Vendor APIs have bugs that differ from their docs; record real behavior.
- **Schema sources are authoritative.** OpenAPI spec, Protobuf `.proto`, AsyncAPI spec, or JSON Schema are the ground truth; hand-written test assertions that duplicate or paraphrase these are maintenance liabilities. Validate against the machine-readable schema.
- **Schema registry compatibility mode is configured explicitly.** Confluent Schema Registry, AWS Glue Schema Registry, and Apicurio each support: BACKWARD, FORWARD, FULL, NONE compatibility. The correct mode must be set per subject/schema at registration time; default (BACKWARD) is not always correct.
- **Pact broker or equivalent maintains contract version history.** Consumer-driven contracts need a shared broker (Pact Broker, PactFlow) or equivalent to coordinate provider verification across independent release cycles — otherwise contracts are verified only locally and broken when either side changes independently.

# Industry Benchmarks

Anchor against consumer-driven contract testing, OpenAPI/AsyncAPI/protobuf schema compatibility, schema registry compatibility modes, generated-client checks, Pact Broker or equivalent version history, and breaking-change diff tools. Use [references/checklist.md](references/checklist.md) for quick planning and load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when selecting tooling, classifying breaking changes, or designing a broker/schema-registry workflow.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| API schema compatibility | OpenAPI, GraphQL, SDK, DTO, or error response changes. | Classify additive, breaking, deprecated, or versioned changes. | Schema diff, affected consumers, generated-client or provider verification command. | `api-contract-design`, `version-compatibility` | Provider unit tests as compatibility proof. |
| Event/message contract | AsyncAPI, Kafka/SQS/SNS, schema registry, protobuf, Avro, webhook payload. | Prove producer and consumer serialization compatibility. | Subject/schema, compatibility mode, fixture replay, old/new consumer version matrix. | `message-queue-design`, `integration-testing` | Registry default compatibility assumptions. |
| Consumer-driven contract | Independent provider and consumer release cycles. | Verify active consumer expectations against provider before deploy. | Pact/expectation source, broker selector, provider verification, can-i-deploy result. | `quality-test-gate`, `delivery-release-gate` | Provider-owned pact files only. |
| Vendor contract fixture | Third-party API, webhook, sandbox, or SDK dependency. | Prevent mocks from drifting from real or published vendor behavior. | Published spec or recorded sandbox response, fixture freshness, redaction, replay command. | `integration-change-builder`, `security-privacy-gate` | Memory-built vendor mocks. |
| Compatibility repair | Prior consumer break, breaking-change review finding, or stale contract evidence. | Reproduce the broken expectation and lock it into CI. | Defect/consumer reference, red/green contract check, migration/sunset plan, residual risk. | `regression-testing`, `execution-trajectory-analysis` | Compatibility claim without consumer evidence. |

# Selection Rules

Use this selection when **consumer-visible compatibility** is the primary concern. Adjacent routing:

- Prefer `api-contract-design` when designing the contract shape itself (before implementation).
- Prefer `dto-schema-design` when the question is the serialized transfer object structure.
- Prefer `integration-testing` for testing provider-internal behavior (not the external contract).
- Prefer `version-compatibility` for release rollout strategy across mixed-version deployments.
- Prefer `input-validation` when validating payload conformance at runtime rather than design-time.

# Risk Escalation Rules

Escalate when: a change removes or renames any field consumed by mobile apps (cannot force-upgrade); a breaking change affects a public/partner API with SLA; a Kafka topic schema changes in a way that invalidates in-flight messages; a webhook contract changes for third-party integrations that cannot be notified; a schema registry compatibility mode change is proposed; a consumer depends on undocumented behavior that the provider considers "internal"; an external vendor API is discovered to behave differently than its documented spec.

# Proactive Professional Triggers

- **Signal:** A PR changes OpenAPI, AsyncAPI, proto, JSON Schema, GraphQL SDL, SDK exports, DTOs, or error response fields without naming consumers. **Hidden risk:** local tests pass while downstream clients break. **Required professional action:** build a consumer inventory and run or require schema/client compatibility checks. **Route to:** `consumer-impact-analysis`, `data-api-contract-changer`. **Evidence required:** changed surface, consumer list, schema diff, generated-client or contract command.
- **Signal:** Provider tests pass but no pact, broker, generated-client, or schema-registry verification ran. **Hidden risk:** provider business behavior is verified while the supported contract is untested. **Required professional action:** map each contract surface to consumer and provider verification. **Route to:** `quality-test-gate`, `validation-broker`. **Evidence required:** provider command, consumer command, broker/can-i-deploy status or not-run reason.
- **Signal:** An event, webhook, or topic schema uses default compatibility mode or omits null/optional/unknown-field policy. **Hidden risk:** mixed-version producers and consumers fail during rollout. **Required professional action:** declare compatibility mode and test old/new version behavior. **Route to:** `message-queue-design`, `version-compatibility`. **Evidence required:** schema subject, mode, old/new fixtures, registry check output.
- **Signal:** A vendor or partner mock is hand-written from memory or stale docs. **Hidden risk:** integration tests validate impossible behavior and miss real sandbox quirks. **Required professional action:** rebuild fixtures from a published spec or recorded sandbox response and mark freshness. **Route to:** `integration-testing`, `security-privacy-gate`. **Evidence required:** fixture source, captured_at/version, redaction boundary, replay result.
- **Signal:** Project memory, repository graph, or prior validation says a contract passed before later schema, generated client, or fixture changes. **Hidden risk:** stale compatibility evidence is treated as current. **Required professional action:** reconcile graph/memory/trajectory freshness and rerun mapped validators after final edits. **Route to:** `project-memory-governance`, `repository-graph-analysis`, `execution-trajectory-analysis`. **Evidence required:** accepted/rejected prior claims, final changed paths, validation freshness, residual risk.

# Critical Details

Contract testing succeeds only when both **provider** and **consumer** perspectives are actively maintained. Common precision failures:

- **"additionalProperties" discipline.** If `additionalProperties: false` is set on a response schema, consumers will reject any future field additions. Set `additionalProperties: true` (or omit it, which defaults to true in JSON Schema) in consumer response expectations to allow forward-compatible evolution. Reserve `additionalProperties: false` for request validation where strict input rejection is intentional.
- **Pagination shape is a contract.** `data`, `items`, `results`, `meta.total`, `links.next` — any field a consumer unpacks is contracted. Tests that only verify status codes 200 miss pagination regressions.
- **Null vs absent field.** JSON `"field": null` and missing `"field"` key are different; typed consumers (TypeScript strict mode, Go struct unmarshalling, Jackson deserialization) behave differently. Test both.
- **Enum expansion is a breaking change for closed consumers.** A consumer that switch-cases on an enum and throws on unknown values will break if the provider adds a new value. Use extensible enum patterns (allow unknown values) or explicitly version the enum.
- **Error contract is a first-class contract.** RFC 7807 / RFC 9457 Problem Details define `type`, `title`, `status`, `detail`, `instance`. If consumers parse error bodies (retry logic, error display, machine-readable codes), these are contracted. Golden-path-only tests miss error contract regressions.
- **Pact interactions represent a subset, not a full spec.** A pact file describes the minimum expectations of that consumer. A new consumer with different expectations needs its own pact. Provider verification against all active consumer pacts is the safety net.
- **Schema registry FULL compatibility.** BACKWARD means new schema can read old data; FORWARD means old schema can read new data; FULL means both. For Kafka topics with mixed-version consumers, FULL is the safe default.
- **Sunset timeline.** RFC 8594 defines the `Sunset` HTTP header for communicating API deprecation timelines. Use it alongside `Deprecation` header in responses. Contract tests should verify the deprecated operation still works until sunset date.
- **Contract test ≠ integration test.** Contract tests are fast, isolated (mock provider/consumer), and run per-change. Integration tests use real services. Running integration tests instead of contract tests at PR time is expensive and slower; both have their place.

### Anti-examples

| Anti-pattern | Consequence |
| --- | --- |
| Contract test checks only `status: 200` and no body fields | Any field rename, removal, or type change passes undetected |
| Consumer mocks third-party vendor from memory | Mock drifts from real vendor behavior; integration fails in production |
| Schema registry set to NONE compatibility | Any schema change accepted; producers/consumers deserialization errors at runtime |
| Breaking change hidden as "backward compatible patch" | Existing clients break on next deployment; hotfix required |
| `additionalProperties: false` on response schema in consumer pact | Any future field addition by provider breaks consumer CI |
| Provider verified only locally (no pact broker) | Independent consumer release deploys against unverified provider |
| Error responses not covered by contract tests | Error-handling code in consumers regresses silently |
| Enum values tested as exhaustive list | Provider adds enum value; consumer switch-case throws on unknown value |
| Pact file committed to provider repo | Defeats consumer-driven model; provider self-certifies compliance |

# Failure Modes

- **Provider-only CI:** CI only runs provider unit tests; no consumer expectations are verified; breaking change ships.
- **Broker gap:** Consumer pact broker not configured; contracts verified locally only; independent releases diverge.
- **Error-shape gap:** Golden snapshot for response body does not include error cases; 4xx contract regressions are invisible.
- **Long-lived client break:** Mobile client cannot be force-upgraded; breaking API change causes crash on old app version.
- **Event replay break:** Kafka topic schema evolves; in-flight messages fail deserialization on consumer restart.
- **Enum drift:** Enum value removed; consumer code that pattern-matched it returns null silently.
- **Unknown-field rigidity:** `additionalProperties: false` on response pact; provider adds new optional field; consumer CI breaks on a non-breaking change.
- **Vendor fixture drift:** Vendor API mock built from stale documentation; production integration behaves differently than tests.
- **Registry mode mismatch:** Schema registry mode not set; default (BACKWARD) assumed for FULL requirement; forward-incompatible change breaks old consumers.
- **Version matrix gap:** Contract version matrix not tracked; provider verified against old consumer version; new consumer expectation never run.
- **Deprecation signal gap:** Sunset header not added; deprecated endpoint removed; partner integration fails without warning.
- **Pagination contract gap:** Pagination `meta.total` removed; consumer pagination UI breaks; not covered by contract test.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 selection, routing, output, and gate rules. Load [references/checklist.md](references/checklist.md) when drafting a concrete contract test plan, closure map, or provider/consumer evidence review. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when selecting tooling, classifying breaking changes, comparing REST/gRPC/event/webhook/GraphQL contract styles, or designing Pact Broker/schema-registry workflows. Load [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on repository graph, project memory, execution trajectory, validation freshness, fixture freshness, broker/registry status, or tool permission boundaries. Use [examples/example-output.md](examples/example-output.md) only when the expected answer shape is unclear or a compact source-authored example is needed. Do not load references for provider-internal tests with no consumer-visible contract surface.

# Output Contract

Return a contract test plan with:

- `mode_selected` (API schema compatibility, event/message contract, consumer-driven contract, vendor contract fixture, or compatibility repair)
- `contract_surface` (endpoints, operations, event types, message schemas, webhook shapes)
- `source_evidence` (schema paths, generated clients, pacts, registry subjects, vendor specs, graph slice, direct source files, and freshness)
- `providers` (service name, version, deployment cycle)
- `consumers` (service/app name, version, deployment cycle, pact or expectation source)
- `schema_sources` (authoritative spec files: OpenAPI path, proto file, AsyncAPI file, JSON Schema)
- `compatibility_mode` (per schema: BACKWARD/FORWARD/FULL/NONE; per API: additive-only/versioned)
- `breaking_change_assessment` (per changed field/operation: breaking Y/N; strategy: version/deprecate/safe)
- `positive_cases` (happy-path interactions with schema-validated response)
- `negative_cases` (error responses: 400/404/409/422/503 with body shape)
- `null_and_optional_cases` (fields that are sometimes absent or null)
- `enum_expansion_cases` (enum fields and their extensibility policy)
- `pagination_cases` (pagination shape, cursors, totals, links)
- `version_behavior` (versioning strategy; sunset timeline for deprecated operations)
- `ci_gate` (tool + command that runs in CI; blocking condition)
- `pact_broker_config` (broker URL; can-i-deploy check; consumer version selectors)
- `migration_evidence` (for breaking changes: dual version period, consumer migration deadline, sunset date)
- `graph_memory_execution_coupling` (repository graph, project memory, prior summary, and trajectory claims accepted, rejected, stale, partial, or not verified)
- `validation_freshness` (provider/consumer commands, schema diff, generated-client check, registry check, broker check, exit code or not-run status, and final-edit freshness)
- `tool_permission_boundary` (shell/vendor-sandbox/registry/broker action class, sandbox/approval status, and sensitive fixture redaction rule)
- `what_evidence_proves` and `what_evidence_does_not_prove`
- `residual_risk` (unknown consumers, stale fixtures, unsupported versions, unrun broker checks, owner, and next gate)

# Evidence Contract

A contract test is accepted only when the output includes:

- **Provider and consumer**: service/library/API producer and each affected consumer.
- **Contract surface**: request schema, response schema, error code, header, event payload, pagination, sort/filter, or SDK method.
- **Compatibility claim**: backward-compatible, additive, breaking, deprecated, or versioned.
- **Consumer verification**: generated client, pact/contract test, schema diff, fixture replay, or consumer test command.
- **Provider verification**: provider-side contract validation command and output.
- **Semantic limits**: what the contract verifies versus business behavior outside the schema.
- **What evidence proves**: the named consumer/provider contract remains compatible.
- **What evidence does not prove**: unknown consumers, production traffic compatibility, runtime data semantics, or behavior outside the contract.
- **Residual risk**: unverified consumers, owner, and next gate.
- **Boundaries inspected**: schema, provider, consumer, generated client, broker/registry, vendor fixture, graph, memory, and trajectory evidence included or explicitly skipped.

# Quality Gate

The contract test plan passes only when:

1. Consumer expectations are machine-executable against the actual provider, not assertions about mock behavior.
2. Every breaking change in the diff is explicitly classified and has a versioning + migration plan.
3. Error responses (4xx, 5xx) are covered with body shape assertions.
4. Null, absent, and optional field behavior is covered.
5. Enum fields have an extensibility policy (open/closed; unknown value handling).
6. Pagination and collection ordering are covered where consumers depend on them.
7. Schema registry compatibility mode is explicitly set per subject with justification.
8. External vendor behavior is mocked from a machine-readable spec or recorded real response, not from memory.
9. Contract tests run in CI on every PR that touches a contract surface.
10. `can-i-deploy` (or equivalent) is checked before production deployment.
11. Validation evidence names provider, consumer, schema diff, registry, broker, generated-client, or fixture replay command plus exit code or not-run status.
12. Graph, memory, prior-summary, and execution-trajectory claims are reconciled before they influence compatibility or release readiness.
13. Vendor fixtures and recorded responses have sensitive data redacted and freshness markers.
14. Residual risk and next gate are explicit for unknown consumers, unsupported versions, or skipped compatibility checks.

# Benchmark Coverage

This capability covers consumer-driven contract testing, OpenAPI/AsyncAPI/protobuf/GraphQL compatibility diffing, schema registry mode selection, generated-client verification, broker-backed provider verification, vendor fixture replay, error/null/pagination/enum contract coverage, versioned migration, and validation freshness.

# Routing Coverage

Route here when the primary risk is consumer-visible compatibility across API, event, webhook, SDK, schema, generated client, or vendor contract boundaries. Route away when the primary need is contract design (`api-contract-design`, `dto-schema-design`), provider-internal behavior (`integration-testing`), release rollout (`version-compatibility`, `delivery-release-gate`), or prior defect recurrence (`regression-testing`).

# Used By

- quality-test-gate
- data-api-contract-changer
- integration-change-builder

# Handoff

Hand off to `api-contract-design` or `dto-schema-design` for contract shape design; `version-compatibility` for mixed-version deployment strategy; `integration-testing` for provider-internal behavior; `regression-testing` for prior compatibility defects; `delivery-release-gate` for deployment readiness with contract verification status.

# Completion Criteria

The capability is complete when **an independent provider change that breaks any supported consumer expectation is caught in CI before it can be deployed** — and every contracted field, error shape, enum, pagination, and null behavior is covered by an executable assertion with a documented compatibility evolution strategy.
