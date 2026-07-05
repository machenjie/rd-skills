# Consumer Impact Evidence Patterns

Use this reference when closure depends on repository graph, project memory, execution trajectory, telemetry freshness, generated artifact freshness, validation freshness, or evidence limits.

## Evidence Map

| Evidence Type | Accept When | Reject When | Closure Wording |
| --- | --- | --- | --- |
| Source/spec/schema read | Contract files and changed generated artifacts were read after final edit | Only provider implementation was read | `current contract inspected: ...` |
| Repository graph | Graph covers providers, imports, generated clients, docs/examples, tests, jobs, dashboards, topics, configs, and packages | Graph covers only local call sites or predates moved files | `graph accepted/rejected because ...` |
| Project memory | Prior consumer decisions are reconciled with current source, telemetry, and owner evidence | Memory is treated as proof of no consumers | `memory used as hint, verified by ...` |
| Execution trajectory | Command order shows generation, validation, repair, and re-run after final edits | Old generated-client or contract check is reused after source change | `trajectory freshness: ...` |
| Telemetry | Metric source, window, dimensions, freshness, and zero/threshold decision are stated | Calendar date or docs notice is used as migration proof | `telemetry proves/does-not-prove: ...` |
| Validation command | Command can fail for the changed surface and ran after final source/generated/doc edits | Provider-only unit test is used for consumer compatibility | `command, exit code, consumer class covered` |
| Owner review | Owner covers a named consumer class and accepts explicit residual risk | Owner review has no surface, consumer class, or rollback scope | `owner review scope and limits: ...` |

## Freshness Rules

- Re-run or disclose stale validation when contract source, generated clients, docs/examples, fixtures, registry metadata, package exports, telemetry query, or rollout plan changes after a command.
- Treat repository graph and project memory as selectors until current source and generated artifacts are read.
- Treat schema/API/export diff as structural evidence only; it does not prove semantic, default, error, timing, telemetry, or rollback safety.
- Treat telemetry as removal evidence only when dimensions match the old/new surface and the window covers lagging consumers.
- Treat a successful provider build as insufficient for generated clients unless generated artifacts compile or downstream smoke passes.

## Changed Consumer To Validation Map

Use this compact map in reports:

```yaml
changed_consumer_to_validation_map:
  - changed_surface: ""
    consumer_class: known_direct | generated | mobile_partner_public | event_job_report | docs_examples | unknown
    compatibility_risk: structure | meaning | validation | defaults | error | timing_order | persistence_rollback
    proof: schema_diff | contract_test | generated_compile | fixture_replay | telemetry | owner_review | residual_risk
    command_or_artifact: ""
    proves: ""
    does_not_prove: ""
    freshness: fresh | stale | partial
    owner: ""
```

## What Evidence Proves

- Search output proves only searched paths and literal/detected references; it does not prove dynamic, external, package, dashboard, or documentation consumers.
- Repository graph proves known edges only when generated from current source; it does not prove telemetry-observed external consumers.
- Project memory proves prior decisions existed; it does not prove the current contract, generated artifacts, or consumers are unchanged.
- Contract tests prove named interactions; they do not prove unmodeled consumers or semantics outside fixtures.
- Generated-client compile proves source/binary compatibility for that client version; it does not prove mobile/partner adoption.
- Telemetry proves observed usage within the selected window and dimensions; it does not prove uninstrumented consumers are absent.

## Closure Template

```yaml
consumer_impact_evidence:
  mode: api_dto | sdk_package_export | event_webhook_schema | cli_config_output | unknown_consumer | deprecation_removal
  inspected:
    contract_surfaces: []
    consumer_classes: []
    graph_memory_trajectory: accepted | rejected | stale | not_used
  compatibility_decision: additive | bridge | version | upcaster | feature_flag | dual_write | config_bridge | no_ship | residual_risk
  validation:
    command_or_artifact: ""
    proves: ""
    does_not_prove: ""
    freshness: fresh | stale | partial
  rollout_rollback: ""
  residual_consumer_risk: ""
  next_gate: ""
```
