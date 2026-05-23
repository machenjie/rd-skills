# Security Checks

## Threat Surface

This benchmark touches cost regression guardrail, resource diff analysis, budget thresholds, release evidence. A flawed implementation can expose data, weaken integrity, hide operational failure, or ship a release path that cannot be safely reviewed.

## Required Checks

- Verify that cost checks run from deterministic infrastructure plan input.
- Verify that thresholds are scoped by service and environment.
- Verify that tests include below threshold, above threshold, and approved exception cases.
- Verify that output is readable by reviewers and CI systems.

## Rejection Cases

- Reject any solution that uses using production bill totals as the only pre deploy guard.
- Reject any solution that uses letting all cost increases pass when an owner field exists.
- Reject any solution that uses ignoring egress and storage lifecycle cost changes.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
