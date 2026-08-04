# Tamper Evidence, Storage, And Access

**Load when:** Protected storage, immutability, tamper evidence, missing-record detection, validation, or privileged evidence access changes.

**Do not load when:** No stored audit-evidence integrity, verification, or administration boundary changes.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `evidence-record`, `validation-plan`, `proof-limit`

## One Decision

Select one storage and verification composition that states what each mechanism covers, detects scoped alteration and loss, and gives neither producers, subjects, nor one admin an invisible bypass.

## Decision Matrix

| Boundary | Required decision | Failure signal |
|---|---|---|
| Canonical object | Exact bytes/fields, schema, source identity, transformation state, and integrity scope | A mutable view is treated as the sole evidence |
| Write path | Authorized append path, acknowledgement meaning, duplicate behavior, failure durability, and reconciliation | Producer success proves protected storage |
| Storage | Immutability/tamper-evidence mechanism, versioning, replication, failure boundary, and deletion behavior | Marketing label replaces effective permissions |
| Integrity | Bound bytes and identity for hashes/signatures plus sequence/checkpoint/reconciliation scope for deletion, truncation, gaps, replay, reorder, and rollover | An individual hash is called proof against deletion or sequence loss |
| Verifier | Independent identity, trusted keys/configuration, location binding, schedule, alerts, and failure owner | Enabling digest creation is called validation |
| Administration | Separate read/write/delete/hold/export/key/policy authority with break-glass limits | One admin can alter records and verifier |
| Detection | Missing, changed, duplicated, replayed, reordered, invalid, and unverifiable disposition | Invalid evidence is silently skipped |

## Verification

- Alter and delete records, indexes, checkpoints, signatures, keys, and configuration at the storage boundaries in scope.
- Insert, replay, duplicate, truncate, reorder, and omit records across restart and rollover.
- Exercise producer, evidence-admin, verifier, export, and break-glass identities against denied paths.
- Validate from an independent trust boundary and alert for each unverifiable interval.

## Primary Sources

- [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
- [NIST SP 800-92: Log Management](https://csrc.nist.gov/pubs/sp/800/92/final)
- [RFC 5848: Signed Syslog Messages](https://www.rfc-editor.org/rfc/rfc5848.html)
- [AWS CloudTrail log integrity validation](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-intro.html)
- [AWS CloudTrail digest structure](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-digest-file-structure.html)

Official sources were accessed on 2026-07-26.

## Proof Limits

RFC 5848 supplies a signed-stream model, not a current algorithm choice. CloudTrail validation covers referenced files after delivery, not source completeness or every export. A hash or signature proves only the bytes and context it binds; missing-record, truncation, replay, and reorder claims require their selected sequence, checkpoint, anchor, or reconciliation composition. Storage immutability cannot prove truthful emission or independence from all privileged paths.
