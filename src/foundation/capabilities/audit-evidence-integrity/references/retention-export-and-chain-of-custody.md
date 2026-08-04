# Retention, Export, And Chain Of Custody

**Load when:** Retention, hold, expiry, export, transformation, transfer, verification, or custody changes audit-evidence availability or meaning.

**Do not load when:** No audit lifecycle, export artifact, or custody handoff changes and current evidence closes availability.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `decision-record`, `residual-risk`

## One Decision

Select one policy-owned lifecycle and custody contract that preserves scoped meaning and integrity across retention, export, transformation, and handoff.

## Decision Matrix

| Boundary | Required decision | Failure signal |
|---|---|---|
| Authority | Retention/hold source, scope, owner, effective time, conflicts, review, and release | Engineer invents a universal period |
| Copies | Records, indexes, replicas, backups, exports, integrity metadata, keys, and manifests | One store defines the whole lifecycle |
| Hold/expiry | Eligible objects/versions, propagation, late arrival, deletion suppression, release, and gaps | Hold label does not cover new versions |
| Disposal | Authorized target, preconditions, verification, residual copies, and audit record | Expiry silently removes evidence |
| Export scope | Query/selector, source snapshot, time range, schema/version, exclusions, counts, and completeness limit | Download is called the full record |
| Transformation | Original identity/hash, tool/version, parameters, derived schema, row mapping, loss, and verifier | CSV conversion becomes canonical evidence |
| Custody | Artifact/manifest identity, actor, purpose, time, location, access, transfer, receipt, and condition | Handoff occurs through an unrecorded channel |
| Verification | Hash/signature, trusted key, original-location binding, verification time/result, and exception owner | Hash is copied without recomputation |

## Verification

- Exercise retain, hold, late arrival, release, expiry, deletion, restore, and conflicting-policy paths across the retained and exported copy set.
- Reproduce exports from bound selectors; compare counts, identities, exclusions, and source snapshots.
- Transform, split, merge, compress, transfer, and re-import while verifying lineage and integrity.
- Break a custody handoff, manifest, key, or verifier and require an explicit evidence gap.

## Primary Sources

- [NISTIR 8387: Digital Evidence Preservation](https://www.nist.gov/publications/digital-evidence-preservation-considerations-evidence-handlers)
- [NIST SP 800-86: Forensic Techniques](https://csrc.nist.gov/pubs/sp/800/86/final)
- [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
- [Amazon S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)
- [CloudTrail query-result validation](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-query-results-validation.html)

Official sources were accessed on 2026-07-26.

## Proof Limits

These sources do not establish legal admissibility, retention obligations, or regulatory compliance. Provider locks and signatures are version-, permission-, object-, and configuration-specific. A valid export proves scoped bytes, not query completeness, semantic fidelity, or an unbroken prior custody history.
