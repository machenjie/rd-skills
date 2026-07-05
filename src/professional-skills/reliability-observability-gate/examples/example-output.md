# Example Output

SLI impact: Project archive request success rate and latency.

Performance budget: p95 below 300 ms for synchronous endpoint.

Controls: Idempotency prevents duplicate retries; rate limit protects bulk archive path.

Telemetry: Counter for archive failures by reason, trace span around transaction, alert on error spike.

Recovery: Reconciliation job detects projects with missing audit records.
