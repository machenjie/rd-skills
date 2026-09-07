# Tamper Evidence, Storage, And Access

**Load when:** Protected storage, immutability, tamper evidence, missing-record detection, validation, or privileged evidence access changes.

**Do not load when:** No stored audit-evidence integrity, verification, or administration boundary changes.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `evidence-record`, `validation-plan`, `proof-limit`

## Root-Relocated Integrity Rules

- Preserve canonical records and schema versions while treating views and transformations as derived evidence with lineage.
- Separate administration from producers and subjects, protecting records, integrity metadata, keys, policy, validation configuration, and privileged-use evidence.
- Select one composition-specific verification contract and bind what sequences, checkpoints, signatures, hashes, storage controls, and reconciliation each cover. An isolated hash proves only its bound bytes and cannot by itself prove deletion, truncation, replay, or reordering.
- A mutable admin path alters protected evidence.
- Delete, alter, replay, duplicate, reorder, skew clocks, break correlation, and exercise privileged access.

## Integrity And Access Decision

Bind canonical bytes/source/lineage, durable append/reconciliation, effective storage/deletion, hash/signature and sequence/checkpoint coverage, independent verifier, separated administration/break-glass, and explicit gap dispositions.

## Verification, Sources, And Limits

Alter/omit/replay evidence and exercise producer/admin/verifier identities. Sources: [NIST 800-53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [NIST 800-92](https://csrc.nist.gov/pubs/sp/800/92/final), [RFC 5848](https://www.rfc-editor.org/rfc/rfc5848.html), [CloudTrail validation](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-intro.html), and [digest structure](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-digest-file-structure.html), accessed 2026-07-26. They do not select algorithms or prove truthful emission, pre-delivery completeness, sequence loss or absence of privileged bypass without the selected composition.
