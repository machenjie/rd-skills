# Error Code Design Checklist

- Select the mode and name the client-visible error surface.
- Inspect current catalog/spec/controller/adapter/provider/generated-client paths or state that none exist.
- Record graph, memory, and execution-trajectory claims accepted, rejected, or not verified.
- Define stable code or RFC 7807/9457 `type` URI, category, and transport status.
- Define user-safe message key, client action, and localization/support behavior.
- Separate response detail from operator diagnostics and trace/request id linkage.
- Redact stack traces, SQL/ORM/provider details, secrets, tokens, PII, tenant ids, and internal policy names.
- Define 401/403/404 posture and existence-leak decision for protected resources.
- Define field-level validation violations, safe rejected-value echo policy, and message ownership.
- Mark retryability, `Retry-After` or backoff, idempotency requirement, and duplicate-side-effect guard.
- Classify compatibility for changed codes, status, retryability, message semantics, generated clients, and SDK behavior.
- Keep metrics bounded by code/category/status; do not label by raw message, user id, resource id, or provider text.
- Map each changed error behavior to tests, validators, generated diffs, manual review, or residual risk.
- State reuse/placement rationale for catalog namespace and translation boundary.
- State evidence limits, residual risk owner, and next handoff.
