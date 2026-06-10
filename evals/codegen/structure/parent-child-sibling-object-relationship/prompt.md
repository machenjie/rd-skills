# Benchmark Prompt

## Task

Refactor cancellation, refund, and shipping rules that are mixed in one service
into explicit object relationships without creating pass-through objects.

## Context

The starter repository has a large `OrderLifecycleService` where cancellation,
refund, and shipping decisions are intertwined. Some behavior may be child
detail under a parent lifecycle coordinator. Other behavior may be peer sibling
policies with independent change reasons.

## Requirements

- Decide whether cancellation, refund, and shipping are parent-child,
  sibling, collaborator, policy, or module-local helper relationships.
- Keep the parent responsible for public lifecycle/orchestration when a
  parent-child split is chosen.
- Keep detailed sub-behavior inside children without letting children reach
  into parent internals.
- Keep sibling policies independent and prevent sibling internal access.
- Route shared behavior through explicit policy, value object, contract, or
  module-local helper.

## Constraints

- Do not split by method names only.
- Do not create a parent that only forwards calls.
- Do not let cancellation, refund, and shipping siblings call each other's
  private methods.
- Do not move shared business behavior to shared/common just to avoid ownership.

## Deliverables

- Implementation Structure Plan with Object Relationship Map.
- Parent-child or sibling rationale for each extracted object.
- Public behavior tests for cancellation, refund, shipping, and combined
  lifecycle outcomes.
- Review note listing allowed collaboration and forbidden internal access.

## Completion Evidence

- Tests prove parent lifecycle behavior and sibling policy behavior.
- Relationship map declares type, direction, allowed collaboration, and
  forbidden internal access.
- Review evidence shows no pass-through parent and no sibling internal access.
