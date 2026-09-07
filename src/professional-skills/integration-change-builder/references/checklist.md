# Integration Checklist

- Name provider, owner, environment, producer/consumer contracts, version skew, authority, and partial-failure behavior.
- Define timeout, retry/backoff, circuit breaking, aggregate budget, idempotency, duplicates, unknown outcomes, ordering, compensation, and reconciliation.
- Derive the exact signed representation and permitted transformation or canonicalization from the current provider contract.
- Preserve raw bytes only when the provider contract defines raw bytes as the signed representation.
- Before verification, allow only the bounded preprocessing required to form the provider-defined signed input. Complete signature, freshness, and replay checks before trusting payload values, applying business transformations, or producing effects.
- Exclude secrets, replayable authorization material, and unapproved sensitive payloads or signatures from logs, source, images, configuration, and generated artifacts. Retain only purpose-required, authorized, classified non-sensitive fixtures or evidence with bounded exposure and provenance.
- Name the owner of credential storage, rotation, and least privilege.
- Keep provider and generated models inside the adapter unless version, null, and default mappings are explicit.
- Validate sandbox/production and rate-limit differences, recovery, the integrated diff, consumers, and contract/failure/replay/monitoring behavior.
- Record provider/version, credential, artifact, consumer, log, reconciliation, release, skipped boundaries, command/result, freshness, proof limit, rollback, residual risk, next owner, and handoff.
