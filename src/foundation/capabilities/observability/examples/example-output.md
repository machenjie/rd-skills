# Example Output

```markdown
## Observability Plan

Flow: Async account export.

Logs:
- export_id, account_id, actor_role, status, correlation_id.
- Redact filters and file location.

Metrics:
- export_started_total, export_failed_total, export_duration_seconds.
- queue_lag_seconds and file_write_failures_total.

Traces:
- request span links to worker span through export_id.

Alerts:
- Page owner when failure rate exceeds 5 percent for 15 minutes.
- Ticket when p95 duration exceeds 10 minutes for 1 hour.
```
