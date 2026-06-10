# Security Checks

## Threat Surface

Contract compatibility can accidentally expose new fields to unauthorized consumers or keep deprecated fields after privacy requirements change.

## Required Checks

- Old and new fields preserve authorization and privacy filtering.
- Telemetry for consumer usage avoids PII and secret values.
- Migration docs do not expose internal consumer identities beyond approved scope.

## Rejection Cases

- Reject compatibility aliases that bypass field-level permission checks.
- Fail when telemetry logs raw user identifiers or secrets.
- Reject rollback that reintroduces a privacy-forbidden field.
