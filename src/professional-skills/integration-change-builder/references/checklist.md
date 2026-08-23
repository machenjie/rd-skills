# Integration Checklist

- Name provider, owner, environment, producer/consumer contracts, version skew, authority, and partial-failure behavior.
- Define timeout, retry/backoff, circuit breaking, aggregate budget, idempotency, duplicates, unknown outcomes, ordering, compensation, and reconciliation.
- Derive the exact signed representation and permitted transformation or canonicalization from the current provider contract.
- Preserve raw bytes only when the provider contract defines raw bytes as the signed representation.
- Prove signature verification, freshness, and replay checks finish before representation-changing operations or effects.
- Keep payload, signature, token, cookie, authorization, secret, and credential data out of logs, source, images, configuration, and generated artifacts; own credential storage, rotation, and least privilege.
- Keep provider and generated models inside the adapter unless version, null, and default mappings are explicit.
- Validate sandbox/production and rate-limit differences, recovery, the integrated diff, consumers, and contract/failure/replay/monitoring behavior.
- Record provider/version, credential, artifact, consumer, log, reconciliation, release, skipped boundaries, command/result, freshness, proof limit, rollback, residual risk, next owner, and handoff.
