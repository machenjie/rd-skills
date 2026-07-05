# Benchmark Prompt

## Task

Review a generated patch for removable complexity and produce a complexity
delete list.

## Context

The starter repository has one cohesive billing rule. A generated patch may add
wrapper-only delegation, one-implementation interfaces, unused configuration,
future extension scaffolding, and duplicated helper code.

## Requirements

- Produce a complexity-only review lane with `delete`, `shrink`, `stdlib`,
  `native`, `existing-code`, and `yagni` tags where applicable.
- Keep correctness, security, reliability, and test findings separate from
  line-count preferences.
- Require caller search and behavior-preservation evidence before deletion.
- Add or name tests that would fail if the billing rule changed.

## Constraints

- Do not approve wrappers that only delegate.
- Do not approve one-implementation interfaces or factories without current
  force.
- Do not treat "fewest lines" as approval when boundaries would be lost.

## Deliverables

- Complexity Delete List with tagged findings.
- Behavior-preservation and caller-search evidence.
- Minimal Correctness Decision for retained shortcuts or abstractions.

## Completion Evidence

- Automatic review rejects wrapper-only delegation and speculative abstraction.
- Tests or review evidence cover the protected billing behavior.
- Residual risk states any complexity intentionally retained.
