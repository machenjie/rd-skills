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

# Stage Fit

Use during planning, implementation review, code-review, testing, release preparation, incident-readiness review, and destructive-change approval when core data or critical state could be lost, corrupted, encrypted by an attacker, made unreadable by key/config changes, or restored outside the business RTO/RPO. In planning, define protected datasets, blast radius, recovery scope, RTO/RPO, restore evidence, and ownership before relying on backup as a control. In review, reject stale project-memory or repository-graph claims such as "backups exist", "restore was tested", "RTO is 1 hour", or "keys are retained" unless current backup configuration, runbooks, drill evidence, telemetry, and validation prove them. Hand off when the primary question is migration sequencing, application rollback, observability signals, key custody, ransomware threat model, or release clearance.

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
- **Closure evidence** names the restore command or drill, validator, artifact/report path, exit code or explicit manual result, timestamp, data scope, and owner; stale validation cannot close a backup-recovery gate.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Core dataset recovery | Database, object store, search index, durable queue, vector store, audit log, or canonical cache can be lost/corrupted. | Dataset owner, classification, RPO/RTO, backup cadence, restore validation. | Dataset inventory, business owner approval, last drill actuals, restore scope. | `reliability-observability-gate`, `observability` | Code rollback only. |
| Destructive change safety | DROP, DELETE, purge, archive, rekey, reindex, region decommission, or irreversible migration. | Pre-change snapshot, point-of-no-return, approval, tested restore, forward-fix relationship. | Dry-run count, backup snapshot, restore test, owner signoff, rollback tier. | `data-migration-design`, `release-rollback`, `delivery-release-gate` | Backup as migration plan. |
| Ransomware/insider resilience | Internet-exposed, regulated, high-value, tenant-wide, backup deletion, or credential compromise threat. | Immutable/off-account backups, deletion controls, key separation, restore under compromise. | WORM/object lock, MFA delete, separate backup admin, deletion audit. | `security-privacy-gate`, `threat-modeling`, `secret-configuration-security` | Same-account snapshots only. |
| Key/config/schema restore | Encryption key rotation, KMS migration, config repository, app version, schema version, or feature flag affects restore readability. | Atomic restore scope and compatibility window. | Key retention, config/secrets backup, compatible app version, schema rollback/bridge. | `secret-configuration-security`, `version-compatibility`, `data-migration-design` | Database-only restore proof. |
| DR/failover readiness | Region/account/cloud failure, DR tier change, standby/cross-region replication, DNS/traffic failover. | DR strategy, failover path, actual RTO/RPO, dependency restore order. | DR topology, failover drill, DNS TTL, dependency map, cost/capacity. | `delivery-release-gate`, `reliability-observability-gate`, `kubernetes-gateway` | Snapshot-only proof. |
| Compliance retention and erasure | Legal hold, audit trail, GDPR/CCPA erasure, PCI/HIPAA/SOX retention, e-discovery, archive lifecycle. | Retention correctness, deletion beyond retention, erasure in backups, evidence owner. | Regulatory class, retention window, crypto-shred/rewrite plan, audit evidence. | `security-privacy-gate`, `change-documentation-gate` | Cost-only retention change. |

# Industry Benchmarks

Anchor against ISO/IEC 27031, ISO 22301, NIST SP 800-34, NIST SP 800-209, NIST SP 800-184, ITIL Service Continuity, AWS Well-Architected Reliability REL09/REL13, Google SRE data integrity practice, DORA operational resilience, PCI-DSS/HIPAA/SOC 2/GDPR recovery obligations, CISA ransomware guidance, 3-2-1-1-0 backup practice, WORM/immutable storage, PITR, and DR strategy tiers from backup-and-restore through active/active. Keep this body focused on routing, ownership, evidence, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed tier, backup-type, DR, failure-mode, graph/memory/trajectory, and validation matrices.

# Selection Rules

Select this capability when **recovery from data loss or corruption** is primary. Adjacent routing:

- Prefer `data-migration-design` when the question is the migration sequence and rollback strategy itself.
- Prefer `release-rollback` when the question is reverting application code, not data.
- Prefer `observability` when the question is detection of corruption or loss.
- Prefer `secret-configuration-security` for key custody and rotation lifecycle.
- Prefer `reliability-observability-gate` for SLO/SLA and DR readiness review.
- Use **with** `delivery-release-gate` when a release demands a pre-deploy snapshot or DR exercise.

# Proactive Professional Triggers

