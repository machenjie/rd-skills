# Example Output

```markdown
## Backup Recovery Plan

mode_selected: destructive change safety + key/config/schema restore + ransomware/insider resilience

source_evidence:
- Backup policy for document metadata DB.
- Object bucket versioning and object-lock configuration.
- KMS key rotation policy.
- Restore runbook and last quarterly drill report.
- Repository graph found document search index and feature flag dependency.
- graph_memory_trajectory_judgment: prior "restore tested" memory accepted only for DB snapshot; rejected for object bucket and KMS key restore because no current drill evidence was found.

protected_dataset:
- document metadata table: customer-owned PII, owner Storage Ops.
- object storage files: customer documents, owner Storage Ops.
- encryption key mapping: critical key metadata, owner Security Platform.
- derived search index: rebuildable from metadata + objects, owner Search Platform.

business_impact_analysis:
- Loss or unreadable documents causes legal/customer-impacting outage.
- Business owner approved RPO 15 minutes and RTO 2 hours for affected-tenant restore.

rpo_rto:
- Target RPO: 15 minutes; last DB drill actual 6 minutes.
- Target RTO: 2 hours; last DB-only actual 48 minutes.
- Gap: object + key restore actual not proven; drill required before production re-key.

backup_strategy:
- DB: PITR with 7-day window plus daily full snapshot.
- Objects: versioning + immutable 30-day object lock in backup account.
- Keys: old KMS key versions retained for full backup retention window.

storage_topology:
- Production account cannot delete backup account immutable objects.
- Backup deletion API has security alert and two-person approval.

restore_scope:
- Metadata DB + object bucket versions + key mapping + KMS key version + search index rebuild + feature flags + compatible app release tag.

restore_runbook:
- Restore DB to timestamp.
- Restore object versions for affected tenant.
- Validate key mapping and decrypt sampled documents.
- Rebuild search index from restored metadata.
- Run application canary read path for restored tenant.

validation_plan:
- Full tenant document count.
- Object checksum comparison for sampled and high-value documents.
- KMS decrypt sample using old and new key mappings.
- Application read canary.
- Search index count after rebuild.

changed_recovery_to_validation_map:
- Re-key operation -> pre-change snapshot + key restore drill.
- Object storage -> object version restore + checksum validation.
- Metadata DB -> PITR restore + row counts.
- Search index -> rebuild runbook + post-rebuild counts.
- Ransomware copy -> object-lock policy read + deletion-denied evidence.

handoff_boundaries:
- `secret-configuration-security`: KMS key custody and rotation approval.
- `data-migration-design`: re-key batching and idempotent migration.
- `release-rollback`: release trigger and rollback/forward-fix plan.
- `delivery-release-gate`: production approval after drill.

residual_risks:
- Cross-region full restore not tested in this plan.
- Partner document export cache is outside current restore scope and needs owner confirmation.

evidence_limits:
- DB-only prior drill does not prove object/key/search restore.
- Staging restore does not prove production region failover timing.
```
