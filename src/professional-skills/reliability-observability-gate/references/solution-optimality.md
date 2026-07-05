# Solution Optimality Self-Check — Reliability & Observability Gate

Compiled from foundation capability `solution-optimality-evaluation`. Apply when designing
SLI/SLO targets, alert strategies, capacity budgets, and observability instrumentation —
these choices are performance and reliability contracts. Loaded on demand per the skill's
Reference Loading Policy.

**Three-Challenge Rule** — apply to every reliability and observability design decision:
1. **Why this SLI/SLO/alert design?** State the concrete user impact or operational requirement it addresses. An SLO without a user-impact justification is a number without meaning.
2. **Is this the simplest sufficient observability design?** Three golden signals (Rate, Errors, Duration) cover most services. More signals require justification. More alerts require justification. Alert fatigue is a reliability anti-pattern.
3. **What is the strongest alternative, and why is it rejected?** Name it. For example: "Fixed error-count threshold rejected because it fires during non-impacting traffic spikes; burn-rate alerting preferred because it is traffic-proportional."

**Performance Dimension Budget Matrix** — for every change affecting a production service, define or verify the following budgets. A missing budget is an unenforceable SLO:

| Dimension | Required Definition | Reliability-Specific Failure Mode |
|---|---|---|
| **CPU** | What is the CPU utilization budget for this service at steady-state load? What is the saturation threshold (CPU% where queuing begins)? Is there a CPU-based auto-scale trigger? | Service at 90% CPU steady-state has no headroom for traffic spikes; auto-scale triggers too late because it fires at 80% which is already in queueing territory |
| **Memory** | What is the baseline RSS and the maximum RSS after 24h of production load? Is the container memory limit ≥ 2× expected peak RSS? Is there a memory leak detection alert (monotonically increasing RSS over 1h)? | Container memory limit set equal to expected peak RSS — any spike triggers OOM kill; no alert for gradual memory leak before it reaches the limit |
| **Network** | What is the replication lag budget for database replicas? What is the external bandwidth budget? Are metric labels validated for cardinality (no user_id, session_id, or raw path in label values)? | High-cardinality `user_id` label in a request metric creates millions of time-series, causing Prometheus OOM and destroying observability |
| **Disk** | What is the log storage growth rate? Is log rotation and retention policy enforced? Is the alert for disk space at 80% capacity, not 95%? | Disk fills at 95% before alert triggers; 5% headroom disappears in hours during an incident with high logging verbosity |
| **Locks / Connection Pool** | What is the database connection pool saturation threshold? Is there an alert for connection pool wait queue depth > 0 sustained over 60s? | No alert for connection pool exhaustion — the first signal is P99 latency spike and service errors, not a proactive capacity warning |
| **TPS / QPS — RED Method** | Are Rate (requests/s), Error rate (%), and Duration (P50/P95/P99) SLIs defined for every user-facing endpoint? Are they validated as correctly calculated (not including health-check traffic in error rate)? | Error rate SLI includes health-check 200s in denominator — a high-traffic health-check hides actual error rate; error budget appears healthy while users experience errors |
| **Parallelism** | For parallel processing jobs (batch, stream processing), is there a parallelism headroom check? Is the worker count bounded to prevent resource exhaustion? | Unbounded parallel worker spawn exhausts CPU and memory on large batch; no saturation alert before OOM kill |
| **Concurrency** | Is consumer concurrency bounded? Is there a saturation metric for queue consumer lag (Kafka consumer lag, SQS depth)? Is an alert defined for sustained consumer lag growth? | Consumer lag grows for 2 hours before alerting; by the time the alert fires, the lag is 45 minutes of unprocessed events |
| **Response Latency** | Are SLO targets defined as percentiles (P95 for standard, P99 for critical flows, P999 for financial)? Is multi-window multi-burn-rate alerting configured (1h/14× burn for critical page; 6h/6× burn for warning page)? | Single-window fixed-threshold alert fires on non-impacting traffic spikes; misses slow-burn SLO degradation that takes 3 days to exhaust the error budget |

**Additional Professional Considerations for Reliability Design:**
- **Error budget policy is non-negotiable**: When the 28-day error budget is exhausted, feature work stops. The error budget policy must be agreed in writing with the product team before the service ships — not negotiated after the first incident.
- **Alerting on symptoms, not causes**: Alert on SLO burn rate (user-visible impact). Do not alert on CPU%, memory%, disk%, or error count as primary pages — these are diagnostic signals. An alert that fires without user impact is a false alarm that trains operators to ignore alerts.
- **Cardinality budget for metrics**: Every label value combination creates a time-series. A metric with 3 labels each with 100 values creates 1M time-series. Define cardinality limits before instrumenting: label values must be from a bounded set (endpoint name, not URL path with IDs; HTTP status class, not raw status code).
- **Chaos engineering is a reliability gate, not optional**: Circuit breakers, fallback paths, and retry logic that have never been executed under failure conditions are not reliability controls — they are documentation. Conduct a game day before declaring a resilience control production-ready.
- **Tail latency is the user's actual experience**: P99 latency means 1 in 100 user requests is slower. For a user making 100 requests per session, this means every session has at least one slow request. Design SLOs with the user session model, not just the per-request model.
