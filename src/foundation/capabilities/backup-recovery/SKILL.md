---
name: backup-recovery
description: Requires core data changes to define backup, restore, RTO, RPO, ownership, and recovery validation before production risk is accepted.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "70"
changeforge_version: 0.1.0
---

# Mission

Ensure core data and critical state can be **recovered to a defined point with bounded loss within a defined time** after destructive change, corruption, ransomware, outage, operator error, region failure, or supply-chain attack — proven by tested restores, not by the existence of backups.

# When To Use

Use this capability when a change creates, migrates, deletes, transforms, archives, rekeys, reindexes, encrypts, imports, exports, replicates, or otherwise risks: production databases (relational, NoSQL, time-series, vector), object storage (S3/GCS/Azure Blob), message broker durable state (Kafka topics, RabbitMQ queues), search indexes, cache state where it has become canonical, secrets stores, encryption keys (KMS), configuration repositories, audit logs, or any data whose loss has legal, financial, or operational consequence.

# Do Not Use When

Do not use this capability to treat backup as a substitute for safe migration design (`data-migration-design`), safe rollout (`release-rollback`), idempotent operations (`idempotency-retry-design`), or correct authorization (`authentication-authorization`). Backup is the last line of defense, not the first.

# Non-Negotiable Rules

- Every core dataset has a **named RPO (Recovery Point Objective)** and **RTO (Recovery Time Objective)** approved by the business owner — not assumed by engineering.
- **Restore is tested**, not just configured. Untested backup = no backup. Quarterly minimum for critical systems; per-release for systems under active schema change.
- **3-2-1 rule (minimum)**: 3 copies, 2 different media/locations, 1 off-site/off-account. For ransomware resilience extend to **3-2-1-1-0**: + 1 immutable/air-gapped + 0 errors verified.
- **Immutable / WORM backups** are mandatory where ransomware is a credible threat (any system with internet exposure, any system holding regulated data). Use object-lock (S3 Object Lock in compliance mode, Azure immutable blob, GCS bucket retention) so that even root credentials cannot delete during the lock window.
- **Backups are encrypted at rest and in transit**; encryption keys are stored **separately** from the backup storage (a backup encrypted with a key that lives in the same blast radius is not protected against tenant-wide credential compromise).
- **Recovery scope is documented atomically**: a database is useless without its object-storage attachments, search index, encryption keys, configuration, message-broker offsets, and the application version that knows the schema. Restoring the database alone produces a non-operating system.
- **RTO/RPO/ownership/restore steps/validation/notification** are recorded in a **runbook** that an on-call engineer who has never seen the system can execute at 02:00 with no other documentation.
- **Irreversible operations** (DROP TABLE in production, mass DELETE, schema downgrade, key destruction, region decommission) require: pre-operation backup snapshot, dry-run, two-person approval, rollback plan, and post-operation verification.
- **Backup retention** must meet legal hold, regulatory minimums, and operational discovery windows — and must explicitly delete beyond them where privacy regulation requires (GDPR right to erasure, etc.).
- **Access to backups** follows least-privilege; access is audited; production credentials cannot grant unrestricted backup deletion.
- **Recovery drills** measure actual RTO/RPO achieved and feed back into capacity, automation, and runbook revisions.

# Industry Benchmarks

Anchor against: **ISO/IEC 27031** (ICT readiness for business continuity), **ISO 22301** (Business Continuity Management Systems), **NIST SP 800-34 Rev. 1** (Contingency Planning Guide for Federal Information Systems) and the BIA (Business Impact Analysis) discipline, **NIST SP 800-209** (Security Guidelines for Storage Infrastructure), **ITIL Service Continuity Management**, **AWS Well-Architected Reliability Pillar** (REL09 backup data, REL13 disaster recovery), **Google SRE Workbook — Data Integrity** (24 combinations of data loss requires layered defense; "no backup is good if it cannot be restored"), **DORA EU Regulation** (Digital Operational Resilience Act, financial sector, mandatory recovery objectives + testing), **PCI-DSS v4 §12.10** (incident response includes data restoration), **HIPAA §164.308(a)(7)** (data backup, disaster recovery, emergency mode), **SOC 2 CC7.4 / A1.2** (backup and recovery), **GDPR Art. 32** (ability to restore availability and access to personal data in a timely manner), **Veeam 3-2-1-1-0 rule** (anti-ransomware extension), **CISA Stop Ransomware guidance**, **NIST SP 800-184** (Guide for Cybersecurity Event Recovery), **OWASP CWE-1009** (Audit Trail), **DAMA-DMBOK** data lifecycle. For DR site strategies: **AWS DR patterns** (Backup & Restore → Pilot Light → Warm Standby → Multi-Site Active/Active), **Gartner DR tier model**.

