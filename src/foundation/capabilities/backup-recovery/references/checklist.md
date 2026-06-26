# Backup Recovery Checklist

- Select the mode: core dataset recovery, destructive change safety, ransomware/insider resilience, key/config/schema restore, DR/failover readiness, or compliance retention and erasure.
- Identify protected data, metadata, files, indexes, caches that became canonical, queues/offsets, keys, secrets, configuration, feature flags, and compatible application version.
- Record source evidence: backup config, runbook, restore drill, storage topology, KMS/key policy, retention policy, alerts, repository graph, project memory, and validation freshness.
- Accept, reject, or mark not verified every reused graph/memory/trajectory claim about backup existence, restore tests, RTO/RPO, keys, topology, or runbook status.
- Define failure scenarios, backup source, cadence, retention, encryption, access controls, deletion controls, and immutable/off-account copies.
- State RPO, RTO, restore target, business owner approval, last-tested actual, escalation path, and gap owner.
- Validate restore before relying on backup for release safety, destructive operations, ransomware resilience, or compliance evidence.
- Check atomic restore scope and application compatibility after restore, including objects, indexes, keys, config, broker state, and app/schema version.
- Document irreversible operations, point of no return, pre-operation snapshot, dry-run count, owner signoff, residual risk, and compensating recovery options.
- Map datasets, backup copies, keys, dependencies, drills, monitors, retention rules, and destructive-change gates to validation evidence or named residual risk.
- Name handoff boundaries, evidence limits, rollback relationship, and next owner before completion.
