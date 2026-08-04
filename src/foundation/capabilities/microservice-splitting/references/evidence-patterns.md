# Microservice Splitting Evidence Patterns

Use this reference when closure depends on current repository inspection, prior task evidence, observable action sequence, validation freshness, source-to-validation mapping, tool permission boundaries, or residual-risk wording. Keep it as an evidence map, not a second checklist.

## Split Claim-To-Evidence Map

| Split claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Split force is real | Business capability, owner, deploy cadence, scaling, compliance, fault-isolation, or cost force with current source/metric/owner evidence | The proposed boundary solves a named force | Future scale, all consumers, or production readiness is proven |
| In-process alternative is insufficient | Module-boundary option, public facade/import-rule option, rejected reason, graph coupling, and owner acceptance | A simpler local boundary was considered | Every modular repair path is impossible |
| Data ownership can separate | Entity/table/topic owner map, shared-table/FK/read-replica scan, migration pattern, source-of-truth owner, and no-shared-table decision | The split has a plausible data boundary | Backfill, reconciliation, or future reporting projections are safe |
| Contract boundary is ready | OpenAPI/proto/event schema, versioning policy, generated-client source, consumer inventory, compatibility check, and deprecation plan | Consumers can target a stable public contract | Unknown consumers or manual integrations are fully covered |
| Cross-service consistency is safe | Saga/outbox/inbox/reconciliation map, compensation owner, idempotency key, retry class, terminal failure, and failure-mode test | The named workflow has a consistency strategy | Every interleaving, replay, or operational recovery path is proven |
| Runtime call is reliable enough | Latency budget, timeout/retry/circuit values, fallback/degraded behavior, trace/span coverage, dependency SLO, and load/failure evidence | The inspected call has bounded failure behavior | Production traffic mix or provider behavior cannot violate the budget |
| Migration and rollback are credible | Strangler/parallel-run/branch-by-abstraction phases, traffic switch, mixed-version window, rollback trigger, forward-fix path, and retirement criteria | The extraction can proceed incrementally | Data rollback or business reversal is guaranteed |
| Operability is ready | Service owner, on-call, runbook, SLO, dashboard, alert, capacity/cost model, secrets/config owner, and incident escalation | The team can operate the service in the declared scope | Real incident response, future staffing, or cost drift is solved |

## Current Evidence And Freshness

- Treat prior ADRs, prior task evidence, diagrams, incident notes, and platform assumptions as leads until current source, deploy files, contracts, owners, and validation confirm them.
- Mark evidence stale after edits to module ownership, data schema, API/event contracts, generated clients, deploy pipelines, feature flags, migration scripts, test fixtures, observability config, or validation commands.
- Record inspected and skipped boundaries: modules, services, deploy units, data stores, contracts, consumers, transactions, queues/events, observability, ownership docs, release path, and generated artifacts.
- Map every approval, deferral, rejection, or merge recommendation to a source path, command/report, owner review, or explicit not-verified residual risk.

## Tool Permission Boundary

- Production traffic switches, dual writes, backfills, and service deployments require accepted ownership, staged proof, a stop signal, and rollback or forward-fix paths for both sides of the split.
- When database, queue, incident, telemetry, or cost evidence supports a candidate split, record its environment and observation window and qualify the conclusion with unobserved coupling or mixed-version behavior.

## Handoff Evidence Shape

```yaml
microservice_split_evidence_closure:
  decision_scope: ""
  inspected_boundaries: []
  accepted_prior_claims: []
  rejected_or_stale_claims: []
  split_decision_to_validation_map: []
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  what_remains_unproved: []
  residual_split_risk: []
  next_gate: ""
```

## Blocking Conditions

Block completion when the split relies only on code size, shared data ownership is unresolved, public contracts lack compatibility evidence, or cross-service consistency lacks recovery. Also block lockstep release, missing production ownership, stale prior evidence, and artifact-writing commands without write-scope and rollback disclosure.
