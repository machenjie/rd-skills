# Example Output

```markdown
## Error Catalog Entry

mode_selected: security-sensitive error

boundaries_inspected:
- Controller: POST /refunds maps RefundPolicyViolation.
- Service: RefundPolicyViolation.ORDER_CLOSED is terminal.
- Adapter/provider: no provider body is returned to clients.
- Generated API docs: OpenAPI problem details example updated.

source_evidence:
- Current controller maps domain conflict to problem detail.
- Current error catalog has ORDER_REFUND_NOT_ALLOWED namespace.

graph_memory_trajectory_judgment:
- Accepted: existing catalog namespace `ORDER_*`.
- Rejected: prior note that all refund errors are retryable; current service marks this terminal.
- Not verified: mobile SDK behavior outside this repository.

catalog_entry:
- code: ORDER_REFUND_NOT_ALLOWED
- type: https://api.example.com/errors/ORDER_REFUND_NOT_ALLOWED
- category: business_conflict
- http_status: 409
- grpc_code: FAILED_PRECONDITION
- user_safe_message_key: refund.not_allowed.closed_order
- client_action: show message, refresh order state, do not auto-retry
- retryability: not-retryable
- idempotency_requirement: none for this terminal response
- authorization_posture: unchanged; unauthorized order lookup remains 404
- correlation_id_behavior: `X-Request-ID` header and `traceId` body field

diagnostic_separation:
- Response excludes `RefundPolicyViolation.ORDER_CLOSED`.
- Structured log includes internal policy code and order state with redacted tenant-safe ids.

validation_or_tests:
- Negative test: no internal policy name appears in response.
- Contract test: client branches on `code`, not message.
- Trace test: response body and log share the same request id.

behavior_preservation:
- Existing `ORDER_NOT_FOUND` and auth 404 posture unchanged.

evidence_limits:
- Does not prove mobile SDK release readiness; route generated-client compatibility to `version-compatibility` if SDK code changed.

handoff_boundaries:
- `failure-contract-design` owns service failure taxonomy.
- `logging-error-handling` owns structured diagnostic fields.
```
