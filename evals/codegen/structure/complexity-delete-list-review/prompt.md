# Benchmark Prompt

## Task

Review a generated patch for removable complexity and produce a complexity
delete list.

## Context

The starter repository contains the cohesive billing rule and a real
`review.patch` artifact. Review that patch as supplied; do not apply it and do
not modify the workspace.

## Requirements

- Produce a complexity-only review lane with `delete`, `shrink`, `stdlib`,
  `native`, `existing-code`, and `yagni` tags where applicable.
- Keep correctness, security, reliability, and test findings separate from
  line-count preferences.
- Require caller search and behavior-preservation evidence before deletion.
- Add or name tests that would fail if the billing rule changed.
- Every reportable finding must name the patch file location and concrete impact.

## Constraints

- Do not approve wrappers that only delegate.
- Do not approve one-implementation interfaces or factories without current
  force.
- Do not treat "fewest lines" as approval when boundaries would be lost.
- Do not edit, apply, repair, or regenerate the supplied patch.

## Deliverables

- Complexity Delete List with tagged findings.
- Behavior-preservation and caller-search evidence.
- Minimal Correctness Decision for retained shortcuts or abstractions.

## Completion Evidence

- Automatic review rejects wrapper-only delegation and speculative abstraction.
- Tests or review evidence cover the protected billing behavior.
- Residual risk states any complexity intentionally retained.
- The workspace remains unchanged after the review.
