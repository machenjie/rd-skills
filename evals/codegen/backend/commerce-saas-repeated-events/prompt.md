# Benchmark Prompt

## Task

Implement deterministic commerce and SaaS acceptance evaluators from fixed event records. Implement the bounded counterexample shrinker defined in task.md.

## Context

The Python starter currently returns optimistic defaults. The work is a standalone validation implementation. Read `task.md` for data fields and observable outcomes, and `plan.md` for the bounded approach.

## Requirements

- Expired reservations cannot be silently fulfilled by late payment.
- Repeated cancellation preserves inventory and partial returns preserve conservation.
- SaaS entitlement follows the explicit grace, downgrade, refund, seat, and usage policies.
- Shrinking retains reservation preconditions and replays a minimal duplicate-cancellation counterexample.

## Constraints

- Treating payment as proof of allocation or fulfillment.
- Incrementing inventory for a replayed cancellation.
- Hardcoding a SaaS grace, refund, quota, or seat policy.
- Accepting invalid shrinks as product defects.
- Use Python standard-library code and fixed records only.
- Do not add a model service, business runtime, generic state engine, or external dependency.

## Deliverables

- Implement the public functions in `commerce_saas.py`.
- Preserve input data and return the contracted diagnostics and values.
- Keep passing and rejecting neighboring cases distinguishable.

## Completion Evidence

- Seven executable assertion methods cover arithmetic, time, identity, and policy.
- Twenty bounded generated quantity/replay combinations challenge conservation.
- A stored three-event counterexample is minimized and replayed.
- Passing, incomplete starter, and duplicate-release control are run separately.
- Report the exact candidate and assertion results, including proof limits.
