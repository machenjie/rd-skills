# Test Suite

## Required Checks

- API DTO as domain object and ORM persistence model response leakage are rejected.
- Mapper business rules are rejected unless explicitly modeled as policy.
- Mapping tests preserve null, default, optional, serialization, and validation semantics.
- Event payload version compatibility and generated boundary behavior are tested.

## Fixtures

Mapping fixtures belong to the account contract boundary and must state source model, target model, version, and null/default semantics.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Missing display name remains distinct from empty display name.
- Persistence-only audit fields do not appear in API output.
- Old event payload version still maps correctly.
- Generated client model does not import domain behavior.
