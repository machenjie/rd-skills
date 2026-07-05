# Security Checks

## Threat Surface

Failure contracts can expose provider internals, secrets, PII, permission details, or timing information through unsafe error mapping.

## Required Checks

- User-visible messages are safe and do not include raw database, SDK, token, or PII values.
- Logs preserve cause with redaction and bounded fields.
- Permission and auth failures do not reveal whether protected resources exist.

## Rejection Cases

- Reject raw DB or SDK error leakage to responses.
- Fail when internal diagnostics include secrets or customer PII.
- Reject fallback that hides an authorization or payment failure.
