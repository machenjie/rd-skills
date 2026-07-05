# Solution Optimality Checklist

Use this checklist when drafting or reviewing a concrete optimality decision. Keep the capability body for selection and output rules; use this file for the repeatable decision pass.

- State the problem as a decision question, not as the proposed implementation.
- Name non-goals, constraints, owner, current behavior, desired behavior, and production-scale assumptions.
- List at least two viable candidates; include delete, reuse, native/stdlib, local direct implementation, and new abstraction/dependency where relevant.
- For each candidate, record time complexity, space complexity, I/O shape, reversibility, ownership cost, testability, and failure/rollback implications.
- Apply the three-challenge rule: why this approach, simplest sufficient design, strongest rejected alternative with specific cost.
- Evaluate CPU, memory, network, disk, locks/contention, TPS/QPS, parallelism, concurrency, response latency, and rendering speed, or mark each N/A with rationale.
- Classify hot/cold path and whether benchmark/profile/load evidence is required before approval.
- Check cognitive complexity, side-effect boundaries, security surface, operational cost, and observability/no-log rationale.
- Classify reversibility and any deferred optimization threshold with owner.
- Map the chosen decision and each material rejected risk to validation evidence or residual risk.
