# Security Checks

## Threat Surface

Pricing tests may create unsafe seams if they bypass authorization, tenant, or tier lookup behavior.

## Required Checks

- Test seams do not allow callers to override tenant or permission decisions in production.
- Fake customer tier data does not include real customer PII.
- Diagnostic assertions do not expose tokens, API keys, or customer identifiers.

## Rejection Cases

- Reject a test seam that bypasses production authorization behavior.
- Reject fixture data copied from production customers.
- Fail when error output leaks customer tier provider internals.
