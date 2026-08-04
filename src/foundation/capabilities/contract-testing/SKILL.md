---
name: contract-testing
description: "`analysis-agent`/`task-agent`/`review-agent`: use for provider-consumer compatibility of APIs, events, schemas, or behavior; skip without independent consumer/version risk."
---

# contract-testing

## Registry Trigger

**Use when**

- prove provider-consumer compatibility for an API, event, schema, generated client, or captured external behavior

**Do not use when**

- the change has no independent consumer expectation, compatibility transition, or retained-message/replay risk

## Skill Role

Prove executable compatibility on named provider-consumer surfaces. Exclude broad consumer discovery, contract design, and release verdicts.

## High-Value Rules

- Name the provider, known and unknown consumer classes, authoritative or observed contract source, versions that may coexist, and compatibility direction. A provider self-test does not establish consumer admissibility.
- Contract the semantics consumers branch on: absent versus null, defaults, error and authorization shapes, unknown fields or enum values, ordering, pagination, and duplicate or replay behavior. Avoid copying provider internals into expectations.
- Prove both sides of the boundary: provider verification shows named expectations can be served; consumer or generated-client evidence shows named consumers can accept them. Unrepresented consumer classes remain explicit proof limits.
- Classify compatibility with the actual protocol, reader/writer rules, retention window, and rollout order. Neither an additive change nor a schema-tool pass is universally safe.
- Treat registries, brokers, generated clients, diffs, and vendor fixtures as scoped evidence. Record the selected subject/version/environment or capture provenance, plus behavior and consumers they do not prove.
- Exercise old/new producer-consumer combinations and retained or replayed payloads when versions coexist. Preserve field identifiers, unknown-value behavior, and migration semantics required by the selected protocol.
- Re-run affected checks after contract, fixture, generator, compatibility-policy, or consumer-selection changes. Redact captured credentials and tenant data, and disclose unavailable consumers or environments.

## Anti-Patterns

- Declaring compatibility from schema shape alone while semantic meaning, error behavior, or consumer tolerance changed.
- Inventing a vendor or consumer mock from memory, or treating one captured response as the provider's complete behavior.
- Applying one broker, registry mode, versioning style, or consumer-driven workflow to every boundary.
- Replacing integration, journey, consumer discovery, or rollout proof with contract tests.

## Stop Conditions

- Escalate when unknown or independently deployed consumers, retained messages, undocumented provider behavior, or an unavailable compatibility environment prevent a bounded claim and no owner accepts the residual risk.

## Output Contract

- provider-consumer compatibility decision with covered versions, semantic expectations, executable proof, freshness, and explicit non-proof boundaries

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Compatibility direction protocol mixed versions retained payloads generated clients or external behavior leave proof choices open | One named provider consumer surface and its compatibility rule resolve the decision | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Several semantic version consumer fixture replay or rollout decisions must close together | No provider consumer expectation or compatibility behavior changes | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Provider consumer mixed-version fixture broker registry or generated-client claims need fresh scoped proof | Fresh named-provider and named-consumer results close the bounded compatibility claim | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
