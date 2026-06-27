# Profiling Checklist

- State symptom, hypothesis, workload, data volume, and environment.
- Capture a baseline before changing code.
- Identify CPU, memory, I/O, lock, query, network, allocation, or rendering bottleneck.
- Use representative profiling tools and preserve artifacts.
- Compare after the change with the same scenario.
- Protect sensitive fields in profiles, traces, and logs.
- Map each profiled route, query, job, render path, dependency, cost driver, repository graph edge, accepted/rejected memory item, and validation command to freshness, owner, rollback trigger, handoff gate, or residual risk.
