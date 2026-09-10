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

Define audit coverage, identity/time/causality, integrity/storage/access, lifecycle/export/custody, and verification.

## High-Value Rules

- Stop until question, consumer, outcomes, sources, time window, and owners are named.
- Load only the Reference for the active attribution, integrity, or lifecycle/custody decision.
- Return an evidence gap and residual risk for unresolved coverage, privileged bypass, composition, reconciliation, export, or custody.

## Anti-Patterns

- Local success substituted for evidence of the audit evidence integrity contract.

## Stop Conditions

- Stop without owners and current proof for coverage/attribution, integrity/bypass, and lifecycle/export/custody.
- Route legal admissibility and compliance conclusions to accountable owners.

## Output Contract

- audit-evidence decision with analysis or implementation owner, coverage, identity, time, causality, composition-specific integrity and gap detection, storage, access, lifecycle, export, custody, verification, limits, and owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [completeness identity and time](references/completeness-identity-and-time.md) | targeted | Coverage actor/service provenance time ordering correlation or causality remains unresolved | Emission schema alone is changing or current evidence closes coverage and attribution | analysis-agent, task-agent, review-agent | decision-record, boundary-decision, proof-limit |
| [tamper evidence storage and access](references/tamper-evidence-storage-and-access.md) | evidence-pattern | Immutable or tamper-evident storage verification gap detection or privileged access changes | No stored-evidence integrity or access boundary changes | analysis-agent, task-agent, review-agent | evidence-record, validation-plan, proof-limit |
| [retention export and chain of custody](references/retention-export-and-chain-of-custody.md) | targeted | Retention hold expiry export transformation transfer or custody changes | No audit lifecycle export or handoff decision changes | analysis-agent, task-agent, review-agent | boundary-decision, decision-record, residual-risk |
