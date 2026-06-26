# Backup Recovery Benchmarks And Patterns

Use this reference when `backup-recovery` needs detailed RTO/RPO tiers, backup-type selection, DR strategy, ransomware controls, failure-mode coverage, graph/memory/execution coupling, or validation matrices beyond the inline `SKILL.md`.

## Benchmark Anchors

| Benchmark | Recovery implication | Evidence to require |
| --- | --- | --- |
| ISO/IEC 27031 and ISO 22301 | Business continuity requires impact analysis, objectives, plans, exercises, and continual improvement. | Business owner, BIA, test cadence, gap remediation. |
| NIST SP 800-34 | Contingency planning links BIA, recovery strategy, plan testing, and maintenance. | RTO/RPO target, contingency plan, exercise result. |
| NIST SP 800-209 | Storage security includes isolation, access control, encryption, logging, and resilience. | Storage topology, key custody, deletion audit. |
| NIST SP 800-184 and CISA ransomware guidance | Cyber recovery assumes attackers may target backups. | Immutable/off-account copy, MFA delete, compromised-credential scenario. |
| AWS Well-Architected REL09/REL13 | Backup and DR strategy are reliability pillars, validated by testing. | Backup cadence, restore drill, DR topology, failover test. |
| Google SRE data integrity practice | Data loss prevention needs layered defenses and restore verification. | Failure-mode matrix, consistency checks, restore validation. |
| PCI/HIPAA/SOC 2/GDPR/DORA | Regulated systems need restoration, retention, resilience, and timely availability evidence. | Regulatory class, retention, restore proof, evidence owner. |
| 3-2-1-1-0 | Ransomware-resilient backups need copies, media/location diversity, immutability, and verified zero errors. | Copy count, off-site/off-account, immutable retention, verification status. |

## RPO/RTO Tier Reference

| Tier | Example workload | RPO target | RTO target | Typical strategy |
| --- | --- | --- | --- | --- |
| 0 mission-critical | Payment authorization, life-safety, trading execution | Near zero | < 1 min | Multi-region active-active, sync replication, automated failover. |
| 1 business-critical | Customer-facing transactional database | <= 5 min | <= 1 hr | Warm standby, cross-region replication, continuous WAL/oplog shipping. |
| 2 important | Internal SaaS, operational reporting | <= 1 hr | <= 4 hr | Hourly backups, pilot-light DR, tested runbook. |
| 3 standard | Analytics, dev/test, noncritical workflow state | <= 24 hr | <= 24 hr | Daily snapshot, backup-and-restore. |
| 4 archive | Compliance archive, audit trail, legal hold | <= 7 days | Days | Cold storage, immutable retention, retrieval runbook. |

RPO/RTO must be approved per dataset by the business owner. A service SLO does not automatically define acceptable data loss.

## Backup Type Selection Matrix

| Backup type | Recovery point granularity | Restore complexity | Pick when | Risk to control |
| --- | --- | --- | --- | --- |
| Full | Per snapshot | Simple | Small datasets or periodic baseline for chains. | Storage cost and long snapshot windows. |
| Incremental | Last full plus chain | Higher | Large datasets with frequent backups. | Chain corruption or missing segment. |
| Differential | Last full plus latest diff | Medium | Balance full restore speed and storage cost. | Diff growth over time. |
| Continuous WAL/oplog/CDC | Seconds/transactions | Higher | RPO measured in minutes or less. | Replay tooling and point-in-time target accuracy. |
| Storage snapshot | Per snapshot | Fast in same platform | Fast same-region restore. | Not a substitute for off-site/off-account backup. |
| Logical export | Per export | Slow but portable | Cross-version restore and migration safety net. | Restore time at TB scale. |
| Object versioning + MFA delete | Per object version | Per-object | Object storage accidental deletion. | Lifecycle rules and cost. |
| Immutable/WORM backup | Per backup | Base restore complexity | Ransomware/compliance resilience. | Retention lock errors and recovery permissions. |

## DR Strategy Selection

| Strategy | RTO | RPO | Cost | Pick when | Validation |
| --- | --- | --- | --- | --- | --- |
| Backup and restore | Hours to days | Hours | Low | Standard apps tolerate downtime. | Restore drill from off-site copy. |
| Pilot light | Tens of minutes | Minutes to hours | Medium | Core services stay warm. | Scale-up and dependency restore drill. |
| Warm standby | Minutes | Seconds to minutes | High | Reduced capacity is always running. | Traffic failover drill and capacity test. |
| Multi-site active/active | Near zero | Near zero | Very high | Mission-critical and split-brain complexity accepted. | Failover/failback and data consistency drill. |

## Failure-Mode Coverage Matrix

Recovery design must defend against intersecting loss type and loss source. Fill each relevant cell with detection and restore path.

| Loss type / source | Hardware | Software bug | Operator error | Malicious insider | External attack | Region/account failure |
| --- | --- | --- | --- | --- | --- | --- |
| Single record | PITR or logical restore; audit lookup. | Versioned record or reconciliation. | Point lookup restore workflow. | Access audit plus immutable copy. | PITR before attack timestamp. | Cross-region copy. |
| Single table/index | Snapshot restore into side DB and selective copy. | Rebuild/index validation. | Pre-change snapshot and restore script. | Deletion audit and WORM. | Clean restore from pre-attack point. | Off-account copy. |
| Whole database | Replica, PITR, snapshot. | Restore to pre-bug point. | Full restore runbook. | Separate backup admin. | Immutable/off-account restore. | DR tier strategy. |
| Object storage | Versioning and lifecycle. | Derived object rebuild. | Object version restore. | MFA delete and object lock. | Immutable bucket. | Cross-region replication. |
| Encryption key | Key version retention. | Restore prior key metadata. | KMS backup/escrow process. | Separate key admin. | Compromise rotation and retained old keys. | Cross-region KMS strategy. |
| Backup itself | Copy verification. | Multi-version retention. | Deletion protection. | WORM/off-account. | Immutable copy. | Off-site/off-cloud copy. |

