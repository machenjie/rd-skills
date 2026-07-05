# Test Suite

## Required Checks

- Planned resource changes are compared against declared monthly cost thresholds.
- Unexpected storage, egress, or compute increases fail the check.
- Approved exceptions require owner, expiry, and budget note.
- Release evidence includes cost diff output and rollback signal.

## Fixtures

- Fixture data for cost regression guardrail.
- Fixture data for resource diff analysis.
- Fixture data for budget thresholds.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: Using production bill totals as the only pre deploy guard.
- Reject shortcut: Letting all cost increases pass when an owner field exists.
- Existing successful behavior remains available after the new guard or compatibility path is added.
