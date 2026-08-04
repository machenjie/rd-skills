# Data Format Contract Evidence Patterns

- Format and content type.
- Schema authority and owner.
- Parser/serializer library, version, and options.
- Compatibility mode and consumer/storage inventory.
- Positive fixtures, negative fixtures, golden files, and validation command.
- Generated artifact source/generator/output/drift policy.
- Migration/backfill/read-old-data command when stored data is affected.

## Fixture Requirements

Include examples for absent versus null, false versus missing, zero versus empty, unknown fields, and relevant duplicate keys.
Include old-schema, new-schema, and malformed hostile input examples.
For Protobuf, include reserved fields.
For YAML, include ambiguous scalars.
For CSV, include formula-looking cells.

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

Block completion when parser settings are unknown.
Block completion when Protobuf numbers are reused.
Block completion when YAML or XML uses unsafe parsing on untrusted input.
Block completion when generated artifacts are stale.
Block compatibility claims without old/new fixture evidence.
