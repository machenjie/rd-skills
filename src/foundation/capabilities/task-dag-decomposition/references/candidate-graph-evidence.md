# Candidate Graph Evidence

Use this reference to test whether candidate graph claims have enough current evidence for a consumer to accept or reject them. The consumer remains responsible for the final graph.

- Bind every candidate node to one acceptance-linked outcome and produced output.
- Classify proposed dependencies in the current candidate graph as data edges, control edges, contract edges, or order edges.
- An evidence-backed edge records its current source and downstream blocker.
- Record rejected edges with the evidence that makes a proposed relationship nonblocking.
- Map collision surfaces, shared-write surfaces, and resource surfaces before claiming independence.
- Derive the candidate critical path only from supported edges.
- Identify parallel opportunity only where no path dependency is supported.
- Report cycles and ambiguous ownership as uncertainty instead of resolving them by assumption.
- A consumer acceptance or rejection recommendation includes its proof limits and residual risk.
