# Security Checks

## Threat Surface

The adapter parses supplied fixture text and returns a new string. Tests execute only fixed local examples with an in-memory import seam. No external effect is authorized.

## Required Checks

Keep unresolved source unchanged. Preserve non-target text and reject invalid syntax without file mutation.

## Rejection Cases

Rewriting unrelated symbols or hiding unresolved use fails. This fixture is not a sandbox or a general untrusted-code security assessment.
