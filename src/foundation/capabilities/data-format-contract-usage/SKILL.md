---
name: data-format-contract-usage
description: Use when JSON, YAML, XML, CSV, Protobuf, Avro, Parquet, OpenAPI schema, serialization, parser behavior, compatibility, coercion, field evolution, or wire-format contracts need professional evidence.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "134"
changeforge_version: 0.1.0
---

# Mission

Protect data format contracts across parsers, serializers, generated code, schema evolution, compatibility, and wire/storage behavior. Treat JSON/YAML/XML/TOML/CSV/Protobuf/Avro/Parquet changes as contracts only when their parser rules, compatibility class, examples, generated artifacts, and validation evidence are explicit.

# When To Use

Use when a change touches serialization/deserialization, JSON Schema, OpenAPI schema, YAML config, TOML config, XML, CSV/TSV, Protobuf, Avro, Thrift, Parquet, Arrow, CPE identifiers, schema registry, parser options, enum/field evolution, default/null/unknown field behavior, number/time encoding, generated models, content type, backward/forward compatibility, golden fixtures, or format migration.

# Do Not Use When

Do not use for a simple JSON literal inside a unit test, ordinary DTO field addition with no parser/compatibility risk, or application-level API design that does not depend on format semantics. Use `api-contract-design` or `dto-schema-design` when operation or field validation is primary and format compatibility is not the risk.

# Stage Fit

Use during planning, implementation, code-review, testing, release, migration, and incident-repair stages when parser behavior, schema evolution, generated models, fixtures, stored data, or wire/storage compatibility can change runtime meaning. Re-enter after schema, parser library/options, generator config, golden fixture, OpenAPI/JSON Schema/Protobuf/Avro/Parquet/YAML/XML/CSV/TOML/CPE, content type, compatibility mode, or stored-format migration edits. Skip for ordinary DTO work where the format parser, serializer, compatibility class, generated artifacts, fixtures, and old-data behavior are unchanged.

# Non-Negotiable Rules

- Name the format, schema authority, parser/serializer library, version, and options that define behavior.
- Classify compatibility: backward, forward, full, transitive, additive, breaking, or storage-only.
- Protobuf field numbers must never be reused; removed fields and enum values must be reserved.
- YAML scalar coercion must be controlled. Ambiguous booleans, numbers, dates, anchors, tags, and duplicate keys require parser policy and negative tests.
- YAML 1.1 vs. 1.2 scalar differences must be explicit for boolean-like values such as `yes`, `no`, `on`, and `off`.
- TOML type strictness must be preserved: strings, integers, floats, booleans, arrays, dates, and tables cannot be silently coerced across versions.
- JSON numbers, nulls, absent fields, unknown fields, ordering, duplicate keys, and timestamp formats require explicit behavior at boundaries.
- CSV requires delimiter, quote, escape, newline, encoding, header, null/empty, formula-injection, and column-order policy.
- XML requires namespace, entity expansion, external entity, schema validation, canonicalization, and size/depth limit policy.
- CPE identifiers require normalization, version matching, wildcard, edition/language/update handling, and vendor/product ambiguity checks.
- Schema registry or generated-code changes require source/generator/output policy and drift validation.
- Storage formats such as Avro/Parquet require reader/writer schema compatibility, partition evolution, nullable/default behavior, and backfill/read-old-data tests.
- Examples, golden fixtures, and parser differential tests must validate with the same parser settings as production.

# Industry Benchmarks

Anchor decisions against JSON Schema 2020-12, OpenAPI 3.1, YAML 1.1/1.2 behavior, TOML 1.0 type rules, XML security and canonicalization guidance against XXE/entity expansion, RFC 8259 JSON, RFC 4180 CSV baseline plus formula-injection controls, Protobuf field evolution rules, Confluent Schema Registry compatibility modes, Avro schema resolution, Parquet schema evolution guidance, CPE 2.3 naming/matching guidance, ISO 8601/RFC 3339 timestamps, and language-specific parser security guidance.