### RPO / RTO Tier Reference

| Tier | Example workload | RPO target | RTO target | Typical strategy |
| --- | --- | --- | --- | --- |
| 0 — Mission-critical | Payment authorization, life-safety | ≈ 0 (synchronous replication) | < 1 min | Multi-region active-active + sync replication + automated failover |
| 1 — Business-critical | Customer-facing transactional DB | ≤ 5 min | ≤ 1 hr | Warm standby cross-region + continuous WAL shipping |
| 2 — Important | Internal SaaS, reporting | ≤ 1 hr | ≤ 4 hr | Hot backup hourly + pilot-light DR |
| 3 — Standard | Analytics, dev/test | ≤ 24 hr | ≤ 24 hr | Daily snapshot, backup-and-restore |
| 4 — Archive | Compliance archive, audit trail | ≤ 7 days | Days | Cold storage + immutable retention |

RPO and RTO **must be assigned by the business owner per dataset**, not inherited generically. A 99.9% SLO with no defined RPO is incoherent.

### Backup Type Selection Matrix

| Backup type | Recovery point granularity | Storage cost | Restore complexity | Pick when |
| --- | --- | --- | --- | --- |
| **Full** | Per snapshot | Highest | Simple | Small datasets; weekly baseline for incremental chains |
| **Incremental** | Last full + chain | Lowest | Higher (chain dependency) | Daily/hourly cadence, large datasets |
| **Differential** | Last full + last diff | Medium | Medium | Balance between full and incremental |
| **Continuous (CDC / WAL / oplog shipping)** | Per-transaction (seconds) | Medium-high | Requires point-in-time recovery tooling | RPO ≤ minutes; transactional databases |
| **Snapshot (storage-level)** | Per snapshot | Low (CoW) | Fast | Same-region recovery; not a substitute for off-site backup |
| **Logical export (`pg_dump`, `mongodump`)** | Per export | Low | Slow restore; format-portable | Schema migration safety net; cross-version moves |
| **Object versioning + MFA delete** | Per object version | Low | Per-object | S3/GCS bucket protection against accidental delete |
| **Immutable backup (Object Lock / WORM)** | Per backup | Higher | Same as base | Ransomware resilience, compliance retention |

### Disaster Recovery Strategy Selection

| Strategy | RTO | RPO | Cost | Pick when |
| --- | --- | --- | --- | --- |
| **Backup & Restore** | Hours–days | Hours | $ | Standard apps; can tolerate downtime |
| **Pilot Light** | Tens of minutes | Minutes | $$ | Core stays warm; scale up on failover |
| **Warm Standby** | Minutes | Seconds–minutes | $$$ | Reduced capacity always running |
| **Multi-Site Active/Active** | ≈ 0 | ≈ 0 | $$$$ | Mission-critical; tolerate split-brain complexity |

### Failure-Mode Coverage Matrix (the 24 combinations principle)

Recovery design must defend against multiple intersecting failure modes — not one at a time. Tabulate:

| Loss type \ Source of loss | Hardware | Software bug | Operator error | Malicious insider | External attack | Region failure |
| --- | --- | --- | --- | --- | --- | --- |
| Single record |  |  |  |  |  |  |
| Single table / index |  |  |  |  |  |  |
| Whole database |  |  |  |  |  |  |
| Encryption key |  |  |  |  |  |  |
| Backup itself |  |  |  |  |  |  |

Each cell needs a defined detection + restore path. The corner case "attacker deleted both production and backups using leaked admin credentials" is the case immutable WORM backups exist to cover.

# Selection Rules

Select this capability when **recovery from data loss or corruption** is primary. Adjacent routing:

- Prefer `data-migration-design` when the question is the migration sequence and rollback strategy itself.
- Prefer `release-rollback` when the question is reverting application code, not data.
- Prefer `observability` when the question is detection of corruption or loss.
- Prefer `secret-configuration-security` for key custody and rotation lifecycle.
- Prefer `reliability-observability-gate` for SLO/SLA and DR readiness review.
- Use **with** `delivery-release-gate` when a release demands a pre-deploy snapshot or DR exercise.

# Risk Escalation Rules

Escalate when data is: financial (ledger, billing, settlement), regulated (PII/PHI/PCI), customer-owned (loss = legal liability), tenant-wide (single bug → all-customer impact), irreversible (destructive cleanup with no source), high-volume (multi-TB restore time risk), encrypted with rotated keys (must preserve key history), cross-region (data residency + transfer cost), cross-service (dependency chain restore), required for **legal hold / e-discovery / audit**, or under **ransomware threat** (any internet-exposed asset). Escalate when a proposed RPO/RTO has never been tested at full data volume. Escalate any decommission of a backup system, region, or key.

