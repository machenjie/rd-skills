# Security Checks

## Threat Surface

Preference defaults can affect authorization-adjacent UI state and user-visible settings.

## Required Checks

- Reject fixes that treat denied, missing, false, and zero as the same state.
- Fail if the solution logs raw preference payloads while debugging the fallback.

## Rejection Cases

- Reject truthiness defaulting that overwrites valid falsey values.
- Reject broad shared helper changes that alter other preference domains.

