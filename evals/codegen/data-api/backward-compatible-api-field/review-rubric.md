# Review Rubric

## Passing Standard

The implementation must be additive and backward compatible across DTOs,
schemas, persistence, and docs. Old client behavior must be protected by tests,
not only described in prose.

## Scoring

- 30 percent contract compatibility for additive schema, nullability, and old client fixtures.
- 20 percent validation correctness for allowed values and stable error shape.
- 20 percent persistence and mapping for existing records and new values.
- 15 percent test quality for unit, integration, and contract coverage.
- 15 percent documentation quality for examples, API diff, and migration notes.

## Automatic Failure Conditions

- Existing clients must send the new field to keep working.
- Existing response fields are renamed, removed, or semantically changed.
- Invalid enum values are stored or silently accepted.
- Authorization checks are bypassed or weakened.

## Reviewer Notes

Reward solutions that keep compatibility decisions visible in tests and docs.
Penalize broad rewrites of the profile API when a focused additive change would
be sufficient.