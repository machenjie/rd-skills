---
name: data-format-contract-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use when Protobuf schemas, parsers, or old-reader/new-writer compatibility changes; skip work without a data-format contract."
---

# data-format-contract-usage

## Registry Trigger

**Use when**

- JSON Schema YAML XML TOML CSV CPE Protobuf Avro Parquet schema registry parser compatibility parser serializer deserializer serialization wire format storage format field evolution compatibility generated model golden fixture
- protobuf field number reserved field enum value wire type breaking change old reader new writer YAML safe loader YAML 1.1 YAML 1.2 scalar coercion TOML type strictness
- duplicate key unknown field boolean timestamp XML canonicalization size depth limit parser differential CPE normalization version matching

**Do not use when**

- no task-local data format contract usage decision is required

## Skill Role

Define format dialect, parser and serializer semantics, schema evolution, canonical meaning, resource bounds, generated-model lineage, and reader/writer compatibility. Exclude transport API design and storage migration.

## High-Value Rules

- **Name the effective format contract.** Identify dialect and version, schema source, parser and serializer implementations, validation mode, encoding, canonicalization, and the persisted or transmitted boundaries that depend on them.
- **Model semantic states explicitly.** Distinguish absent, null, empty, defaulted, unknown, duplicate, invalid, truncated, and unrecognized values wherever consumers or round trips treat them differently.
- **Protect evolution identifiers and meaning.** Evaluate structural and behavioral compatibility while preserving field identity, wire types, enum behavior, aliases, defaults, and unknown fields.
- **Test mixed reader and writer versions.** Exercise current supported combinations, round trips, unknown values, old persisted data, rollback, and generated models using representative fixtures and consumer evidence.
- **Bound parser work from untrusted input.** Define consequence-derived resource limits with explicit rejection and partial-input behavior.
- **Control canonicalization and comparison.** Specify normalization, ordering, numeric precision, timestamp, locale, whitespace, escaping, and signature-sensitive behavior before using textual equality or hashes.
- **Keep generated artifacts attributable.** Bind schema, generator, configuration, runtime library, and checked output to current versions, then classify semantic change separately from regeneration noise.

## Anti-Patterns

- Treat successful parsing as proof that producer and consumer assign the same meaning.
- Infer compatibility from schema validation alone while defaults, unknown fields, enum handling, canonicalization, or generated code change.
- Accept permissive parsing, silent coercion, duplicate keys, or unbounded expansion without an explicit contract and risk owner.

## Stop Conditions

Escalate when the dialect or schema authority is unknown, persisted data cannot be sampled safely, old readers or writers are unowned, or parser behavior differs across supported runtimes. Also escalate when canonicalization affects signing or identity, rollback can make data unreadable, or resource bounds cannot contain untrusted input.

## Output Contract

- data-format decision with effective dialect, semantic states, evolution constraints, mixed-version evidence, resource bounds, canonicalization, generated lineage, proof limits, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Format, parser, compatibility, or security semantics require comparison | Schema authority and parser behavior are already fixed | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Boundary changes coercion, unknown fields, limits, or generated artifacts | No serialized shape or parser option changes | task-agent, analysis-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Format claims need fresh fixtures, validators, or generated diffs | No compatibility or parser-safety claim awaits proof | task-agent, analysis-agent, review-agent | evidence-record, proof-limit, residual-risk |
