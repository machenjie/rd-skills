# Rotation, Versioning, And Recovery

**Load when:** Key rotation, version routing, rewrap, re-encryption, backup, recovery, escrow, or retirement changes decryptability.

**Do not load when:** No key transition occurs and current evidence proves every retained ciphertext has an authorized decrypt path.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `validation-plan`, `proof-limit`

## One Decision

Select one versioned transition and recovery contract that introduces new protection without losing, reviving, or silently stranding retained data.

## Decision Matrix

| Boundary | Required decision | Failure signal |
|---|---|---|
| Identity | Stable key identity, material version, purpose, status, provenance, and envelope binding | Alias alone becomes historical identity |
| Write/read sets | Active encrypt version, allowed decrypt versions, propagation, cache refresh, and failure | Writer advances before readers can resolve it |
| Rotation | Trigger, generation, activation, overlap, adoption evidence, rollback, and retirement | Schedule completion is called migration |
| Data transition | Rewrap versus re-encrypt scope, inventory, checkpoint, idempotency, and mixed-state reads | Key rotation is assumed to rewrite ciphertext |
| Recovery | Recoverable key types, copies, protection, integrity, location separation, authorization, and exercise | Backup exists but cannot restore keys and data together |
| Escrow | Explicit policy need, custodians, split authority, access evidence, expiry, and destruction | Escrow becomes an unrestricted decrypt path |
| Retirement | Last-use evidence, retained ciphertext, backups, legal/retention needs, revoke/disable/destroy order | Old material disappears before decrypt closure |

## Verification

- Encrypt and decrypt across the supported key/data version matrix and mixed rollout states.
- Interrupt activation, rewrap/re-encryption, rollback, recovery, and retirement at each durable boundary.
- Restore protected data with its exact key lineage, then validate domain reads and denied recovery.
- Prove inaccessible, mismatched, expired, revoked, and unsupported versions fail safely.

## Primary Sources

- [NIST SP 800-57 Part 1 Rev. 5](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final)
- [NIST SP 800-133 Rev. 2: Key Generation](https://csrc.nist.gov/pubs/sp/800/133/r2/final)
- [AWS KMS data keys](https://docs.aws.amazon.com/kms/latest/developerguide/data-keys.html)
- [AWS KMS key rotation](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html)

Official sources were accessed on 2026-07-26.

## Proof Limits

NIST guidance does not prove organization policy, custody, or production restoration. AWS rotation and version selection are product-, key-type-, origin-, and configuration-specific. A local round trip cannot establish full ciphertext inventory or recovery under production access controls.
