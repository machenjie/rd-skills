# Security Checks

## Threat Surface

This benchmark touches SSRF prevention, URL canonicalization, network allowlist, safe denial responses. A flawed implementation can expose data, weaken integrity, hide operational failure, or ship a release path that cannot be safely reviewed.

## Required Checks

- Verify that validation canonicalizes scheme, host, port, and resolved addresses before fetch.
- Verify that network policy is centralized and covered by unit and integration tests.
- Verify that error handling fails closed for parse, DNS, redirect, and timeout failures.
- Verify that logs capture reason codes without storing sensitive URL query values.

## Rejection Cases

- Reject any solution that uses string prefix allowlists that accept attacker controlled hostnames.
- Reject any solution that uses checking only the original URL before following redirects.
- Reject any solution that uses allowing localhost or cloud metadata addresses for convenience.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
