# Solution Optimality Self-Check — Integration Change Builder

Compiled from foundation capability `solution-optimality-evaluation`. Apply to every
integration change that introduces or modifies outbound calls, retry logic, circuit
breakers, webhook handling, or provider dependencies. Loaded on demand per the skill's
Reference Loading Policy.

**Three-Challenge Rule** — answer all three before finalizing any integration design:
1. **Why this approach?** State the concrete reason (not "it's the standard pattern"). What specific resilience, compliance, or operational requirement drives this design?
2. **Is this the simplest sufficient design?** A synchronous call with a timeout is simpler than an async queue + DLQ + reconciliation job. Use the simpler approach unless reliability requirements explicitly require the complexity.
3. **What is the strongest alternative, and why is it rejected?** Name it. Reject it with a specific cost ("synchronous path makes us unavailable when provider is down", "no reconciliation means undetected payment drift", "polling adds 30s average processing latency").

**Performance Dimension Checklist** — evaluate each or declare N/A with a one-line rationale:

| Dimension | Required Question | Integration-Specific Failure Mode |
|---|---|---|
| **CPU** | What is the CPU cost of the retry backoff algorithm (exponential + jitter calculation)? Is response deserialization on the critical path? Is there unnecessary re-serialization of the request body on each retry? | Retry loop serializes the full request body 5 times from scratch instead of serializing once and reusing the byte array |
| **Memory** | Is the retry queue bounded? What is the maximum in-memory payload size if 1,000 retries are queued? Is response streaming used for large provider responses instead of buffering the entire body? | Unbounded in-memory retry queue grows to GBs during provider outage; large file download buffered entirely in heap before processing |
| **Network** | What is the maximum network amplification factor: (base RPS) × (max retries) × (payload size bytes)? Does this stay within provider rate limits and internal bandwidth budgets? Is connection keep-alive enabled to avoid TCP handshake overhead per retry? | Retry storm: 100 RPS × 5 retries × 50KB payload = 25 MB/s to provider during an outage — may exhaust provider rate limit and trigger account suspension |
| **Disk** | Are retry events logged to disk? Is the log volume bounded (log rotation, structured log level control)? Is DLQ persistence cost (storage per message × max queue depth) acceptable? | Every retry attempt logged at INFO with full request body — 5 retries × 50KB × 1,000 concurrent requests = 250MB disk per minute during incident |
| **Locks / Contention** | Is the idempotency key lookup thread-safe under concurrent retries? Can two concurrent requests race on the same idempotency key deduplication store? | Two concurrent retries for the same request both pass the idempotency check because the first has not yet committed the key record |
| **TPS / QPS** | What is the maximum RPS this integration sends to the provider? Is it validated against the provider's rate limit (requests per second, requests per day, burst limit)? Is a token bucket or leaky bucket algorithm used for smoothing? | Integration sends 120 RPS to a provider with a 100 RPS rate limit; every 12th request is throttled; no rate limit awareness means all 120 requests are sent and 17% fail |
| **Parallelism** | Are independent outbound calls executed in parallel where the provider allows it? Is there a concurrency limit to prevent overloading the provider or exhausting the local connection pool? | 500 concurrent webhook deliveries opened simultaneously exhaust the HTTP connection pool; no semaphore or concurrency limit configured |
| **Concurrency** | Are concurrent retry storms handled via jitter (preventing synchronized retries from all instances)? Is there a distributed circuit breaker state that is consistent across multiple application instances? | All 10 application instances retry simultaneously at the same backoff intervals — synchronized retry storm hits provider at identical milliseconds |
| **Response Latency** | What is the timeout window (connection timeout + read timeout)? Is the timeout validated against the provider's documented SLA? Is tail latency amplification considered for fan-out to multiple providers? | Default timeout of 30s means a slow provider holds a thread for 30s; at 100 concurrent slow requests this exhausts the thread pool |

**Additional Professional Considerations for Integrations:**
- **Retry storm cost formula**: Maximum amplified network load = (base RPS) × (max_retries + 1) × (payload_size). Calculate this before setting retry counts — a 5-retry policy at 200 RPS with 10KB payloads generates 12 MB/s sustained toward the provider during an outage.
- **Back-pressure from the provider**: When the provider sends `429 Too Many Requests` with a `Retry-After` header, the correct response is to pause all requests for that window — not to continue retrying and discard the header. Implement `Retry-After` header parsing before setting retry counts.
- **Tail latency amplification in fan-out**: If a user action fans out to 3 external providers in parallel, the P99 of the user-visible response is driven by the slowest of the 3, not the average. Design timeout windows for the aggregate, not for each individual call.
- **Provider migration shadow mode**: When migrating from provider A to provider B, run both in parallel for a period, compare results, and reconcile discrepancies before cutting over. Never migrate by simply swapping providers and hoping the outputs match.
- **Reconciliation is not optional for money and state**: Any integration that moves money, provisions accounts, or changes entitlements must have a scheduled reconciliation job that detects and alerts on drift between local state and provider state — regardless of how reliable the provider claims to be.