# Selection Rules

Select when parser behavior, serialization, schema evolution, generated artifacts, or format compatibility is the central risk. Pair with `api-contract-design` for client-visible API operations, `dto-schema-design` for field validation, `contract-testing` for consumer/provider fixtures, `data-migration-design` for stored data format migration, and `build-tool-professional-usage` for generated-code drift.

# Risk Escalation Rules

Escalate to `security-privacy-gate` for XML external entities, YAML unsafe loaders, CSV formula injection, deserialization gadgets, or untrusted parser inputs. Escalate to `data-api-contract-changer` when public or cross-service contracts evolve. Escalate to `data-middleware-change-builder` for storage formats, schema registry, streams, or warehouse files. Escalate to `delivery-release-gate` for incompatible format migrations or backfills.

# Proactive Professional Triggers

- **Signal:** A config, schema, fixture, or parser change is described as "just JSON/YAML/XML/CSV/TOML" without parser library, version, options, duplicate-key, coercion, null/default, or unknown-field policy. **Hidden risk:** parser defaults become runtime policy and can change permissions, routing, money, or rollout behavior. **Required professional action:** define the parser contract and add positive and negative fixtures for the risky states. **Route to:** `configuration-runtime-policy`, `input-validation`, `quality-test-gate`. **Evidence required:** parser version/options, risky scalar/key/null cases, fixture output, and what the fixture does not prove.
- **Signal:** Protobuf, Avro, Parquet, OpenAPI, JSON Schema, schema registry, or generated model changes are claimed compatible without old-reader/new-writer, old-data/new-reader, or generated-client evidence. **Hidden risk:** local validation passes while consumers or stored data break. **Required professional action:** classify compatibility and verify old/new consumer or stored-data behavior. **Route to:** `contract-testing`, `version-compatibility`, `data-migration-design`. **Evidence required:** compatibility class, consumer/storage inventory, schema diff, generated output policy, and old/new validation result.
- **Signal:** YAML unsafe loader, XML entity handling, CSV export, duplicate JSON keys, deserialization, huge nesting, formula-like cell, or untrusted format input reaches runtime. **Hidden risk:** XXE, injection, formula execution, resource exhaustion, or parser-dependent privilege confusion. **Required professional action:** route security review and prove malicious or malformed input is rejected or neutralized. **Route to:** `security-privacy-gate`, `web-security`. **Evidence required:** hostile-input fixture, size/depth limit, safe loader or encoding rule, command output, and residual untested parser/version.
- **Signal:** Generated validators, clients, schemas, fixtures, or checked-in generated artifacts change without a source/generator/output/drift decision. **Hidden risk:** generated files become a stale source of truth and later agents edit the wrong artifact. **Required professional action:** establish generated artifact authority and run or disclose drift validation. **Route to:** `build-tool-professional-usage`, `validation-broker`. **Evidence required:** source spec, generator version/config, generated output path, committed/ignored decision, drift command output or not-run owner.
- **Signal:** Repository graph, project memory, old examples, previous parser output, or historical schema notes are reused after parser, schema, generator, fixture, or stored-format edits. **Hidden risk:** stale memory or graph evidence certifies the wrong compatibility boundary. **Required professional action:** treat graph and memory as selectors, rerun selected parser/schema/fixture checks, and mark stale evidence rejected. **Route to:** `project-memory-governance`, `execution-trajectory-analysis`, `repository-graph-analysis`. **Evidence required:** accepted/rejected memory, graph freshness, changed paths, rerun validator command, exit code, and report/artifact path.

# Critical Details

