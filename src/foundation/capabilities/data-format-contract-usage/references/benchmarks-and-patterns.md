# Data Format Contract Benchmarks And Patterns

## Benchmarks

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
| Protobuf | field number and reserved policy | reuse removed field number |
| Avro | reader/writer schema compatibility | change defaults without old-data test |
| Parquet | nullable/type/partition evolution | rewrite schema without old-reader check |

## Compatibility Classes

Use backward when new readers can read old data, forward when old readers can read new data, full when both directions work, transitive when all historical versions must work, and breaking when coordinated rollout or migration is required.

## Parser Security

Unsafe YAML loaders, XML external entities, Python pickle-like deserialization, CSV formulas, duplicate JSON keys, huge nesting, and unbounded payload size are security surfaces. Route to security when inputs are untrusted or data controls permissions, money, or execution.
