# Integration Checklist

- Identify provider contract, ownership, and environment.
- Define timeout, retry, backoff, and circuit breaker policy.
- Define idempotency keys and duplicate handling.
- Derive the exact signed representation and permitted transformation or canonicalization from the current provider contract.
- Preserve raw bytes only when the provider contract defines raw bytes as the signed representation.
- Prove signature verification, freshness, and replay checks finish before representation-changing operations or effects.
- Define replay identity and out-of-order delivery behavior from the current provider contract.
- Define credential storage, rotation, and least privilege.
- Validate sandbox and production differences.
- Plan reconciliation, backfill, and manual repair.
- Add contract, failure, replay, and monitoring tests.
- Record provider/version, credential, generated-artifact, consumer, log, reconciliation, release, and skipped boundaries.
- Record command, exit status, artifact, freshness, covered failure path, proof limit, and behavior-preservation evidence.
- State sandbox/production parity, rate-limit, credential, replay, drift, rollback, residual risk, next owner, and handoff.
