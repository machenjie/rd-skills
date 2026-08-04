---
name: consumer-impact-analysis
description: "`analysis-agent`/`task-agent`/`review-agent`: use when API, SDK, schema, event, package, CLI, or export changes may affect consumers; skip when no consumer contract can change."
---

# consumer-impact-analysis

## Registry Trigger

**Use when**

- consumer impact analysis API SDK schema event public export generated client mobile web backend consumer compatibility migration deprecation telemetry rollout rollback unknown consumer risk

**Do not use when**

- no task-local consumer impact analysis decision is required

## Skill Role

Establish known and unknown consumers of a changed contract, then select compatibility, migration, rollout, and validation from current evidence.

## High-Value Rules

- Inventory direct, generated, inferred, telemetry-observed, owner-confirmed, omitted, and unknown consumers before approving a consumer-visible change.
- Bound a no-consumer claim by inspected repositories, graphs, generated artifacts, exports, registries, documentation, telemetry, and explicit search gaps; local caller search alone is insufficient.
- When a consumer can still depend on old behavior, require a compatible bridge, version, coordinated migration, or no-ship decision derived from its release and retention boundary.
- Treat generated clients, SDKs, events, webhooks, and machine-readable CLI output as versioned consumers; verify regeneration, mapping, replay, and package or schema impact where triggered.
- Select deprecation and removal from current usage and owner evidence rather than a calendar alone, and record the evidence limits when telemetry is unavailable.
- Validate mixed producer and consumer states, rollback after new writes, and the behavior of retained data or messages when the rollout can create version skew.

## Anti-Patterns

- A provider-only green test does not prove downstream compatibility.
- A public export, package, stream, webhook, or copied example can have consumers outside repository search scope.
- Calendar expiry without usage or owner evidence can remove a still-live contract.
- Generated output treated as incidental hides source-schema and compatibility drift.

## Stop Conditions

Escalate to the relevant contract owner when API, schema, event, package, or generated-client compatibility changes. Escalate to `delivery-release-gate` for coordinated rollout, publication, or removal. Escalate to `security-privacy-gate` for changed sensitive fields or tenant scope. Escalate to `quality-test-gate` when current consumer proof is missing. State unknown external-consumer risk rather than inferring absence.

## Output Contract

- Return a Consumer Impact Report: changed contracts, consumers, compatibility, migration, deprecation, telemetry, rollout, rollback, tests, docs, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Compatibility, migration, telemetry, or mixed-version strategies compete | The private surface has no external or generated consumers | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Consumer impact spans SDKs, events, mobile clients, or unknown callers | No observable contract or public export changes | task-agent, analysis-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Compatibility claims require fresh consumer, telemetry, or generated-artifact proof | No consumer-readiness claim is being approved | task-agent, analysis-agent, review-agent | evidence-record, proof-limit, residual-risk |