- **Parser settings are the contract.** Safe loader vs unsafe loader, duplicate-key handling, unknown-field behavior, and coercion options can change behavior without schema text changing.
- **Absent, null, empty, zero, and false differ.** Define each state before mapping data into domain or config behavior.
- **Protobuf compatibility is numeric.** Field names are not the wire contract; field numbers and wire types are.
- **YAML is risky config surface.** `yes`, `on`, `no`, `off`, timestamps, anchors, and tags can be coerced unexpectedly depending on parser version.
- **TOML is strict config surface.** A value moving from `"8080"` to `8080`, array element type changes, or date parsing differences can break consumers that relied on exact types.
- **JSON duplicate keys are ambiguous.** Many parsers keep last value; security-sensitive configs should reject duplicates.
- **XML canonicalization and limits matter.** Equivalent-looking XML can sign, compare, or normalize differently; entity expansion and deep nesting need explicit limits.
- **CPE matching is normalization-sensitive.** Vendor, product, version, update, edition, language, and wildcard handling can change vulnerability matching results.
- **Generated models drift.** Schema source, generated clients, and runtime validators must stay aligned.
- **Golden fixtures prove only configured behavior.** Fixtures must use production parser options and include negative cases.
- **Parser differential tests catch hidden compatibility.** Compare old/new parser settings or library versions when config, schema, or wire-format behavior changes.
- **Data lake formats need old-reader/new-writer checks.** Avro/Parquet changes must be tested against old files and old consumers where compatibility matters.

# Failure Modes

- **Protobuf field reuse:** a removed field number is reused for a new meaning; old consumers interpret new data incorrectly.
- **YAML boolean coercion:** `on` or `yes` becomes boolean true, enabling a feature or permission unexpectedly.
- **Unknown field drop:** parser silently drops new fields, causing partial updates or lost config.
- **Duplicate JSON key:** attacker supplies two `role` keys; parser keeps the privileged value.
- **CSV formula injection:** exported cell begins with `=`, causing spreadsheet execution when opened.
- **XML entity expansion:** unsafe parser resolves external entity or expands payload into resource exhaustion.
- **Timestamp ambiguity:** local time without offset is interpreted differently by producers and consumers.
- **Avro default mismatch:** reader schema expects a default that writer never supplied; old data fails after deployment.
- **Generated client stale:** schema changed but generated models were not regenerated.

# Anti-Rationalization Table

| Rationalization | Hidden Risk | Required Correction |
|---|---|---|
| "It is just a config format." | Parser/coercion behavior changes runtime policy. | Name parser settings and add positive/negative fixtures. |
| "JSON/YAML parser behavior is obvious." | Duplicate keys, unknown fields, or scalar coercion differ by library/version. | Record parser version/options and test edge cases. |
| "Renaming a Protobuf field is safe." | Field numbers and wire types, not names, are compatibility. | Reserve removed numbers/names and verify old/new consumers. |
| "Duplicate keys do not happen." | Attackers or bad generators can choose parser-dependent values. | Reject duplicates where security or config behavior matters. |
| "Golden fixture passed, so all consumers are safe." | Fixture covers one parser and one happy path only. | Add differential, negative, and consumer compatibility evidence. |

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 routing, risk, and output-contract rules.

Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete data-format contract record, fixture plan, compatibility handoff, generated-artifact review, or format migration checklist.
Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) only when parser/serializer behavior, Protobuf/YAML/TOML/XML/CPE compatibility, schema registry, generated model, or storage format risks need deeper benchmark support.
Load [references/evidence-patterns.md](references/evidence-patterns.md) only when the handoff needs concrete fixture, parser-differential, generated-drift, schema-registry, or old-reader/new-writer evidence patterns.
Do not load references for ordinary DTO changes, local JSON literals in tests, or application-level API design with no parser, serialization, wire-format, generated-model, schema-registry, or storage-format risk.
References are just-in-time support, not default-loaded encyclopedia content.

# Output Contract

Return a Data Format Contract Record with:

