# Candidate Graph Evidence

Use this reference to test whether candidate graph claims have enough current evidence for a consumer to accept or reject them. The consumer remains responsible for the final graph.

- Bind every candidate node to one acceptance-linked outcome and produced output.
- Classify proposed dependencies in the current candidate graph as data edges, control edges, contract edges, or order edges.
- An evidence-backed edge records its current source and downstream blocker.
- Record rejected edges with the evidence that makes a proposed relationship nonblocking.
- Map collision surfaces, shared-write surfaces, and resource surfaces before claiming independence.
- For a timing claim, use nonnegative task durations in one common time unit. Record each estimate's source, assumptions, and interval; missing duration evidence remains unknown.
- Derive the candidate critical path from the largest sum of task durations along supported edges in an acyclic graph. Include single-node paths and tied longest paths.
- Dependency depth and node count do not establish elapsed time. If plausible duration estimates change the longest path, retain those alternatives or mark timing unknown.
- The weighted path is a dependency-only duration lower bound. Resource limits and scheduling overhead can increase elapsed time; the consumer owns the executable schedule.
- Identify parallel opportunity only where no path dependency is supported.
- Report cycles and ambiguous ownership as uncertainty instead of resolving them by assumption.
- A consumer acceptance or rejection recommendation includes its proof limits and residual risk.
