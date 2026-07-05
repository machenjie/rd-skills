# Benchmark Prompt

## Task

Implement a small order label behavior while proving the minimal correct
implementation path.

## Context

The starter repository has one order module and one existing formatter helper.
The requested behavior is local: archived orders should display an `ARCHIVED`
suffix in one public label function. A generated proposal may try to add a new
service, factory, config switch, or shared utility.

## Requirements

- Search existing order label and formatter code before adding new structure.
- Prefer existing repository code, standard library, native language behavior,
  installed dependency, and local direct code in that order.
- Keep the behavior in the current order owner unless a real boundary is
  proven.
- Add public behavior tests for active and archived labels.
- Return a Minimal Correctness Decision with deleted or rejected complexity.

## Constraints

- Do not add a service, factory, interface, registry, or config option for one
  label rule.
- Do not move order business terms into shared/common/utils.
- Do not claim "fewer files" as the reason; use owner and boundary evidence.

## Deliverables

- Updated order label implementation.
- Tests for the public label function.
- Minimal Correctness Decision naming the ladder result and rejected options.

## Completion Evidence

- The test command fails if archived labels are not handled.
- The review evidence rejects speculative service/factory/config growth.
- The final implementation keeps required safety gates and validation evidence.
