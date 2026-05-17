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

Anchor against: **Pact** (consumer-driven contract testing framework; pact.io; supported for REST, gRPC, messages) — the industry reference for CDC testing. **Pact Specification v3/v4** — supports interactions, message pacts, synchronous request/response. **Spring Cloud Contract** — JVM-ecosystem CDC testing with stub generation. **OpenAPI Specification (OAS) 3.x** (OpenAPI Initiative) — machine-readable REST contract; validate with `spectral`, `openapi-diff`, `oasdiff`. **AsyncAPI Specification 2.x/3.x** — event and async message contract. **Protocol Buffers** (Protobuf/gRPC) — `buf breaking` for breaking-change detection on proto files. **Confluent Schema Registry** + Avro/Protobuf/JSON Schema with compatibility modes (BACKWARD / FORWARD / FULL). **JSON Schema Draft 2020-12** — structural validation; `additionalProperties: false` as explicit unknown-field policy. **`oasdiff` / `openapi-diff`** — CLI tools for OpenAPI backward compatibility analysis. **Pact Broker / PactFlow** — contract version registry and provider verification coordination. **WireMock / MockServer** — stub generation from contracts for consumer integration tests. **Spectral** (Stoplight) — OpenAPI/AsyncAPI linting with custom rulesets. **OWASP API Top 10 (2023)** — API2:2023 Broken Authentication, API3:2023 Broken Object Property Level Authorization relate to contract-level security expectations. **REST API versioning best practices** (SemVer, URL path, Accept header, sunset header RFC 8594).

### Contract Type Selection Matrix

| Contract type | Tooling | Machine-readable source | Breaking change detection | Pick when |
| --- | --- | --- | --- | --- |
| **REST / HTTP** | Pact v4, OAS3 diff (`oasdiff`), WireMock stubs | OpenAPI 3.x YAML/JSON | `oasdiff breaking`; Pact provider test | HTTP services with independent release cycles |
| **gRPC / Protobuf** | `buf breaking`, Pact gRPC plugin | `.proto` files | `buf breaking --against origin/main` | gRPC services; strict binary compatibility needed |
| **Async / Events** | Pact v3 message pacts, AsyncAPI diff | AsyncAPI 2.x/3.x YAML | AsyncAPI diff; Pact message provider test | Kafka, SNS, SQS, webhooks, event-driven |
| **JSON Schema** | AJV, `ajv-cli`, json-schema-diff | JSON Schema 2020-12 | json-schema-diff; `additionalProperties` mode | DTOs, config, data pipeline payloads |
| **Avro (Kafka)** | Confluent Schema Registry CLI | `.avsc` | Registry compatibility check (BACKWARD mode default) | Confluent Kafka with schema registry |
| **Protobuf (Kafka)** | `buf`, Confluent Schema Registry | `.proto` | `buf breaking`; registry FULL mode | High-throughput serialized events needing binary compat |
| **GraphQL** | `graphql-inspector diff` | SDL schema | `graphql-inspector diff` breaking | GraphQL APIs with external consumer apps |
| **Webhook** | Pact v4 async; WireMock stubbing | OpenAPI Webhook (OAS 3.1) / AsyncAPI | Manual review + pact; event shape snapshot | Third-party webhook integrations |

### Breaking vs Non-Breaking Change Classification

| Change type | Breaking? | Safe evolution strategy |
| --- | --- | --- |
| Remove required field from response | **Yes** | Deprecate (mark `deprecated: true`), keep for ≥ 1 version, sunset |
| Remove required request field | Yes if consumers send it | Version if ambiguous; mark optional first |
| Change field type (`string` → `integer`) | **Yes** | New field name + deprecation; never silent type change |
| Remove HTTP status code | **Yes** | Keep code, add new code simultaneously in v transition |
| Remove enum value | **Yes** | Never; add `x-extensible-enum` / open enum pattern |
| Add new **optional** response field | No | Safe; consumers should ignore unknown fields |
| Add new **required** request field | **Yes** | Add as optional + validate server-side; force in v+1 |
| Add new enum value (closed enum) | **Yes** for typed consumers | Use extensible enum pattern; warn consumers |
| Change sort order of collection | **Yes** (if order was relied on) | Explicitly document sort; provide `sort` parameter |
| Remove endpoint / operation | **Yes** | Sunset header (RFC 8594) + deprecation + versioned alt |
| Rename field | **Yes** | Add new field + deprecate old; dual-write period |
| Widen nullability (non-null → nullable) | Yes for strict consumers | Deprecate + new version; test null handling |

