# Benchmark Prompt

## Task

Fix a backend statement-order bug that publishes an event before transaction commit.

## Context

The starter repo has an order update service that writes the database, publishes
an event, updates cache, and commits in the wrong order.

## Requirements

- Ensure durable state commits before event publication and cache mutation.
- Preserve idempotency and rollback behavior.
- Add tests for commit failure and publish-after-commit ordering.
- Include code-element, side-effect-flow, and transaction evidence.

## Constraints

- Do not publish duplicate events.
- Do not update cache from uncommitted state.
- Do not move ordering logic into a generic helper without owner proof.

## Deliverables

- Updated backend service.
- Ordering and failure-path tests.
- Handoff with transaction/event/cache order evidence.

## Completion Evidence

- Test output proving no event or cache write occurs when commit fails.
- Review note naming the statement order and residual risk.

