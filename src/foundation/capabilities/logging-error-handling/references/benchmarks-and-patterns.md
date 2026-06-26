# Logging Error Handling Benchmarks And Patterns

Use this reference when the main skill selects deep benchmark mapping, schema design, trace propagation, redaction, audit separation, or graph-memory-execution consistency. Keep closure evidence tied to current source and validation output; do not treat this reference as proof that an implementation is safe.

## Benchmark Anchors

- OWASP Logging Cheat Sheet: define events worth logging, avoid sensitive data, preserve integrity, encode log output, and use correlation for investigation.
- NIST SP 800-92: collect, protect, review, retain, and dispose logs as managed security records rather than incidental debug output.
- W3C Trace Context: propagate `traceparent` and related context through HTTP calls and asynchronous boundaries.
- OpenTelemetry Logs Data Model: attach trace and span identifiers, severity, resource attributes, and structured attributes so logs can join metrics and traces.
- RFC 7807: return stable problem details to clients without leaking internal exception text or stack frames.
- PCI DSS: never log full PAN or sensitive authentication data; retain audit evidence for privileged and cardholder-data access.
- SOC 2 CC7.2: security events must be detectable, reviewable, and protected from inappropriate alteration.
- Elastic Common Schema and common APM tools: prefer consistent names for `error.*`, `http.*`, `user.*`, service, environment, deployment, and trace fields.

## Error Taxonomy And Level Matrix

| Error class | Typical status | Log level | Stack trace | Audit event | Client output |
| --- | --- | --- | --- | --- | --- |
| User validation | 400 | INFO or DEBUG | No | No | Field-level remediation |
| Not found | 404 | INFO or DEBUG | No | No | Stable code and message |
| Conflict or duplicate | 409 | INFO | No | Sometimes | Conflict reason safe for caller |
| Rate limit | 429 | INFO | No | No | Retry-After or retry guidance |
| Authentication failure | 401 | WARN plus security audit | No | Yes | Generic unauthorized |
| Authorization denial | 403 | WARN plus security audit | No | Yes | Generic forbidden |
| Unexpected system failure | 500 | ERROR | Internal only | No | Opaque error with correlation id |
| System timeout or overload | 503 | WARN or ERROR | Usually no | No | Retry guidance when safe |
| Third-party timeout or 5xx | 502 or 503 | WARN or ERROR | No | No | Opaque dependency failure |
| Suspicious or abusive input | 400 or 403 | WARN plus security audit | No | Yes | Generic rejection |

## Structured Log Schema

Minimum production event fields:

```json
{
  "timestamp": "2026-01-15T14:23:05.123Z",
  "level": "ERROR",
  "service": "orders-api",
  "version": "3.2.1",
  "environment": "production",
  "correlationId": "req-abc123",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "spanId": "00f067aa0ba902b7",
  "message": "Failed to persist order",
  "error": {
    "type": "DuplicateOrderException",
    "message": "duplicate idempotency key",
    "stacktrace": "internal system errors only"
  },
  "userId": "u:sha256:a3f8...",
  "requestId": "req-abc123",
  "http": {
    "method": "POST",
    "route": "/orders",
    "status_code": 409
  }
}
```

Never include passwords, API keys, bearer tokens, session cookies, private keys, full payment data, full raw payloads, unrestricted query strings, or unscreened provider responses. Hash or pseudonymize identifiers when direct user identifiers are unnecessary for diagnosis.

## Trace Context Propagation

- Parse inbound `traceparent` when present; otherwise generate a new trace id and initial span id at the boundary.
- Bind trace and correlation context before application code logs.
- Pass trace context on all outbound HTTP or RPC calls.
- Inject correlation context into queue message headers, job metadata, or scheduler metadata rather than domain payloads.
- Extract and bind context in consumers before the first log statement.
- Do not generate a new trace id mid-request unless starting a genuinely independent trace with an explicit link.

## Audit And Diagnostic Split

Diagnostic logs explain how a request failed. Audit logs prove that sensitive actions occurred and who initiated them. Authentication success/failure, authorization denial, permission change, administrative override, sensitive data access, and configuration change belong in an append-only audit sink with actor, action, resource, outcome, timestamp, source IP or device context, and correlation id. Application log rotation must not delete required audit evidence.

## Graph, Memory, And Execution Coupling

- Use repository graph context to find logger wrappers, middleware, exception mappers, job consumers, outbound clients, and audit sinks.
- Use memory or prior reports only as search hints; stale validation does not close current risk.
- Compare same-pattern implementations before changing a single handler or logger call.
- Verify execution with captured log output, API response fixtures, audit event assertions, and correlation propagation tests.
- State whether validation covers the sink, only the local logger call, or only an in-memory test fixture.

## Validation Checklist

- Every log statement in the touched path includes correlation or trace context.
- Forbidden fields are absent from captured log output.
- Expected user errors do not emit `ERROR`.
- Unexpected failures include internal diagnostics without leaking to the client.
- Client responses follow RFC 7807 or the local stable error envelope.
- Audit events use a separate append-only sink when security-sensitive actions are involved.
- Async and queue paths bind context before work begins.
- Third-party errors capture dependency, timeout, status, retryability, and circuit state without provider secrets.
- Tool output used as evidence avoids raw secrets, full payloads, environment dumps, and unbounded logs.
