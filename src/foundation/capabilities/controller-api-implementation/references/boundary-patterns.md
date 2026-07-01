# Controller Boundary Patterns

Use this reference when a controller may be doing non-transport work, when generated handlers are being reviewed, or when route, service, DTO, error, authorization, and idempotency ownership are unclear. Keep the decision local to controller boundaries; hand deeper behavior to the owning capability.

## Responsibility Split

| Concern | Controller Owns | Handoff Owner | Reject When | Evidence |
| --- | --- | --- | --- | --- |
| Route binding | Method/path, operation id, content negotiation, accepted media type, handler wiring | `api-contract-design` for operation shape | Handler invents an undocumented operation or changes response envelope | Route file, OpenAPI/proto operation, handler registration |
| Request parsing | Path/query/header/body extraction, size and media limits, typed parse result | `dto-schema-design` for DTO semantics | Raw request object is passed downstream or request fields are read across layers | Parser/validator path, allowlisted fields |
| Validation handoff | Invoke schema/validator, map field errors, fail closed before service call | `input-validation` for validation rules | Validation is partial, client-only, duplicated in service, or allows unknown privileged fields | Schema ref, invalid cases, unknown-field behavior |
| Auth context | Extract trusted subject, tenant, scopes, roles, correlation id | `authentication-authorization` / `permission-boundary-modeling` for policy | Controller trusts body `user_id`, `tenant_id`, role, or scope | Middleware/auth path, derived context fields |
| Object authorization | Forward context and resource identifiers to service/policy | Service or permission capability | Controller decides ownership with stale or partial resource data | Service method, policy point, wrong-owner test owner |
| Service invocation | Call one use case with validated command/query and context | `service-business-logic` for orchestration | Controller calls repositories, transactions, providers, pricing, or domain mutators directly | Call graph, service boundary |
| Response mapping | Map service result to DTO, status, headers, content type | `api-contract-design` / `dto-schema-design` for wire shape | Persistence/domain/provider object is returned directly | DTO mapper, schema, response sample |
| Error mapping | Map typed failures to status, Problem Details, safe message, trace id | `error-code-design` for taxonomy | Raw exception, stack, SQL/provider detail, tenant id, secret, or internal policy leaks | Error table, negative tests, redaction rule |
| Idempotency and retries | Validate header syntax and forward key/fingerprint | `idempotency-retry-design` for dedupe store and replay | Controller dedupes business effects or ignores retryable writes | Header rule, service idempotency contract |
| Observability metadata | Correlation id, bounded route labels, rate-limit and retry headers | `reliability-observability-gate` for SLOs | Logs include payload secrets, user ids as labels, or unbounded messages | Log field list, redaction decision |
| Streaming/multipart | Enforce size, type, timeout, and backpressure boundaries | `file-storage-processing` / reliability gate | Controller buffers unbounded payloads or trusts filename/content type | Limit config, timeout, streaming test |

## Thin Controller Decision Record

```yaml
controller_boundary_decision:
  route_or_operation: ""
  contract_source: ""
  handler_file: ""
  middleware_auth_path: ""
  request_schema_or_validator: ""
  context_forwarded:
    subject: ""
    tenant: ""
    scopes_or_roles: ""
    correlation_id: ""
  service_boundary:
    service_method: ""
    command_or_query_dto: ""
    forbidden_controller_calls:
      - repository
      - transaction
      - domain mutation
      - provider call
      - object authorization decision
  response_boundary:
    success_statuses: []
    dto_mapper: ""
    required_headers: []
  error_boundary:
    typed_failures: []
    problem_details_type_source: ""
    redacted_fields: []
  handoffs:
    - capability: ""
      reason: ""
```

## Boundary Exceptions

- Middleware can own cross-cutting entry behavior such as auth extraction, request ids, rate-limit headers, and content negotiation, but the controller still records the boundary and evidence.
- Generated controllers are acceptable only when generated artifacts, schema source, mapper hooks, and error hooks are current and diffed after edits.
- A simple read-only controller may skip idempotency detail, but it still needs validation, auth context, response shape, and error mapping evidence.
- Public unauthenticated endpoints still need input validation, rate/size limits, safe errors, and a reason why authentication is not required.