- **Signal:** A destructive migration, purge, rekey, reindex, archive, or region/key decommission relies on "we have backups" without a fresh restore drill. **Hidden risk:** the recovery path fails or exceeds RTO after data is already lost. **Required professional action:** require pre-operation snapshot, restore proof, owner signoff, and rollback/forward-fix relationship. **Route to:** `data-migration-design`, `release-rollback`, `delivery-release-gate`. **Evidence required:** dry-run count, backup artifact, restore validation, RTO/RPO actuals.
- **Signal:** Backup scope names only the database while product correctness depends on object storage, indexes, queues, offsets, keys, config, flags, or app version. **Hidden risk:** "restored" system cannot serve users. **Required professional action:** define atomic restore scope and dependency order. **Route to:** `observability`, `secret-configuration-security`, `version-compatibility`. **Evidence required:** dependency map, compatible app/schema/key set, validation query/canary.
- **Signal:** Backups, deletion rights, and encryption keys share one account, role, region, vault, or admin credential. **Hidden risk:** ransomware/insider compromise destroys production and recovery copy together. **Required professional action:** require off-account/off-site immutable backup and separated key custody. **Route to:** `security-privacy-gate`, `threat-modeling`, `secret-configuration-security`. **Evidence required:** object lock/WORM, MFA delete, deletion audit, key-retention policy.
- **Signal:** RTO/RPO is inherited from an SLO, guessed by engineering, or not measured at production-like scale. **Hidden risk:** business assumes a recovery level the system cannot meet. **Required professional action:** require business owner approval and drill actuals. **Route to:** `reliability-observability-gate`, `observability`. **Evidence required:** BIA owner, target, last drill, gap owner.
- **Signal:** Compliance retention, legal hold, audit logs, or erasure obligations are affected by backup retention or restore. **Hidden risk:** audit failure, over-retention, under-retention, or impossible erasure. **Required professional action:** classify retention and erasure behavior before changing backup policy. **Route to:** `security-privacy-gate`, `change-documentation-gate`. **Evidence required:** regulatory class, retention window, deletion/crypto-shred plan, evidence owner.
- **Signal:** Project memory, repository graph, runbook, or prior execution says restore was already tested. **Hidden risk:** stale drill evidence survives after schema, size, key, region, dependency, or runbook changes. **Required professional action:** confirm current configuration, restore artifact, data volume, runbook, and validation freshness. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected memory, freshness limit, validation command or residual risk.

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
- **Validation artifact quality.** A restore drill report, validator output, screenshot, or ticket is useful only when it identifies the backup artifact, command/runbook step, exit code or manual pass/fail result, dataset size, dependency scope, evidence owner, and freshness after the last schema, key, config, region, or volume change.
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

- **Stale validation closure**: a prior drill report or successful command is reused after schema, key, config, data volume, dependency, or region changes; evidence no longer covers the recovery risk.
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

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 backup and recovery routing, evidence, output, and gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete recovery plan, destructive-change approval, backup policy change, restore drill, RTO/RPO claim, retention decision, or release preflight. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when detailed benchmark anchors, RTO/RPO tiers, backup-type choice, DR strategy, failure-mode coverage, ransomware controls, graph/memory/trajectory coupling, or validation matrices are needed. Use [examples/example-output.md](examples/example-output.md) only when output shape is unclear. Do not load references for pure routing or minor wording where the inline output contract and quality gate are enough.

# Output Contract

Return a backup-and-recovery plan with:

- `mode_selected` (core dataset recovery / destructive change safety / ransomware-insider resilience / key-config-schema restore / DR-failover readiness / compliance retention and erasure)
- `source_evidence` (backup config, runbook, restore drill, storage topology, KMS/key policy, retention policy, monitoring, repository graph, project memory, execution trajectory, and validation freshness inspected)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for each reused backup, restore, RTO/RPO, runbook, topology, key-retention, or drill claim)
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
- `validation_commands` (restore or drill command, validator name, artifact/report path, exit code or manual result, timestamp, dataset size, and freshness verdict)
- `drill_schedule` and `last_drill_results` (RTO actual, RPO actual, gaps, follow-ups)
- `monitoring_and_alerts` (backup job success, schedule miss, size anomaly, restore latency drift, deletion API)
- `cost_model` (per-tier storage + egress + drill cost)
- `rollback_relationship` (how this plan interacts with `release-rollback` and `data-migration-design`)
- `changed_recovery_to_validation_map` (each dataset, backup copy, key, restore dependency, drill, monitor, retention rule, and destructive-change gate mapped to validator/test/drill/manual evidence or residual risk)
- `handoff_boundaries` (what belongs to migration sequencing, application rollback, observability signal design, key custody, threat modeling, release gate, compliance docs, or no-next-gate rationale)
- `residual_risks` (data loss windows still possible; ransomware exposure; compliance gaps)
- `evidence_limits` (what was not inspected or not proven: production-scale restore, cross-region copy, key restore, object attachments, search rebuild, queue offset replay, legal hold/erasure, or live failover)

