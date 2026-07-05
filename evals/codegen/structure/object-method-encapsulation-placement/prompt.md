# Benchmark Prompt

## Task

Refactor scattered order cancellation helpers into the right object, service,
adapter, or module-local location without creating fake object structure.

## Context

The starter repository has an `OrderCancellationService` with several helper
functions. Some helpers protect a cancellation window value invariant and should
move into a value object. Some helpers protect order lifecycle state and may
belong on a domain object. Some helpers are simple module-local predicates. One
helper calls a payment provider and must remain in an adapter boundary.

## Requirements

- Classify object candidates before moving methods or creating classes.
- Move only state, invariant, lifecycle, or collaborator-protecting behavior
  onto domain/value objects.
- Keep orchestration in the service/use-case object.
- Keep payment, persistence, cache, queue, clock, and framework side effects in
  adapters, repositories, or services rather than domain/value objects.
- Domain/value object files such as `orders/order.py` must not import, mention,
  or call `PaymentAdapter`, `payment provider`, `refund_payment`, `chargeback`,
  `requests`, or other payment/refund side-effect APIs. They may return a pure
  cancellation/refund-hold decision for the service to orchestrate.
- Keep private helpers private and test behavior through public service or
  module facade behavior.

## Constraints

- Do not create a helper-bag class.
- Do not create an anemic object with getters and setters only.
- Do not move a method to an object because the filename looks right.
- Do not export private helpers just so tests can import them.
- Do not make a domain/value object import infrastructure, UI, or framework
  concerns.

## Deliverables

- Implementation Structure Plan with Object-Method Encapsulation Decision.
- Object candidates list with accepted and rejected object/function/helper
  alternatives.
- Method placement rationale for each moved or unchanged helper.
- Public behavior tests for cancellation decisions and adapter side effects.

## Completion Evidence

- Public behavior tests pass for allowed, denied, expired, refund-hold, and
  payment failure paths.
- Review note identifies methods owned by objects and methods rejected from
  object placement.
- Evidence shows private helpers remain private and infrastructure stays out of
  domain/value objects.
- Evidence shows payment/refund provider calls are delegated from the service to
  an adapter boundary and never hidden inside domain/value objects.
