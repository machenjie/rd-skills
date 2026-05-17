# Example Output

```markdown
## Logging And Error Handling Plan

Error taxonomy:
- User error: invalid request, missing required field, unsupported transition.
- System error: storage timeout, invariant conflict caused by concurrent update.
- Third-party error: payment provider unavailable or rejected request.
- Security error: unauthenticated, unauthorized, suspicious token reuse.

Client mapping:
- User errors return stable code and remediation message.
- System errors return safe retry guidance with correlation id.
- Third-party errors include retryability but not provider internals.
- Security errors avoid revealing protected resource details.

Logging:
- Include correlationId, subjectId, tenantId, operation, resourceId, outcome, and errorCode.
- Redact tokens, credentials, raw payloads, and sensitive field values.

Audit:
- Record permission denials and administrative overrides.
```
