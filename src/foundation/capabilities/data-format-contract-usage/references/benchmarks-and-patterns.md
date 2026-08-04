# Data Format Contract Benchmarks And Patterns

- RFC 8259 JSON and JSON Schema 2020-12.
- OpenAPI 3.1 for HTTP schema contracts.
- YAML 1.2 plus safe-loader guidance.
- RFC 4180 CSV baseline plus spreadsheet formula-injection defenses.
- XML parser security guidance for XXE and entity expansion.
- Protobuf field evolution and reserved-field guidance.
- Avro schema resolution and Confluent Schema Registry compatibility modes.
- Parquet schema evolution and data lake reader/writer compatibility.

## Format Matrix

| Format | Critical contract | Rejected shortcut |
| --- | --- | --- |
| JSON | duplicate/null/unknown/number/time policy | assume parser defaults are universal |
| YAML | safe loader and scalar coercion policy | parse untrusted config with unsafe loader |
| XML | XXE disabled and namespace policy | allow external entity resolution |
| CSV | delimiter, quote, encoding, formula guard | "comma split" parser |
| CPE | selected specification version, binding/form, logical values, escaping, normalization, and component relations | compare bound strings or versions lexically |
| Protobuf | field number and reserved policy | reuse removed field number |
| Avro | reader/writer schema compatibility | change defaults without old-data test |
| Parquet | nullable/type/partition evolution | rewrite schema without old-reader check |

## Compatibility Classes

Use backward when new readers can read old data, and forward when old readers can read new data. Use full when both directions work. Use transitive when compatibility is required across the complete historical version set. Use breaking when coordinated rollout or migration is required.

## Parser Security

Unsafe YAML loaders, XML external entities, Python pickle-like deserialization, CSV formulas, duplicate JSON keys, huge nesting, and unbounded payload size are security surfaces. Route to security when inputs are untrusted or data controls permissions, money, or execution.

## CPE Decision Pattern

- Select the governing CPE specification version and accepted external form; for CPE 2.3, distinguish WFN, formatted-string binding, and legacy URI binding as the contract requires.
- Parse or unbind that form into logical attributes before deciding identity; preserve `ANY` and `NA` as distinct logical values and keep escaped literals distinct from wildcards.
- Apply normalization defined by the selected specification and contract; guessed vendor, product, or version aliases and collapsed missing, empty, `ANY`, or `NA` states remain invalid.
- Compare source and target attributes component by component, including version, retain each relation and the overall relation, and treat any range or ordering policy outside CPE matching as a separate decision.
