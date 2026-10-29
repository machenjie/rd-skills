# Test Suite

## Required Checks

Invoke the candidate with current source, anchored feedback, and independently executed observations. Assert currentness, disposition, bounded edit behavior, and each separate action permission.

## Fixtures

The passing candidate implements the contract. The starter is incomplete. The faulty candidate changes only currentness handling to reject every older comment commit.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

Reject discarding valid reverified old feedback and inferring external authority from code work. Smoke only rejects starters; run the passing and single-defect candidates separately.
