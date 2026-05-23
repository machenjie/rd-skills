# Security Checks

## Threat Surface

This benchmark touches SLO burn rate, metric cardinality, alert noise control, runbook evidence. A flawed implementation can expose data, weaken integrity, hide operational failure, or ship a release path that cannot be safely reviewed.

## Required Checks

- Verify that alert expressions aggregate by bounded service and outcome dimensions.
- Verify that tests lint expressions for unbounded labels and invalid windows.
- Verify that runbook text explains customer impact and rollback signal.
- Verify that notification policy distinguishes page and ticket severity.

## Rejection Cases

- Reject any solution that uses using user id or raw URL path as alert labels.
- Reject any solution that uses paging on a single short window without sustained burn evidence.
- Reject any solution that uses alerting on request volume alone instead of error budget burn.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
