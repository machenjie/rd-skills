# Consumer Impact Evidence Patterns

Use this reference when closure depends on repository inspection, prior task evidence, observable action sequence, telemetry freshness, generated artifact freshness, validation freshness, or evidence limits.

## Evidence Map

- Consumer evidence inventories provider surfaces, generated clients, docs/examples, jobs, dashboards, topics, configuration, packages, and external owner classes affected by the change.
- Compatibility proof names each covered consumer class and a command that can fail after final source, generated, fixture, and documentation edits; provider-only tests are insufficient.
- Removal telemetry states metric source, dimensions, observation window, lag allowance, and owner acceptance for consumer classes that cannot be directly validated.

## Freshness Rules

- Re-run or disclose stale validation when contract source, generated clients, docs/examples, fixtures, registry metadata, package exports, telemetry query, or rollout plan changes after a command.
- Treat repository inspection and prior task evidence as selectors until current source and generated artifacts are read.
- When a schema, API, or export diff supports a compatibility or release claim, treat it as structural evidence and separately prove the relevant semantic, default, error, timing, telemetry, and rollback behavior.
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
- repository inspection proves known edges only when generated from current source; it does not prove telemetry-observed external consumers.
- prior task evidence proves prior decisions existed; it does not prove the current contract, generated artifacts, or consumers are unchanged.
- Contract tests cover named interactions. Unmodeled consumers and semantics outside fixtures remain unproven.
- Generated-client compile proves source/binary compatibility for that client version; it does not prove mobile/partner adoption.
- Telemetry proves observed usage within the selected window and dimensions; it does not prove uninstrumented consumers are absent.
- Choose additive, bridge, version, upcaster, feature-flag, dual-write, configuration-bridge, no-ship, or residual-risk handling from the classified consumer surface.
