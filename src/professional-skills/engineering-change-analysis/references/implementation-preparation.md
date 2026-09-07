# Implementation Preparation

Use read/search-only analysis when the user requests design or current source evidence leaves an important implementation decision unresolved. Unknown local files, owners, tests, or callers normally stay with the implementation agent's bounded discovery.

Resolve the named question: competing owner, behavior or invariant, shared contract or consumer, concurrency, transaction, recovery, migration, authority, or integration semantics. Inspect enough current source and relevant tests to distinguish alternatives and their consequences. Return the key decision, evidence, validation implications, and remaining issues; stop when implementation can proceed correctly.

An Engineering Brief is optional, for complex cross-agent work needing stable decisions. If needed, retain Goal, important constraints/invariants, key decisions, validation, and unresolved issues. Do not require a complete Brief, Task Contract, First Executable Slice, DAG, or independent Review before ordinary implementation.

Preserve settled decisions. Reopen only the affected questions when new evidence invalidates an important judgment; do not re-analyze on task switches, ordinary discovery, repair, or a preference for a different design.

## Evidence Discipline

- Bind material conclusions to current source, an executable observation, or clearly labeled external evidence.
- Separate source facts, supported inferences, reversible assumptions, and
  unknowns. An unknown cannot be reported as no impact.
- Treat generated reports, dependency graphs, examples, and prior analysis as
  selectors until current source confirms them.
- Scan for the same failure or ownership pattern before proposing a local fix;
  record searched scope, related occurrences, and why the change is local or broad.
- Map each changed surface to a validation signal and state what that signal cannot prove.
- Do not use provider-only checks as proof of downstream consumer behavior.

## Coordination

Decompose only for real dependencies or useful independent work. Keep jointly validated changes together. Account for shared resources, write collisions, ordered migration, external consumers, integration ownership, and cross-task validation when the evidence makes them relevant. A DAG can communicate those dependencies; it is not a default analysis output.
