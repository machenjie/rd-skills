# Security Checks

## Threat Surface

Hidden side effects can bypass authorization, publish sensitive events, mutate cache across tenants, or call external APIs before validation.

## Required Checks

- Authorization and validation occur before persistence, cache, event, or external I/O side effects.
- Event payloads and logs exclude secrets and PII.
- Cache keys include tenant or authorization boundary when required.

## Rejection Cases

- Reject side effects before permission checks.
- Fail when hidden mapper events leak sensitive fields.
- Reject cross-tenant cache mutation without source-of-truth and key-boundary proof.
