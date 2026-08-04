# Profiling Checklist

- State the user or operational symptom and a falsifiable bottleneck hypothesis.
- Select measurement resolution and method from the suspected compute, wait, allocation, I/O, query, network, rendering, or unit-cost cause.
- Define representative request/data distribution, load shape, runtime/topology, dependencies, cache/startup state, and configuration.
- Lock comparable baseline and candidate conditions before changing the suspected source or configuration.
- Map the measured dominant cost or wait to an owned path and record secondary constraints.
- Record profiler sampling or instrumentation overhead, authority, blast radius, stop condition, and cleanup.
- Re-profile after the change and identify a moved bottleneck, regression, or unchanged hypothesis.
- Measure transferred memory, I/O, queueing, egress, provider usage, rejected work, and unit cost where reachable.
- Compare outputs, errors, state, required work, security, and durability alongside performance.
- Record minimization, redaction, access, storage, retention or deletion, and ephemeral cleanup from classified sensitive fields and artifact persistence.
- State unmeasured workloads, paths, production effects, and secondary bottlenecks as residual risk.
