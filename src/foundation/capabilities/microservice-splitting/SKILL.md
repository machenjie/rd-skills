---
name: microservice-splitting
description: "`analysis-agent`/`task-agent`/`review-agent`: use when a service split affects ownership, deployment, scaling, isolation, contracts, or data; skip without a split decision."
---

# microservice-splitting

## Registry Trigger

**Use when**

- evaluate service split boundaries ownership deployment data and operational cost

**Do not use when**

- no task-local microservice splitting decision is required

## Skill Role

Approve, reject, or defer a service split from business/data ownership, contract stability, failure isolation, deployability, rollback, and operating capacity. Own the integrated decision and transition exit criteria while named specialists retain their mechanisms. Require coupling reduction to exceed distributed-system cost.

## High-Value Rules

- Shared databases, shared schemas, cross-service foreign keys, or direct table reads block independent deployability until data ownership is separated or mediated through contracts/events.
- Extract only behind a versioned API, gRPC, or event contract that excludes ORM and domain internals.
- An independently deployed service names accountable service, release, and incident owners before production. Accepted service levels, failure modes, or platform policy determine its SLO, alert, dashboard, runbook, capacity, and escalation artifacts.
- Transaction boundaries must be redesigned explicitly with Saga, transactional outbox/inbox, compensation, reconciliation, or a documented decision to keep the boundary in-process.
- A new synchronous call defines timeout, failure, cancellation, and observability behavior; add retry, circuit breaking, bulkheads, or degradation only when dependency criticality, overload, and failure tests justify them.
- Approve a split only when current evidence rejects viable in-process alternatives.
- Integrate accepted outputs from `module-boundary-design`, `data-api-contract-changer`, `transaction-consistency`, `reliability-observability-gate`, `security-privacy-gate`, and `delivery-release-gate`, with each specialist retaining its mechanism.
- Define a reviewable transition covering current/target authority, phases, old/new reads, writes, traffic, mixed-version proof, rollback/forward-fix triggers, retirement, per-phase validation, observable exit conditions, evidence links, proof limits, and residual owners.

## Anti-Patterns

- Assume strangler migration or parallel run proves split safety or guarantees rollback to the in-process path.
- Expose ORM or domain models as external API DTOs or event schemas.
- Treat Saga compensation as database undo instead of an explicit refund, release, cancel, or reconcile action.
- Ignore the added pipeline, telemetry, configuration, capacity, security, and on-call cost when judging a split.
- Treat merging a service as failure when independent deployment never materialized or operating cost exceeds isolation value.

## Stop Conditions

Escalate splits crossing financial, entitlement, inventory, identity, regulated-data, critical synchronous, migration/dual-write, public-contract, rollback, ownership, or on-call boundaries. Route production splits through release, reliability, security, and data gates.

## Output Contract

- service split decision to approve, reject, or defer with business and runtime boundaries; code, data, contract, release, and incident ownership; source-of-truth and consistency authority; and dependency and contract transitions. The decision includes phased migration, mixed-version behavior, rollback, retirement, and exit conditions; failure-isolation and operability readiness; validation evidence and proof limits; rejection/defer reasons; and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | ownership scaling consistency or deployment forces leave extraction options viable | modular-monolith repair satisfies every material split force | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | extraction changes data ownership contracts transactions operations or release independence | no independently deployed service boundary is proposed | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | split independence compatibility or operability claims need current proof | current topology contracts owners and validation prove each claim | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
