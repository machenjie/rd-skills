---
name: audit-evidence-integrity
description: "Use for audit coverage, identity/time fidelity, tamper evidence, retention, export, or custody decisions. Skip event emission, telemetry design, privacy purpose, and legal claims."
---

# audit-evidence-integrity

## Registry Trigger

**Use when**

- Protected actions or decisions need integrity-backed audit evidence.
- Completeness, integrity, ordering, retention, export, or custody behavior changes.

**Do not use when**

- Route implementation of audit emission/schema and stored evidence to `logging-design-gate`.
- Route analysis of audit trust, integrity, and custody to `security-privacy-gate`.
- Route telemetry to `observability` only for a separate telemetry decision.
- Route personal-data purpose and retention to `privacy-data-lifecycle`.
- Do not claim legal admissibility or regulatory compliance.

## Skill Role

Define post-emission audit trust, lifecycle, and verification contracts.

## High-Value Rules

- Define the audit question, critical outcomes and sources, expected records, time window, and completeness reconciliation.
- Preserve authoritative human/service identity, effective actor, delegation, session, tenant, purpose, and stable causation/correlation identities.
- Record occurrence, commit, and receipt time with source, offset, sync health, precision, uncertainty, and no unsupported global order.
- Preserve canonical records and schema versions while treating views and transformations as derived evidence with lineage.
- Separate administration from producers and subjects, protecting records, integrity metadata, keys, policy, validation configuration, and privileged-use evidence.
- Select one composition-specific verification contract and bind what sequences, checkpoints, signatures, hashes, storage controls, and reconciliation each cover. An isolated hash proves only its bound bytes and cannot by itself prove deletion, truncation, replay, or reordering.
- Enforce retention and hold policy across records, indexes, replicas, backups, exports, and verification material without legal conclusions.
- Bind access, export, and custody to selector, time range, schema, counts, integrity proof, actor, purpose, transfer, receipt, and verification.

## Anti-Patterns

- A critical event is missing without a coverage alarm.
- A mutable admin path alters protected evidence.
- Shared actor identity hides who acted.
- Clock skew is misrepresented as reliable order.
- Broken correlation severs cause from outcome.
- A retention gap silently removes evidence.
- Export transformation changes meaning or integrity.
- A custody gap leaves a handoff unverifiable.

## Execution Checklist

- Generate normal, denied, failed, delegated, administrative, and partial paths; reconcile expected records.
- Delete, alter, replay, duplicate, reorder, skew clocks, break correlation, and exercise privileged access.
- Verify exports across transformation/handoff; exercise retention, hold, expiry, and custody transitions.

## Stop Conditions

- Stop without an audit consumer, coverage owner, authoritative identity, bounded time claim, or an independent composition-specific integrity and gap check.
- Stop on unknown privileged bypass, silent lifecycle gap, unverifiable export/custody, or inaccessible verification material.
- Route legal admissibility and compliance conclusions to accountable owners.

## Output Contract

- audit-evidence decision with analysis or implementation owner, coverage, identity, time, causality, composition-specific integrity and gap detection, storage, access, lifecycle, export, custody, verification, limits, and owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [completeness identity and time](references/completeness-identity-and-time.md) | targeted | Coverage actor/service provenance time ordering correlation or causality remains unresolved | Emission schema alone is changing or current evidence closes coverage and attribution | analysis-agent, task-agent, review-agent | decision-record, boundary-decision, proof-limit |
| [tamper evidence storage and access](references/tamper-evidence-storage-and-access.md) | evidence-pattern | Immutable or tamper-evident storage verification gap detection or privileged access changes | No stored-evidence integrity or access boundary changes | analysis-agent, task-agent, review-agent | evidence-record, validation-plan, proof-limit |
| [retention export and chain of custody](references/retention-export-and-chain-of-custody.md) | targeted | Retention hold expiry export transformation transfer or custody changes | No audit lifecycle export or handoff decision changes | analysis-agent, task-agent, review-agent | boundary-decision, decision-record, residual-risk |
