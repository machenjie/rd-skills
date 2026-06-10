# Security Checks

## Threat Surface

Deletion can remove fallback protections, audit logging, permission checks, or privacy shims if references and behavior are not understood.

## Required Checks

- Caller search includes security-sensitive fallback and compatibility behavior.
- Telemetry evidence does not log PII or secrets.
- Rollback path does not re-enable deprecated insecure behavior without approval.

## Rejection Cases

- Reject deletion that removes authorization, audit, or privacy behavior without replacement.
- Fail when telemetry evidence exposes user identifiers or tokens.
- Reject rollback that silently re-enables insecure deprecated API behavior.