- `format_surface` (JSON, YAML, TOML, XML, CSV, CPE, Protobuf, Avro, Parquet, schema registry, generated model, parser config)
- `schema_authority` (source file, registry, generated artifact, runtime validator, owner)
- `parser_contract` (library, version, safe mode, coercion, duplicate key, unknown field, null/default behavior)
- `format_specific_contract` (YAML 1.1/1.2 boolean handling, TOML type strictness, XML canonicalization, CPE normalization/version matching)
- `compatibility_class` (backward/forward/full/transitive/additive/breaking/storage-only)
- `field_evolution` (added, removed, reserved, renamed, type changed, default/null/enum behavior)
- `security_contract` (unsafe loader, XXE, formula injection, deserialization, size/depth limits)
- `generated_artifact_policy` (generator, output, committed/ignored, drift check)
- `fixtures_and_validation` (positive/negative examples, golden files, parser differential tests, schema validation, consumer contract tests)
- `decision_record` (change made, alternatives rejected, migration/rollout rationale)
- `validation_freshness` (commands or validators rerun after the final material schema/parser/fixture/generated edit; stale output rejected or named)
- `what_evidence_proves` and `what_evidence_does_not_prove` (covered parser, version, consumer, stored data, generated artifact, and limits)
- `memory_graph_execution_record` (repository graph, project memory, previous parser output, old fixture, or trajectory evidence accepted, rejected, stale, partial, or not used)
- `rollback_or_migration_plan` (schema compatibility window, parser option revert, generator rollback, data backfill/replay, or release sequencing when relevant)
- `residual_risk` (unverified consumer, parser version, old data, schema registry mode, generated artifact)

# Evidence Contract

Close a data-format contract record only when these answers are concrete: **boundaries inspected** across format surface, schema authority, parser/serializer library and options, generated artifacts, fixtures, old/new consumers, stored data, security-sensitive parser inputs, release or migration path, and validation owner; direct schema/config/parser/fixture/output evidence accepted or rejected; repository graph, project memory, old examples, previous parser output, generated artifacts, and execution trajectory used only as selectors unless rerun against current source; validation evidence names command/test/validator/report/artifact, output summary, exit code or not-run status, and freshness after the final material edit; what evidence proves and does not prove for parser version, consumer coverage, stored data, hostile input, generated drift, and old/new compatibility; reuse and placement rationale for schemas, fixtures, generators, validators, and parser settings; behavior preservation, rollback or migration path, residual risk owner, and next gate.

# Quality Gate

1. Format, schema authority, parser library/version/options, and content type are named.
2. Compatibility class is explicit and matches consumer/storage risk.
3. Removed Protobuf fields and enum values are reserved; no field number reuse.
4. YAML/JSON/XML/CSV parser security and coercion behavior is controlled.
5. TOML type strictness, YAML 1.1/1.2 boolean differences, XML canonicalization, size/depth limits, and CPE normalization/version matching are defined when in scope.
6. Null, absent, empty, zero, false, default, and unknown field behavior is defined.
7. Generated artifacts and runtime validators are aligned with drift checks.
8. Positive, negative, golden, and parser differential fixtures validate with production parser settings.
9. Old-reader/new-writer or old-data/new-reader behavior is tested where compatibility matters.
10. Security-sensitive parser risks route to security review.
11. Validation covers at least the changed format/schema/parser/generated/stored-data path with command output, exit code, report/artifact, or a not-run disclosure.
12. Graph, memory, previous parser output, old fixtures, and generated artifacts are freshness-checked and cannot substitute for current schema/parser validation.
13. Residual risk names unverified consumers, parser versions, stored data, schema registry modes, generated outputs, or hostile-input classes.

# Used By

data-api-contract-changer, data-middleware-change-builder, integration-change-builder, quality-test-gate, backend-change-builder, ai-code-review-refactor, consumer-impact-analysis, configuration-runtime-policy

# Handoff

Hand off to `api-contract-design` for operation behavior, `dto-schema-design` for field validation, `contract-testing` for consumer/provider tests, `data-migration-design` for stored data migration, `security-privacy-gate` for unsafe parser or injection risk, and `build-tool-professional-usage` for generated artifacts.

# Completion Criteria

Data-format work is complete when parser behavior, schema authority, compatibility class, field evolution, generated artifacts, fixtures, security posture, and residual consumer/storage risk are all explicit and validated with the same parser settings used in production.
