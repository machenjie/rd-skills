# Integration Failure-Path Choice Check

**Load when:** an outbound call, webhook, provider migration, retry, concurrency, delivery, or reconciliation design has a material failure, latency, cost, or state-consistency tradeoff.

**Do not load when:** the provider contract and accepted task already determine a bounded adapter change with no material delivery or failure-mode choice.

Derive thresholds from the current repository/provider baseline, representative workload, user/business objective, platform policy, and measured evidence; queues, retries, circuit breakers, throttles, shadowing, and reconciliation are candidates, not defaults.

## Decision Questions

1. What provider guarantees, rate/latency behavior, payload size, traffic shape, and user-visible consequence define the integration boundary under normal and failed operation?
2. Is synchronous, deferred, queued, polled, or callback delivery justified by current latency, availability, ordering, and recovery needs, and what is the simplest supported path?
3. How do timeout, retry, concurrency, backpressure, and idempotency choices affect amplification, local resource saturation, provider limits, and duplicate outcomes?
4. When external state can diverge materially, what detection, comparison, reconciliation, or migration evidence is proportional to the business consequence rather than assumed for every integration?
5. If provider, reliability, cost, and consistency tradeoffs remain coupled, identify `solution-optimality-evaluation` as the broader owner; this reference does not load it automatically.
