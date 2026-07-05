# Example Output

## Big Data Domain Findings
- Blocking: the metric change must declare grain, time zone, late-arrival window, and dashboard compatibility notes before implementation.
- Backfill requirement: run bounded partition backfill with row-count, revenue-total, and duplicate-key comparisons before publishing.
- Cost guardrail: add partition pruning and query budget alert for the new reporting table.

## Verification
- Data quality assertions for completeness, uniqueness, validity, and distribution drift.
- Replay test with duplicate and out-of-order events.
- Monitoring for freshness SLA, bad-record count, job failure, and warehouse cost.
