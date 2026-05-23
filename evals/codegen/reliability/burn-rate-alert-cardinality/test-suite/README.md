# Test Suite

## Required Checks

- Fast and slow burn alerts use bounded labels and stable SLO windows.
- High cardinality user, request, and raw path labels are rejected.
- Alerts include actionable severity, owner, dashboard, and runbook metadata.
- Regression tests catch accidental label explosion.

## Fixtures

- Fixture data for slo burn rate.
- Fixture data for metric cardinality.
- Fixture data for alert noise control.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: Using user id or raw URL path as alert labels.
- Reject shortcut: Paging on a single short window without sustained burn evidence.
- Existing successful behavior remains available after the new guard or compatibility path is added.
