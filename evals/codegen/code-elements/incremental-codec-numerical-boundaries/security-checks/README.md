# Security Checks

## Threat Surface

This deterministic fixture admits untrusted byte lengths. It has no network, credentials, executable input, or production authority.

## Required Checks

Reject oversized frames before payload accumulation and reject invalid write progress. Preserve bounded finite test execution.

## Rejection Cases

Accepting truncated EOF as a complete stream fails the format contract. Replaying an acknowledged write prefix or treating iteration exhaustion as convergence fails correctness. These checks do not establish a general security assessment.
