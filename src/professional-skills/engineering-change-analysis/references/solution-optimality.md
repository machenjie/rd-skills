# Performance Surface Triage

**Load when:** source inspection shows a plausible material change to execution frequency, input scale, CPU, memory, network, storage, locks, throughput, or user-visible latency.

**Do not load when:** a bounded source check finds no performance path change, or a dedicated performance owner already has the accepted question and evidence.

Derive thresholds from the current repository baseline, representative workload, user/business objective, platform policy, and measured evidence; traffic multipliers and resource formulas are analytical aids, not fixed gates.

## Decision Questions

1. Which changed path executes at meaningful frequency or scale, and what current traffic, job cadence, data size, or user journey makes the delta decision-relevant?
2. Which applicable resource changes—CPU, allocation/state growth, network/database calls, disk/index work, lock contention, or queue overlap—are direct, indirect, or still unverified?
3. Does the change amplify an existing fan-out, N+1, cache invalidation, batch, scheduled job, or synchronous dependency even if it did not introduce the original pattern?
4. What source measurement, profile, plan, benchmark, or representative test would distinguish acceptable impact from an unsupported assumption, and what does it not prove?
5. If the tradeoff expands beyond impact triage into selecting among
   cross-resource solutions, stop at the performance-impact boundary and state
   that a dedicated optimization decision is required.
