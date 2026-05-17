# Input Validation Checklist

- Identify every input source and trust boundary.
- Validate type, length, size, format, range, enum, and allowlist rules.
- Validate identifiers for existence, ownership, tenant scope, and permission.
- Validate semantic constraints, invariants, and legal state transitions.
- Normalize and decode input before security decisions.
- Reject unknown or dangerous fields unless compatibility requires tolerance.
- Define safe error responses, logging, and telemetry.
- Test direct API calls, malformed payloads, boundary values, hostile encodings, and unauthorized objects.