# Critical Details

Backups matter only if restore works at scale, in time, with the right scope. Apply these refinements:

- **Restore scope is the hard part, not backup creation.** A typical SaaS service in production at 02:00 needs: primary DB (transactional state), object storage (user uploads, attachments), search index (Elasticsearch/OpenSearch), cache warmup data, message-broker offsets (lest replays cause double-processing), encryption keys (KMS), application config + feature flags, secrets, the deployed application version compatible with the data schema, and downstream consumer alignment. Missing any → partially functional restoration.
- **Application-schema alignment.** Restoring data from 14 days ago against today's application can fail loudly (schema mismatch) or silently (semantic mismatch, e.g., column was repurposed). Document **schema-version compatibility window**; consider keeping reversible migration scripts for the backup retention horizon.
- **Point-in-time recovery (PITR)** lets you target an instant before corruption (e.g., a bad deploy that mass-updated 1M rows). Most managed databases (RDS, Aurora, Cloud SQL, Cosmos DB) support PITR within a window; verify and document the window.
- **Logical vs physical restore.** Logical export (`pg_dump`) is portable across versions but slow on TB-scale; physical/snapshot is fast but version-coupled. Keep both for critical systems.
- **Restore wall time** scales with data size + network + index rebuild + cache warm. Measure on representative data. A 10 TB restore that "should take 4 hours" can take 40 in practice; plan for it.
- **Corruption detection.** Backups can replicate corruption that exists in the source. Defenses: page-level checksums in DB, periodic logical consistency checks, multi-version retention (so an older clean version exists), independent reconciliation jobs comparing aggregates.
- **Ransomware-class threats.** Modern ransomware operators specifically delete backups before encrypting production. Defenses: immutable/WORM backups, separate credentials for backup deletion (MFA delete), cross-account backup ownership (production cannot delete it), monitoring on backup-deletion APIs.
- **Key custody and rotation.** Encrypted backups need their decryption keys preserved across the backup retention period. If keys are rotated and old keys destroyed, old backups become permanently unreadable. Use envelope encryption + key versioning.
- **Compliance erasure obligations** (GDPR right to erasure, CCPA) extend into backups but with documented "next eligible deletion" windows — practical pattern is to encrypt per-subject and destroy the per-subject key on deletion request, which cryptographically erases without rewriting backups.
- **Region failover** has data-egress, latency, and DNS-TTL considerations; failover that depends on a DNS change with TTL 1 hour cannot meet RTO ≤ 5 min.
- **Restore validation** ≠ "the restore command succeeded". Validation must check: row counts ≈ source, key checksums match, sample queries return expected aggregates, application starts and serves canary traffic.
- **Drill cadence.** Quarterly minimum for critical; per-release for systems with frequent schema change. Record actual RTO/RPO achieved; gap-close into runbooks.
- **Drill realism.** Drilling restore into a sandbox proves the artifact is readable; drilling failover with synthetic production traffic proves the system works. Aim for the latter at least annually.
- **Off-site / off-account separation.** Backups in the same AWS account as production are vulnerable to account compromise; cross-account or cross-cloud separation raises the bar.
- **Backup observability.** Alerts on: backup job failure, backup job missed schedule, backup size anomaly (sudden drop = source corruption or attack), restore latency drift, backup storage approaching retention cap.
- **Cost vs RPO trade.** Continuous replication for tier-0 vs daily snapshot for tier-3 differs by order(s) of magnitude in cost; explicit tiering avoids paying tier-0 cost for tier-3 data and vice versa.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| "We have backups" without restore drill in 12 months | The backup format changed; restores fail at incident time |
| Backup encryption key stored in same account / region / vault | Single credential compromise loses both production and backup |
| Same root credentials can delete production and backups | Ransomware deletes both in one minute |
| RPO defined per system (e.g., "1 hour") but PITR window is 24 hours of WAL only | True RPO inherits the shortest dependency; quoted RPO is wrong |
| Database restored without object storage attachments | "Order #1234 has no invoice PDF" → broken product |
| Restore test from snapshot only, not from cross-region copy | When the region fails, the cross-region copy was never proven |
| Mass DELETE shipped to production without snapshot | Mistake = unrecoverable beyond PITR window; PITR not enabled |
| GDPR erasure request triggers backup rewrite (expensive, slow, often fails) | Use crypto-shred (per-subject key) instead |
| Backup deletes scheduled silently to "save cost" | Compliance retention violated; discovered at audit |

# Failure Modes

