# Data Format Contract Evidence Patterns

## Required Evidence

- Format and content type.
- Schema authority and owner.
- Parser/serializer library, version, and options.
- Compatibility mode and consumer/storage inventory.
- Positive fixtures, negative fixtures, golden files, and validation command.
- Generated artifact source/generator/output/drift policy.
- Migration/backfill/read-old-data command when stored data is affected.

## Fixture Requirements

Include examples for absent vs null, false vs missing, zero vs empty, unknown fields, duplicate keys where relevant, old and new schema, and malformed hostile input. For Protobuf include reserved fields. For YAML include ambiguous scalars. For CSV include formula-looking cells.

## Handoff Shape

```
Data Format Contract Record
- Format surface:
- Schema authority:
- Parser contract:
- Compatibility:
- Fixtures/validation:
- Residual risk:
```

## Blocking Conditions

Block completion when parser settings are unknown, Protobuf numbers are reused, YAML/XML unsafe parsing is used on untrusted input, generated artifacts are stale, or compatibility is claimed without old/new fixture evidence.
