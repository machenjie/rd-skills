# Security Checks

## Threat Surface

This benchmark touches OTA update lifecycle, A/B rollback, device health confirmation, staged rollout. A flawed implementation can expose data, weaken integrity, hide operational failure, or ship a release path that cannot be safely reviewed.

## Required Checks

- Verify that state machine separates downloaded, activated, confirmed, failed, and rolled back states.
- Verify that tests simulate reboot loss, failed health, and successful confirmation.
- Verify that rollout metrics expose device cohort health and rollback counts.
- Verify that runbook explains manual pause and recovery.

## Rejection Cases

- Reject any solution that uses marking OTA success before post boot health confirmation.
- Reject any solution that uses activating unsigned or identity mismatched packages.
- Reject any solution that uses continuing rollout after cohort health falls below threshold.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
