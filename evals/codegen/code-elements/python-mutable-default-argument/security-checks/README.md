# Security Checks

## Threat Surface

Shared default state can leak request or tenant data across calls.

## Required Checks

- Reject shared mutable default state.
- Fail if tests use production data or log raw request payloads.

## Rejection Cases

- Reject mutable list or dict defaults.
- Reject fixes that merge tenant/request state between calls.

