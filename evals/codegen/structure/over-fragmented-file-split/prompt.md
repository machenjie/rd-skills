# Benchmark Prompt

## Task

Add a small order cancellation rule without creating micro-file sprawl.

## Context

The starter repository has a cohesive `OrderCancellationService` use-case file.
It already owns authorization checks, deadline checks, refund-hold decisions,
and service-level orchestration. The new requirement adds two small rules:
premium customers receive a short cancellation grace period, and disputed orders
can still cancel but must place the refund on hold.

The change may need one or two private helper predicates. It does not currently
introduce a different owner, lifecycle, collaborator family, side-effect
boundary, public API contract, generated/handwritten boundary, or external
protocol boundary.

## Requirements

- Inspect the existing service, order model, and tests before adding files.
- Prefer extending the existing cohesive owner when the new behavior shares the
  same owner, lifecycle, invariant set, collaborator family, and reason to
  change.
- Keep private helper predicates, local constants, local types, and narrow
  owner-internal value objects in the owning file when cohesive.
- Create a new policy or value-object file only when a real boundary is named
  and the keep in existing file alternative is rejected with evidence.
- Add public behavior tests for standard cancellation, premium grace,
  disputed refund hold, denied authorization, and existing deadline behavior.
- Record navigation cost before and after any split.

## Constraints

- Do not create one-function file artifacts such as
  `order_cancellation_predicate.py`.
- Do not create tiny pass-through files such as `refund_flag_mapper.py`,
  `policy_options.py`, or `cancellation_adapter.py` when they are used only by
  the service.
- Do not export private helpers only to test them.
- Do not justify a split only by line count.
- Do not make a maintainer jump across several files to understand one
  cancellation decision unless those files represent real boundaries.

## Deliverables

- Implementation Structure Plan with a File Granularity Decision.
- Code Clarity Maintainability Review with file navigation cost assessment.
- Tests that prove public cancellation behavior through the service or use-case
  boundary.
- Review note explaining rejected one-function file and micro-file split
  alternatives.

## Completion Evidence

- Passing public behavior tests for the new and existing cancellation outcomes.
- File Granularity Decision documenting the keep-in-existing-file alternative,
  any new-file boundary reason, private helper co-location, and rejected
  micro-file split rationale.
- Navigation cost before/after note showing the main cancellation rule remains
  easier or no harder to follow.
- Review evidence that no automatic failure condition applies.