- Backup exists but restore has never been tested at production data volume → restore at incident time exceeds RTO by an order of magnitude.
- RPO/RTO assumed by engineering but never approved by business owner; mismatch surfaces during incident.
- Database is restored without object storage, search index, encryption keys, message-broker offsets, or compatible application version → "restored" system does not work.
- Destructive migration relies on rollback that cannot reconstruct truly lost rows (rollback ≠ undelete after commit).
- Backup access is too broad; backup deletion not audited or MFA-protected → ransomware deletes both production and backups.
- Encryption keys for old backups rotated/destroyed → backups become permanently unreadable.
- Backups all live in the same account/region as production → single-blast-radius destruction.
- Source corruption silently replicates into backups for weeks; no logical-consistency check catches it.
- Cross-region failover depends on DNS with long TTL; RTO of "5 minutes" is in fact "TTL + warmup + verification".
- "Soft delete" implementation makes restore from backup violate active rows' uniqueness constraints.
- Drill performed against an empty schema; restore process untested against realistic data shape.
- Backup retention silently shortened to save cost; compliance retention violated.
- Schema migration that drops a column → backups from before migration cannot be restored to current app version.
- Restore runbook in a wiki the on-call cannot access during incident.

# Output Contract

Return a backup-and-recovery plan with:

- `protected_dataset` (per dataset: name, owner, classification, storage system, regulatory class)
- `business_impact_analysis` (per dataset: financial/legal/operational impact of loss; references BIA)
- `rpo` / `rto` (per dataset: numeric target + approver name + last-tested actual)
- `failure_scenarios_covered` (matrix vs hardware/software/operator/malicious/region/ransomware/key-loss)
- `backup_strategy` (full/incremental/differential/CDC/snapshot/PITR; cadence; chain depth)
- `storage_topology` (locations, 3-2-1[-1-0] compliance, immutable/WORM where, cross-account/cross-region/cross-cloud)
- `encryption` (algorithm, key custody location separate from data, key rotation + retention policy compatible with backup retention)
- `retention_policy` (per regulatory and operational windows; deletion controls)
- `access_controls` (least-privilege roles; MFA delete; audit on deletion API)
- `restore_scope` (atomic set: DB + objects + index + keys + config + broker state + compatible app version)
- `restore_runbook` (step-by-step, executable by on-call without other docs; pre-checks; validation steps; rollback)
- `validation_plan` (row count / checksum / sample query / canary traffic acceptance)
- `drill_schedule` and `last_drill_results` (RTO actual, RPO actual, gaps, follow-ups)
- `monitoring_and_alerts` (backup job success, schedule miss, size anomaly, restore latency drift, deletion API)
- `cost_model` (per-tier storage + egress + drill cost)
- `rollback_relationship` (how this plan interacts with `release-rollback` and `data-migration-design`)
- `residual_risks` (data loss windows still possible; ransomware exposure; compliance gaps)

# Quality Gate

The plan passes only when:

1. RPO and RTO are **named per dataset, approved by business owner, and within demonstrated capability** (actual drill ≤ target).
2. A restore drill has been completed within the cadence policy (and recently for any system under schema change).
3. Restore scope is atomic — DB + objects + keys + index + config + compatible app version — not just "the database".
4. Backups are encrypted with keys held separately from the backup storage; key custody outlives backup retention.
5. Off-site / off-account / immutable copy exists for ransomware-credible systems.
6. Backup-deletion controls require MFA / cross-account separation; deletion is audited.
7. Failure-mode matrix is filled with concrete defenses for each cell (not "trust IAM").
8. Drill measured actual RTO/RPO; gaps are tracked.
9. Runbook is executable by an on-call who has never restored this system before.
10. Compliance retention obligations met; erasure obligations addressed (crypto-shred or rewrite plan).
11. Monitoring alerts cover job failure, schedule miss, size anomaly, deletion attempt.
12. Cost model is sustainable for the chosen tier.

# Used By

- reliability-observability-gate
- delivery-release-gate

# Handoff

Hand off to `data-migration-design` for safe destructive change sequencing; `release-rollback` for application rollback coordination; `observability` and `reliability-observability-gate` for detection and SLO/SLA alignment; `secret-configuration-security` for key custody, rotation, and KMS access; `threat-modeling` for ransomware and insider-threat scenario coverage; `delivery-release-gate` for pre-release snapshot + post-release verification.

# Completion Criteria

The capability is complete when **core data has tested recovery to a defined point within a defined time, with named owner, atomic restore scope, immutable off-site copy for ransomware resilience, separately-custodied keys, executable runbook, recent drill evidence, and monitoring on backup integrity itself** — and when the business owner can credibly say what loss they have accepted and what loss they are protected from.
