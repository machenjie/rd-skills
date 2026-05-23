# Test Suite

## Required Checks

- Skewed key behavior is identified and mitigated with a named strategy.
- Shuffle partition count and output file size are justified.
- Data quality checks gate promotion.
- Cost, freshness, scan volume, and duration metrics are defined.

## Fixtures

- Fixture data for skewed keys and shuffle-heavy joins.
- Fixture data for partition filters and compaction decisions.
- Fixture data for data quality promotion checks.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: repartition(1) for production output.
- Reject shortcut: Blind cache() without reuse evidence.
- Reject shortcut: Full table scan with no partition filter or cost approval.
- Existing successful behavior remains available after the new guard or compatibility path is added.
