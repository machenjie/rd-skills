# Security Checks

## Threat Surface

The fixture evaluates local, supplied records. It does not authorize external operations, install dependencies, or make production decisions.

## Required Checks

- Keep network and external-service calls absent.
- Preserve caller-owned inputs and the existing benchmark execution boundary.
- Distinguish malformed or conflicting evidence from a successful validation result.

## Rejection Cases

Reject implementations that conceal uncertainty, execute record text, or replace the deterministic evidence contract with external effects. Existing harness checks remain the execution owner.
