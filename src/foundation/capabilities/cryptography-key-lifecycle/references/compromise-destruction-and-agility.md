# Compromise, Destruction, And Agility

**Load when:** Suspected compromise, revocation, destruction, cryptographic erasure, algorithm deprecation, or migration changes key or data availability.

**Do not load when:** No compromise, destructive action, retained-key disposition, or cryptographic transition decision changes.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `failure-decision`, `boundary-decision`, `residual-risk`

## One Decision

Select one contained lifecycle transition that addresses affected key use and data while preserving authorized recovery, evidence, and algorithm migration.

## Decision Matrix

| Boundary | Required decision | Failure signal |
|---|---|---|
| Compromise scope | Key/material versions, uses, principals, data, ciphertexts, exports, replicas, backups, and time window | The reported key alias alone defines the scope |
| Containment | Disable/revoke use, isolate authority, preserve evidence, notify owners, and bound emergency access | Rotation proceeds while compromised use remains |
| Replacement | Fresh material, consumer adoption, rewrap/re-encrypt need, validation, and old-key disposition | Revocation is called complete without data impact |
| Destruction target | Exact key copies, provider objects, caches, exports, replicas, backups, and dependent ciphertext | One control-plane deletion implies universal erasure |
| Safeguard | Authority, approval, hold, inventory, dry run, waiting/recovery window, and irreversibility | Destruction can strand required data |
| Destruction proof | Provider evidence, residual copies, recovery denial, metadata retention, and stated limits | A successful request proves physical erasure |
| Agility inventory | Algorithms, parameters, keys, certificates, formats, libraries, protocols, hardware, data, and consumers | Dependency discovery starts after deprecation |
| Transition | Current policy, target support, dual-read/write needs, downgrade prevention, milestones, and retirement | Old and new formats coexist without closure |

## Verification

- Simulate compromise before/after use, rotation, export, backup, and consumer propagation.
- Verify revoked material cannot perform changed operations while authorized retained data remains readable where required.
- Exercise deletion safeguards and prove the named recovery or irreversible outcome.
- Migrate representative old/new artifacts and reject deprecated or downgraded paths at the defined milestone.

## Primary Sources

- [NIST SP 800-57 Part 1 Rev. 5](https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final)
- [NIST SP 800-57 Part 2 Rev. 1](https://csrc.nist.gov/pubs/sp/800/57/pt2/r1/final)
- [NIST CSWP 39upd1: Crypto Agility](https://csrc.nist.gov/pubs/cswp/39/upd1/considerations-for-achieving-crypto-agility/final)
- [NIST SP 800-131A Rev. 2](https://csrc.nist.gov/pubs/sp/800/131/a/r2/final)
- [AWS KMS key deletion](https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html)

Official sources were accessed on 2026-07-26.

## Proof Limits

Revocation does not erase copies or undo prior disclosure. Provider deletion evidence does not prove erasure outside its boundary. Crypto-agility guidance does not set organization policy or prove migration completeness, downgrade resistance, or compliance.
