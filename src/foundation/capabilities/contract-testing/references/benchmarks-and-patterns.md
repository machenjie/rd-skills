# Contract Testing Benchmarks And Patterns

Load this reference when selecting contract testing tooling, classifying breaking changes, comparing REST/gRPC/event/webhook/GraphQL contract styles, or designing a Pact Broker, schema registry, generated-client, or vendor-fixture workflow. Keep routine routing in `SKILL.md`.

## Benchmark Anchors

- **Pact / Pact Specification v3/v4**: consumer-driven contract testing for REST, gRPC, and messages with provider verification.
- **Spring Cloud Contract**: JVM ecosystem consumer/provider contract tests and stub generation.
- **OpenAPI Specification 3.x**: machine-readable REST contract validated with `spectral`, `openapi-diff`, or `oasdiff`.
- **AsyncAPI 2.x/3.x**: event and async-message contract specification.
- **Protocol Buffers / gRPC**: binary compatibility with `buf breaking`.
- **Confluent Schema Registry, AWS Glue Schema Registry, Apicurio**: Avro, Protobuf, and JSON Schema compatibility modes.
- **JSON Schema Draft 2020-12**: structural validation and explicit unknown-field policy.
- **Pact Broker / PactFlow**: versioned contract registry and provider verification coordination.
- **WireMock / MockServer**: stubs generated from contracts or recorded fixtures.
- **Spectral**: OpenAPI/AsyncAPI linting with custom rulesets.
- **OWASP API Security Top 10 2023**: authentication and object-property risks that can appear in API contracts.
- **RFC 8594 Sunset header**: deprecation and sunset signaling for HTTP APIs.

## Contract Type Selection Matrix

| Contract type | Tooling | Machine-readable source | Breaking change detection | Pick when |
| --- | --- | --- | --- | --- |
| REST / HTTP | Pact v4, OAS3 diff, WireMock stubs | OpenAPI 3.x YAML/JSON | `oasdiff breaking`; Pact provider test | HTTP services with independent release cycles |
| gRPC / Protobuf | `buf breaking`, Pact gRPC plugin | `.proto` files | `buf breaking --against origin/main` | gRPC services; strict binary compatibility needed |
| Async / Events | Pact v3 message pacts, AsyncAPI diff | AsyncAPI 2.x/3.x YAML | AsyncAPI diff; Pact message provider test | Kafka, SNS, SQS, webhooks, event-driven |
| JSON Schema | AJV, `ajv-cli`, json-schema-diff | JSON Schema 2020-12 | json-schema-diff; unknown-field policy | DTOs, config, data pipeline payloads |
| Avro Kafka | Confluent Schema Registry CLI | `.avsc` | Registry compatibility check | Confluent Kafka with schema registry |
| Protobuf Kafka | `buf`, Confluent Schema Registry | `.proto` | `buf breaking`; registry FULL mode | High-throughput serialized events needing binary compatibility |
| GraphQL | `graphql-inspector diff` | SDL schema | `graphql-inspector diff` breaking | GraphQL APIs with external consumer apps |
| Webhook | Pact v4 async; WireMock stubbing | OpenAPI Webhook or AsyncAPI | Manual review plus pact or event fixture | Third-party webhook integrations |

## Breaking Change Classification

| Change type | Breaking? | Safe evolution strategy |
| --- | --- | --- |
| Remove required field from response | Yes | Deprecate, keep for at least one version, then sunset |
| Remove required request field | Yes if consumers send it | Version if ambiguous; mark optional first |
| Change field type | Yes | Add new field name and deprecate old; never silently change type |
| Remove HTTP status code | Yes | Keep old code while adding new code during transition |
| Remove enum value | Yes | Do not remove; deprecate and keep tolerant readers |
| Add optional response field | No | Safe when consumers ignore unknown fields |
| Add required request field | Yes | Add as optional first; enforce in next version |
| Add enum value in closed enum | Often yes | Use extensible enum pattern or versioned enum |
| Change collection sort order | Yes if consumers rely on it | Document sort and provide explicit `sort` parameter |
| Remove endpoint or operation | Yes | Sunset header, deprecation notice, and versioned replacement |
| Rename field | Yes | Add new field, deprecate old, and support both during migration |
| Widen nullability | Yes for strict consumers | Deprecate and version; test null handling |

## Consumer-Driven Workflow

```text
Consumer writes interaction expectations
  -> publishes pact or expectation to broker with consumer version
Provider CI runs provider verification against selected consumer versions
  -> PR is blocked if any active consumer expectation fails
Deployment gate runs can-i-deploy or equivalent
  -> deployment is blocked if provider version is not verified for target environment
```

## Fixture And Registry Patterns

- Recorded vendor fixtures must include source, captured_at, vendor version, redaction status, and replay command.
- Schema registry checks must name subject, compatibility mode, old schema, new schema, producer version, and consumer version.
- Generated-client checks should compile or test the generated client against the changed schema, not only diff the schema text.
- Consumer pacts should live with consumers; provider-owned self-certification is not consumer-driven evidence.
