# Backup Recovery Evidence Patterns

Use this reference when backup-recovery closure depends on evidence quality, validation freshness, repository inspection, prior task evidence, observable action sequence, tool permission boundaries, or recovery-to-validation mapping. Keep it as an evidence map, not a second backup tutorial.

## Recovery-To-Validation Map

| Recovery claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Protected datasets are known | Current data-store, object, queue, index, key, config, runbook, and owner inventory inspected | The plan covers the inspected recovery surface | Hidden stores, manual exports, provider caches, or uninspected tenants |
| RPO/RTO is accepted | Business impact analysis, business owner approval, target, last drill actual, and gap owner | The named owner accepted the measured loss and time window | Future volume growth or incident stress stays within target |
| Backup artifact is usable | Restore command, artifact id/path, validator, exit code or manual pass, dataset size, and timestamp | The named artifact restored under the tested conditions | Cross-region copy, older key version, or full production scale unless tested |
| Atomic restore scope is complete | Dependency map for DB, objects, indexes, queues/offsets, keys, config, secrets, flags, and compatible app version | Inspected dependencies can be restored together | Unknown downstream consumers or partner caches are correct |
| Ransomware copy survives compromise | Immutable/off-account policy read, deletion-denied evidence when safe, key separation, and deletion alert | Production credentials should not delete or decrypt the recovery copy | Backup admin compromise or untested incident procedure is covered |
| Retention and erasure are correct | Regulatory class, retention window, legal hold owner, erasure/crypto-shred plan, and audit evidence | The inspected policy matches declared retention and erasure duties | All jurisdictions, historic backups, or manual exports are compliant |
| Prior drill evidence is fresh | Prior report reconciled with current schema, key, config, region, data volume, runbook, and validation command | Previous evidence still covers the current recovery claim | Later source/config/key/schema/report edits remain covered |

## Evidence Quality Labels

- **Strong evidence**: current restore or failover command/drill, named artifact/report, exit code or manual pass/fail, dataset size, dependency scope, owner, timestamp, and freshness after final material change.
- **Weak evidence**: config or snapshot existence, old drill report, wiki runbook, or dashboard screenshot without current restore proof.
- **Missing evidence**: no owner, no RPO/RTO approval, no artifact id, no restore command, no key-retention proof, or no validation result.
- **Invalid evidence**: empty-schema drill, database-only restore for multi-store product state, same-account snapshot as ransomware proof, or stale prior evidence after schema/key/config/region change.

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, old runbooks, incident notes, provider dashboards, and prior execution results as discovery inputs until current source and validation confirm them.
- Accept a prior "restore tested", "RTO met", "keys retained", or "off-account copy exists" claim only when current schema, data volume, key policy, storage topology, region, runbook, and validator still match.
- Reject or downgrade evidence after edits to schema, migrations, KMS/key policy, bucket lifecycle, object-lock policy, queue/index dependencies, config/secrets, runbook, reports, or build/install outputs.
- Map every accepted recovery claim to a command, validator, drill report, policy-as-code path, telemetry query, owner approval, or explicit not-run residual risk.

- If restore drill in local, staging, or throwaway environment, record dataset, artifact, target environment, cleanup/reset, absence of production credentials, and stop condition.
- If production backup, restore, failover, cloud console, KMS, bucket lock, deletion test, or retention change, require explicit permission, dry-run or read-only proof when possible, rollback/forward-fix path, redaction, and stop condition.
