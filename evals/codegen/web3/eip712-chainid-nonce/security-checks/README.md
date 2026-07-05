# Security Checks

## Threat Surface

This benchmark touches EIP-712 domain validation, chain id binding, nonce replay protection, wallet session security. A flawed implementation can expose data, weaken integrity, hide operational failure, or ship a release path that cannot be safely reviewed.

## Required Checks

- Verify that typed data validation matches the declared domain and message schema.
- Verify that nonce persistence is durable enough for concurrent login attempts.
- Verify that tests include wrong chain, wrong domain, reused nonce, and expired nonce.
- Verify that session creation occurs only after all signature checks pass.

## Rejection Cases

- Reject any solution that uses recovering an address without validating chain id and domain.
- Reject any solution that uses storing nonces only in process memory.
- Reject any solution that uses accepting reused or expired nonces for successful authentication.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
