# Test Suite

## Required Checks

- Expand migration adds nullable split columns without requiring a table rewrite.
- Old client GET and PATCH with full name still work after expand.
- New client GET and PATCH with split fields work during dual write phase.
- Backfill processes bounded batches and resumes after interruption.
- Rollback before cleanup preserves old client behavior.

## Fixtures

- Customers with simple two part names, mononyms, compound last names, and blank edge cases.
- Large table simulation fixture that asserts batch limits.
- Old client contract fixture using full name only.
- New client contract fixture using first name and last name.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Existing full name serialization remains stable until final cleanup.
- Backfill restart does not duplicate work or overwrite manually corrected values.
- Migration rollback leaves schema and application behavior in a known compatible state.