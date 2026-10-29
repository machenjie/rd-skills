# LLM Inference Performance

**Reference type:** targeted
**Load when:** LLM serving needs a quality, latency, capacity, or cost decision under a defined workload.
**Do not load when:** The task only connects an ordinary model API without an inference-performance decision.
**Required by:** analysis-agent, task-agent, review-agent
**Required output:** decision-record, validation-plan, proof-limit

## Shared Measurement Contract

- Fix the quality requirements, operation mix, input/output token distributions, and concurrency or arrival model before comparing configurations.
- Define measurement boundaries for queue delay, time to first token, output generation, and end-to-end completion.
- Record rejected, timed-out, cancelled, and unfinished work alongside successful responses.
- Compare tail latency and consequential quality slices, not throughput averages in isolation.
- Bind cost estimates to actual billing units, prices, workload distributions, cache behavior, and observation dates.
- Reject an unconditional improvement claim when throughput gains violate required quality or tail-latency constraints.

## Hosted API Decisions

- Inspect the actual account and deployment quotas. Distinguish admission limits, rate limits, provider queueing, and client-side waiting.
- Separate input and output token costs and latency contributions. A changed output-length distribution can explain apparent throughput gains.
- Verify cache identity, eligibility, scope, expiry, and accounting against the target provider's current contract.
- Treat cancellation as a client outcome until provider-side execution and billing behavior are known.
- Test retry and timeout policies against duplicate work, amplified traffic, and the required completion semantics.

## Self-Hosted Decisions

- Trace prefill, decode, scheduling, and transfer costs on the actual engine and hardware.
- Evaluate batching against queue delay, request lengths, fairness, and the accepted tail-latency objective.
- Account for weights, activations, KV cache, runtime overhead, and concurrent sequence lengths in device-memory decisions.
- Check cache admission, reuse, eviction, and isolation for the workload. Cache-hit throughput cannot represent an unrelated cold workload.
- Compare quantization and parallelism choices against measured quality, numerical behavior, communication, and device utilization.
- Observe long-context and mixed-length traffic, cancellation, saturation, and recovery before extending a capacity claim.

## Failure Comparisons

| Scenario | Evidence that changes the conclusion |
| --- | --- |
| Throughput rises while long requests starve | Tail latency and fairness by request length |
| Quantization saves memory but degrades a required cohort | Quality regression under the fixed evaluation contract |
| Client cancels but provider continues work | Actual execution state and billed usage |
| Warm-cache benchmark appears cheaper than production | Cache-hit distribution, token mix, and accounting differences |
| Average context fits but concurrent long contexts fail | Peak memory, KV-cache demand, admission, and recovery |

Return the workload-bound tradeoff, deployment configuration, measured limits, and unresolved provider or hardware assumptions.
Keep GPU implementation detail conditional on self-hosted execution; hosted API work does not imply a GPU-kernel task.
Static workload records support accounting checks, not live capacity or billing guarantees.
