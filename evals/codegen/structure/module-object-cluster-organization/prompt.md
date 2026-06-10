# Benchmark Prompt

## Task

Organize cancellation-related objects, methods, and functions into a cohesive
order cancellation module rather than a directory collection.

## Context

The starter repository has cancellation service logic, cancellation policy,
refund hold behavior, order status values, persistence calls, payment adapter
calls, DTO mapping, and private helpers spread across several files. The goal is
to form one module owned by the order cancellation capability while preserving
local repository conventions.

## Requirements

- Identify the module capability or layer first.
- List objects and functions inside the module and classify them as public API,
  internal domain/value/service/policy/repository/adapter/mapper/helper/test.
- Define the module public facade and keep it minimal.
- Define module private internals and forbidden external access.
- Define internal dependency direction and object graph.
- Name next-change location for future cancellation rules, adapter changes,
  DTO changes, and tests.

## Constraints

- Do not create one directory per object without module cohesion.
- Do not move business logic to shared/common.
- Do not expose internal policies, repositories, adapters, mappers, helpers, or
  concrete child objects as public API just in case.
- Do not group unrelated object families in the cancellation module.
- Do not skip the object graph or internal dependency direction.

## Deliverables

- Module Internal Composition Plan.
- Module boundary map with public facade, private internals, object graph, and
  internal dependency direction.
- Tests through the module public facade and any declared contracts.
- Review note listing rejected split/no-split and shared/common alternatives.

## Completion Evidence

- Public facade tests pass for cancellation allowed, denied, refund hold, and
  adapter failure paths.
- Module object graph declares allowed collaboration and forbidden internal
  access.
- Review evidence shows public API is minimal and next-change location is
  obvious.
