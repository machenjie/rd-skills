# Example Output

## Input Scenario

A Protobuf field is removed from an event schema and a YAML feature flag file adds `on` as a value. Several old consumers still read the event.

## Selected Capability

`data-format-contract-usage`

## Decision Record

- Format surface: Protobuf event schema and YAML runtime config.
- Schema authority: `events/order.proto` and `config/features.yaml`.
- Parser contract: Protobuf generated models; YAML 1.2 safe loader with duplicate-key rejection.
- Decision: reserve the removed Protobuf field number and name; quote YAML scalar `"on"` or replace with explicit enum value.
- Rejected shortcut: deleting the field without reservation would allow future field-number reuse and wire-data corruption.

## Evidence Checklist

- Old and new schema compared.
- Removed field number and enum values reserved.
- YAML ambiguous scalar checked under production parser.
- Generated models regenerated.
- Old-reader/new-writer fixture added.

## Validation Commands

```
buf lint
buf breaking --against .git#branch=main
npm run generate:proto
pytest tests/config/test_feature_flags.py
```

## Residual Risk

One external consumer outside the repository was not tested. Owner: platform API team. Follow-up trigger: schema registry compatibility failure.

## Handoff Summary

The change is additive-safe only after reserving removed Protobuf numbers and enforcing YAML parser behavior. External consumer compatibility remains the release gate.
