# Backend Runtime Choice Check

**Load when:** an accepted backend implementation chooses an algorithm, query pattern, cache, batching/streaming boundary, concurrency control, pool, queue, or other resource-sensitive design.

**Do not load when:** no runtime/resource tradeoff is material, or the accepted task already fixes the mechanism from current system evidence.

Derive thresholds from the current repository baseline, representative workload, user/business objective, platform policy, and measured evidence; framework defaults, formulas, and candidate mechanisms are not answers by themselves.

## Decision Questions

1. What input distribution, request/job frequency, data volume, concurrency, and latency/throughput objective make this choice material, and which current measurements support them?
2. How does the choice change query/call count, CPU, allocation, storage I/O, connection/lock contention, queue growth, or degradation at the affected boundary?
3. Does current storage and framework behavior support the selected cache, batch, stream, lock, pool, or backpressure mechanism, including failure and cleanup paths?
4. What simpler repository-consistent implementation was inspected, and which measured saturation, correctness, or operability constraint rules it out?
5. When acceptable limits depend on future load, record the evidence-backed trigger, decision owner, and broader tradeoff-analysis need as unresolved scope.