# Evidence Contract

Close a backup-recovery plan only when it names selected mode, boundaries inspected, current source evidence, graph/memory/trajectory reuse judgment, protected datasets, business owner, RTO/RPO target and actual drill result, atomic restore scope, storage topology, key custody, retention/erasure obligations, access/deletion controls, monitoring, runbook validation, changed-recovery-to-validation map, handoff boundaries, residual risk, and evidence limits.

Validation evidence must name each command, validator, artifact/report path, exit code or manual result, data scope, owner, and freshness after the final material source/config/key/schema change. State what evidence proves, what evidence does not prove, the reuse and placement rationale for graph/memory/trajectory claims, behavior preservation for existing backup and restore controls, and the next gate or handoff owner. "Backups are enabled" or "restore from snapshot" is not sufficient evidence.

# Benchmark Coverage

Improved recovery plans reject common weak patterns: backup existence without restore proof, database-only restore scope, same-account backup deletion rights, keys lost before backup retention expires, unmeasured RTO/RPO, empty-schema drills, backup retention shortened by cost only, PITR not matched to corruption detection, ransomware without immutable copy, and stale memory claims about drills. Detailed tier and failure-mode matrices belong in references so the body stays efficient.

# Routing Coverage

Route here when recovery from data loss, corruption, ransomware, key loss, restore scope, RTO/RPO, DR/failover proof, retention, erasure, or backup integrity is primary. Hand off when the primary work is migration sequencing (`data-migration-design`), code/config rollback (`release-rollback`), observability signal design (`observability` / `reliability-observability-gate`), key custody (`secret-configuration-security`), threat modeling (`threat-modeling`), release clearance (`delivery-release-gate`), or compliance documentation (`change-documentation-gate`).

# Quality Gate

The plan passes only when:

1. Selected mode, current source evidence, and graph/memory/trajectory reuse judgment are explicit.
2. RPO and RTO are **named per dataset, approved by business owner, and within demonstrated capability** (actual drill ≤ target).
3. A restore drill has been completed within cadence policy and recently for any system under schema/key/config change.
4. Restore scope is atomic — DB + objects + keys + index + config + broker/offset state + compatible app version — not just "the database".
5. Backups are encrypted with keys held separately from backup storage; key custody outlives backup retention.
6. Off-site/off-account/immutable copy exists for ransomware-credible systems.
7. Backup-deletion controls require MFA/cross-account separation; deletion is audited and alerted.
8. Failure-mode matrix has concrete detection and restore paths for likely data-loss sources, including backup/key loss.
9. Drill measured actual RTO/RPO; gaps have owners and dates.
10. Runbook is executable by an on-call who has never restored this system before and is accessible during an incident.
11. Compliance retention obligations are met; erasure obligations have crypto-shred or rewrite plan.
12. Monitoring alerts cover job failure, schedule miss, size anomaly, restore latency drift, and deletion attempts.
13. Cost model is sustainable for the chosen tier without silently weakening retention or immutability.
14. Every dataset, backup copy, key, restore dependency, drill, monitor, retention rule, and destructive-change gate maps to validation evidence or named residual risk.
15. Validation commands, validators, artifacts/reports, exit code or manual result, owner, and freshness are recorded for each accepted restore or drill claim.
16. Handoff boundaries and evidence limits are explicit so recovery evidence is not over-claimed as migration safety, release rollback readiness, key-custody approval, or compliance signoff.

# Used By

- reliability-observability-gate
- delivery-release-gate

# Handoff

Hand off to `data-migration-design` for safe destructive change sequencing; `release-rollback` for application rollback coordination; `observability` and `reliability-observability-gate` for detection and SLO/SLA alignment; `secret-configuration-security` for key custody, rotation, and KMS access; `threat-modeling` for ransomware and insider-threat scenario coverage; `delivery-release-gate` for pre-release snapshot + post-release verification.

# Completion Criteria

The capability is complete when **core data has tested recovery to a defined point within a defined time, with named owner, atomic restore scope, immutable off-site copy for ransomware resilience, separately-custodied keys, executable runbook, recent drill evidence, and monitoring on backup integrity itself** — and when the business owner can credibly say what loss they have accepted and what loss they are protected from.
