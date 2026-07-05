# Security Checks

## Threat Surface

This benchmark touches large data scans, job cost, freshness, and quality gates. A flawed implementation can hide stale outputs, create runaway compute cost, or promote bad data to downstream consumers.

## Required Checks

- Verify that partition filters and cost approval are required for full table scans.
- Verify that data quality failures block promotion.
- Verify that metrics include freshness and job duration.
- Verify that tuning notes do not mask data loss or silent sampling.

## Rejection Cases

- Reject any solution that uses repartition(1) for production output.
- Reject any solution that uses blind cache() without reuse evidence.
- Reject any solution that performs a full table scan with no partition filter or cost approval.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
