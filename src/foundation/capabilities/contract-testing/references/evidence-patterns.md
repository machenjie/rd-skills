# Contract Testing Evidence Patterns

Use this reference when contract-test closure depends on repository graph, project memory, execution trajectory, validation freshness, fixture freshness, broker or registry status, or tool permission boundaries.

## Evidence Map

| Evidence Type | Accept When | Reject When | Closure Wording |
| --- | --- | --- | --- |
| Contract source | OpenAPI, AsyncAPI, proto, GraphQL SDL, JSON Schema, SDK export, event schema, or webhook spec was read after the final edit | Only provider implementation or handwritten assertions were read | `current contract source inspected: ...` |
| Provider verification | Provider-side contract command ran against the actual provider or generated stub after final contract edit | Provider unit tests are used as consumer compatibility proof | `provider verification: command, exit code, surface` |
| Consumer verification | Pact, generated-client compile, fixture replay, registry check, or consumer test covers the named consumer class | Consumer list is assumed from memory, owner assertion, or local search alone | `consumer verification: consumer, proof, limit` |
| Repository graph | Graph covers specs, generated clients, docs/examples, tests, topics, packages, and provider/consumer paths | Graph covers only local call sites or predates moved/generated files | `graph accepted/rejected because ...` |
| Project memory | Prior contract decisions are reconciled with current source, generated artifacts, and command output | Memory is treated as proof that a contract still passes | `memory used as selector, verified by ...` |
| Execution trajectory | Command order shows generation, verification, repair, and rerun after final edits | Old contract, schema diff, or broker result is reused after source/fixture/generated changes | `trajectory freshness: ...` |
| Broker or registry | Pact Broker, PactFlow, schema registry, or equivalent result names selector, subject, mode, version, and outcome | Local-only verification is reported as deployment compatibility | `broker/registry status: ...` |
| Vendor fixture | Fixture names source, captured_at, vendor/spec version, redaction, and replay command | Fixture was written from memory or stale docs | `fixture freshness and redaction: ...` |

## Freshness Rules

- Re-run or disclose stale validation when contract source, generated client, pact, fixture, schema registry subject, broker selector, docs/example, or compatibility mode changes after a command.
- Treat graph, memory, and prior summaries as selectors until current contract files and validation output confirm them.
- Treat schema/API diff as structural evidence only; it does not prove behavior outside the described contract, unknown consumers, production traffic, or rollout safety.
- Treat `can-i-deploy` or schema registry checks as environment/version-specific; name selector, subject, environment, and unsupported version risk.
- Treat vendor sandbox captures as sensitive by default; redact tokens, customer identifiers, request signatures, and tenant data before committing fixtures.

## Contract Surface To Validation Map

Use this compact map in reports:

```yaml
contract_surface_to_validation_map:
  - changed_surface: ""
    consumer_class: known_direct | generated_client | event_consumer | webhook_partner | vendor | unknown
    compatibility_risk: structure | error_shape | null_optional | enum | pagination | ordering | version | fixture_drift
    proof: provider_verification | pact | generated_compile | schema_diff | registry_check | broker_check | fixture_replay | residual_risk
    command_or_artifact: ""
    proves: ""
    does_not_prove: ""
    freshness: fresh | stale | partial | not_run
    owner: ""
```

## What Evidence Proves

- Provider verification proves the provider can satisfy named expectations; it does not prove all consumers or production deploy compatibility.
- Consumer pacts prove named interactions; they do not replace schema design, integration behavior, or undocumented consumer discovery.
- Generated-client compile proves compatibility for that generated version; it does not prove mobile, partner, or package adoption.
- Schema registry checks prove the configured subject and mode; they do not prove semantic compatibility, ordering, or downstream processing behavior.
- Fixture replay proves the captured vendor or webhook example still maps correctly; it does not prove unrecorded vendor behavior.
- Repository graph and project memory prove discovery context only after current source and validation freshness are confirmed.
