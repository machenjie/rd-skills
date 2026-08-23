# Retention, Export, And Chain Of Custody

**Load when:** Retention, hold, expiry, export, transformation, transfer, verification, or custody changes audit-evidence availability or meaning.

**Do not load when:** No audit lifecycle, export artifact, or custody handoff changes and current evidence closes availability.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `decision-record`, `residual-risk`

## Root-Relocated Lifecycle Rules

- Enforce retention and hold policy across records, indexes, replicas, backups, exports, and verification material without legal conclusions.
- Bind access, export, and custody to selector, time range, schema, counts, integrity proof, actor, purpose, transfer, receipt, and verification.
- A retention gap silently removes evidence.
- Export transformation changes meaning or integrity.
- A custody gap leaves a handoff unverifiable.
- Verify exports across transformation/handoff; exercise retention, hold, expiry, and custody transitions.

## Lifecycle And Custody Decision

Bind policy/copies; hold/expiry/disposal; export selector/snapshot/schema/counts; transformation identity/tool/lineage/loss; custody artifact/actor/purpose/transfer/receipt; and trusted verification with exception owner.

## Verification, Sources, And Limits

Exercise lifecycle conflicts, reproduce/transform bound exports, and break handoffs/verifiers. Sources: [NISTIR 8387](https://www.nist.gov/publications/digital-evidence-preservation-considerations-evidence-handlers), [NIST 800-86](https://csrc.nist.gov/pubs/sp/800/86/final), [NIST 800-53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html), and [CloudTrail query validation](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-query-results-validation.html), accessed 2026-07-26. They do not establish legal/compliance duties; configured controls and valid bytes do not prove query completeness, semantic fidelity or prior custody.
