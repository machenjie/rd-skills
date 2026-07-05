# Benchmark Prompt

## Task

Implement a focused change to add burn rate alerting without creating high cardinality metrics or noisy paging behavior.

## Context

The starter repo represents an API service emits request counters and needs SLO burn alerts for error budget protection. In its initial state, the starter alert uses raw route labels and pages on transient single window spikes. The implementation should be small enough to review but complete enough to prove the professional quality target.

## Requirements

- Fast and slow burn alerts use bounded labels and stable SLO windows.
- High cardinality user, request, and raw path labels are rejected.
- Alerts include actionable severity, owner, dashboard, and runbook metadata.
- Regression tests catch accidental label explosion.

## Constraints

- Alert expressions aggregate by bounded service and outcome dimensions.
- Tests lint expressions for unbounded labels and invalid windows.
- Runbook text explains customer impact and rollback signal.
- Preserve the existing public contract unless the prompt explicitly asks for a compatible addition.
- Do not replace the benchmark with documentation-only output.

## Deliverables

- Source changes in the starter repo that implement the requested behavior.
- Tests or executable checks that prove the required behavior and denial paths.
- A short implementation note describing important tradeoffs and residual risk.

## Completion Evidence

- `bash setup.sh`
- `bash ../test-suite/run.sh`
- `bash ../security-checks/run.sh`
- Review evidence that no automatic failure condition applies.
