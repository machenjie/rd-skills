# Reliability Objective Choice Check

**Load when:** an owned reliability objective, alert strategy, capacity bound, telemetry design, or failure-control choice has a material alternative.

**Do not load when:** no owned objective or operational decision is affected, or current platform policy and evidence already determine the bounded control.

Derive thresholds from the current repository baseline, representative workload, user/business objective, platform policy, and measured evidence; percentiles, burn windows, headroom, autoscaling, sampling, and failure exercises are candidates, not defaults.

## Decision Questions

1. Which user/business consequence and operating owner justify the indicator, target, capacity bound, alert, or recovery control, and what current baseline makes it measurable?
2. Does the chosen SLI or alert reflect the relevant traffic and failure duration, provide an actionable response, and fit current error-budget semantics and operational maturity?
3. Which CPU, memory, connection, queue, storage, network, or cardinality boundary can saturate first under the representative workload, and what measured/platform evidence sets the trigger?
4. What failure mode justifies timeout, retry budget, backpressure, circuit breaking, degradation, recovery exercise, or another control, and what test or incident evidence supports the selected mechanism?
5. If objective, capacity, cost, and operator-response tradeoffs cannot be decided within this boundary, record broader tradeoff analysis as unresolved scope with its evidence need and decision owner.