### Consumer-Driven Contract Testing Workflow

```
Consumer writes interaction expectations
    ↓ pact publish → Pact Broker (version tagged to consumer branch)
Provider CI runs:
    pact verify --provider-url http://localhost:8080
    --pact-broker-base-url https://pact-broker.internal
    --consumer-version-selectors '[{"mainBranch": true}]'
    ↓ If any interaction fails → PR blocked
Can I Deploy check:
    pact-broker can-i-deploy --pacticipant MyProvider --version <sha> --to-environment prod
    ↓ Checks all consumers are verified against this version
    ↓ If any consumer unverified → deployment blocked
```

# Selection Rules

Select this capability when **consumer-visible compatibility** is the primary concern. Adjacent routing:

- Prefer `api-contract-design` when designing the contract shape itself (before implementation).
- Prefer `dto-schema-design` when the question is the serialized transfer object structure.
- Prefer `integration-testing` for testing provider-internal behavior (not the external contract).
- Prefer `version-compatibility` for release rollout strategy across mixed-version deployments.
- Prefer `schema-validation` when validating payload conformance at runtime rather than design-time.

# Risk Escalation Rules

Escalate when: a change removes or renames any field consumed by mobile apps (cannot force-upgrade); a breaking change affects a public/partner API with SLA; a Kafka topic schema changes in a way that invalidates in-flight messages; a webhook contract changes for third-party integrations that cannot be notified; a schema registry compatibility mode change is proposed; a consumer depends on undocumented behavior that the provider considers "internal"; an external vendor API is discovered to behave differently than its documented spec.

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

- CI only runs provider unit tests; no consumer expectations are verified; breaking change ships.
- Consumer pact broker not configured; contracts verified locally only; independent releases diverge.
- Golden snapshot for response body does not include error cases; 4xx contract regressions are invisible.
- Mobile client cannot be force-upgraded; breaking API change causes crash on old app version.
- Kafka topic schema evolves; in-flight messages fail deserialization on consumer restart.
- Enum value removed; consumer code that pattern-matched it returns null silently.
- `additionalProperties: false` on response pact; provider adds new optional field; consumer CI breaks on a non-breaking change.
- Vendor API mock built from stale documentation; production integration behaves differently than tests.
- Schema registry mode not set; default (BACKWARD) assumed for FULL requirement; forward-incompatible change breaks old consumers.
- Contract version matrix not tracked; provider verified against old consumer version; new consumer expectation never run.
- Sunset header not added; deprecated endpoint removed; partner integration fails without warning.
- Pagination `meta.total` removed; consumer pagination UI breaks; not covered by contract test.

# Output Contract

Return a contract test plan with:

- `contract_surface` (endpoints, operations, event types, message schemas, webhook shapes)
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

# Used By

- quality-test-gate
- data-api-contract-changer
- integration-change-builder

# Handoff

Hand off to `api-contract-design` or `dto-schema-design` for contract shape design; `version-compatibility` for mixed-version deployment strategy; `integration-testing` for provider-internal behavior; `regression-testing` for prior compatibility defects; `delivery-release-gate` for deployment readiness with contract verification status.

# Completion Criteria

The capability is complete when **an independent provider change that breaks any supported consumer expectation is caught in CI before it can be deployed** — and every contracted field, error shape, enum, pagination, and null behavior is covered by an executable assertion with a documented compatibility evolution strategy.