## Atomic Restore Scope Checklist

| Dependency | Why it matters | Evidence |
| --- | --- | --- |
| Primary database | Transactional source of truth. | Snapshot/PITR artifact and validation queries. |
| Object storage | Attachments, exports, media, invoices, blobs. | Versioning/replication and checksum/object count. |
| Search index/cache | Product may need rebuild or warmup before serving traffic. | Rebuild runbook, source-of-truth link, warmup time. |
| Message broker offsets | Restore can replay or skip side effects. | Offset checkpoint, idempotency/replay plan. |
| Encryption keys | Encrypted backups are unreadable without retained key versions. | KMS policy, key version retention, restore drill. |
| Config/secrets/feature flags | Restored app may not boot or may run wrong behavior. | Config/secrets backup, flag export, access path. |
| Application version | Current code may not read old schema/data. | Compatible version/tag and deployment artifact. |
| External dependencies | Webhooks/providers may need re-sync. | Provider recovery steps and contact/credential path. |

## Ransomware And Insider Control Matrix

| Control | Purpose | Evidence |
| --- | --- | --- |
| Off-account backup ownership | Production compromise cannot delete backup. | Account/project separation and role policy. |
| Immutable retention / object lock | Admin cannot alter/delete within lock period. | Compliance/governance lock setting and retention. |
| MFA delete or privileged approval | Prevent one credential from deleting recovery copy. | Delete policy and audit trail. |
| Separate key custody | Backup data and decryption key are not in same blast radius. | KMS/key vault policy and key restore test. |
| Deletion API alert | Detect attacker or operator deleting backups. | Alert rule, owner, runbook. |
| Backup size anomaly alert | Detect corruption, skipped datasets, or tampering. | Metric and threshold. |
| Restore from clean point | Choose timestamp before corruption/encryption. | PITR window and corruption detection signal. |

## Graph, Memory, And Execution Coupling

| Evidence source | How to use it | Failure to avoid |
| --- | --- | --- |
| Repository graph | Find data stores, object buckets, queues, indexes, KMS usage, config, runbooks, backup jobs, Terraform, and restore tests. | Database-only recovery plan when product state spans systems. |
| Project memory | Treat previous drills and RTO/RPO as leads, not proof. | Stale drill evidence after schema/data volume/key changes. |
| Execution trajectory | Reuse prior validation only when it covers the current backup artifact and data volume. | Claiming a unit test or empty restore proves production-scale recovery. |
| Telemetry | Check backup success, missed schedule, size, deletion attempt, restore duration, drill actuals. | No alert for silent backup failure. |
| Business context | RPO/RTO and retention are business risk decisions. | Engineering guessing acceptable loss. |

## Recovery-To-Validation Matrix

| Recovery decision | Preferred validation |
| --- | --- |
| RPO/RTO target | Business approval plus last drill actual within target. |
| Backup job cadence | Scheduled job status, missed-run alert, backup age query. |
| PITR | Restore to timestamp before synthetic corruption in test environment. |
| Object storage restore | Object count/checksum/version restore sample or full validation by tier. |
| KMS/key retention | Restore old backup using retained key version. |
| Immutable copy | Object lock/retention policy read plus deletion-denied test when safe. |
| Cross-region/off-account copy | Restore from the isolated copy, not only primary snapshot. |
| Atomic restore scope | Application can boot and serve canary flow after DB/object/key/config restore. |
| Destructive change preflight | Pre-change snapshot plus restore rehearsal or documented residual risk. |
| Retention/erasure | Policy-as-code, audit evidence, crypto-shred or backup rewrite plan. |
| Runbook usability | On-call tabletop or hands-on drill by someone outside primary author. |

## Review Checklist

1. Inventory every protected dataset and dependency.
2. Name owner, classification, BIA impact, RTO/RPO target, and last-tested actual.
3. Confirm backup type, cadence, retention, copy topology, and immutability.
4. Verify key custody, key retention, and restore with old key versions.
5. Verify off-site/off-account copy and deletion controls for ransomware-credible systems.
6. Define atomic restore scope, dependency order, and compatible app/config/schema version.
7. Validate restore with counts, checksums, application canary, and timing.
8. Define monitoring for job failure, missed schedule, size anomaly, deletion attempt, and restore latency drift.
9. Tie destructive operations to snapshot, approval, rollback/forward-fix, and post-change validation.
10. Record compliance retention, legal hold, erasure, and evidence owner.

## Anti-Pattern Review

| Anti-pattern | Review response |
| --- | --- |
| "Backups are enabled" | Ask for restore drill, RTO/RPO actuals, and validation output. |
| Database-only restore proof | Require object/index/key/config/app-version dependency map. |
| Same account can delete production and backup | Require off-account immutable copy or explicit residual risk owner. |
| RTO guessed from snapshot size | Require measured restore at representative volume. |
| Key rotated and old key destroyed | Block until key retention matches backup retention. |
| DR plan depends on DNS TTL longer than RTO | Adjust TTL/failover strategy or revise RTO. |
| Retention shortened to cut cost | Require business/compliance owner approval and updated evidence. |
| Restore runbook in inaccessible wiki | Require incident-accessible runbook copy and owner. |
