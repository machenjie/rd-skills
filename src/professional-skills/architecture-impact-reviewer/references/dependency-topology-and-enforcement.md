# Dependency, Topology, and Enforcement

Use this Reference only when dependency direction, runtime topology, or durable enforcement changes.

## Decision Rules

- When dependency direction changes, state the effective source edge and evidence against the repository's ownership or model. A topology change includes its failure, capacity, or availability boundary and operational owner. A durable rule carries selected enforcement and proof supported by current repository or platform controls.
- When dependency direction changes, require an effective source-level edge and ownership rationale that protects the repository's enforced stability model rather than a generic layered rule.
- When runtime or deployment topology changes, require failure-boundary, capacity/availability consequence, operational ownership, and containment evidence. Isolation, async decoupling, redundancy, or unchanged topology are candidates justified by the actual platform and traffic assumptions.
- When an architecture rule must survive future edits, require enforcement evidence supported by the repository or platform. Tests, lint/import rules, policy-as-code, build graph checks, code ownership, or review policy are candidates; documentation alone may be sufficient when automation cost exceeds current risk and policy permits it.
- Topology and enforcement proof applies only when that boundary changes.
5. **Review mode:** judge placement, dependency direction, and enforcement.
