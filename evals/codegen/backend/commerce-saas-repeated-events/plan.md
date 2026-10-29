# Implementation Plan

1. Validate event identity and domain before reducing the bounded record list.
2. Separate resource, financial, subscription, entitlement, and usage calculations.
3. Compare conservation and temporal outcomes with independent tests.
4. Shrink a deliberately faulty repeated-cancel sequence without dropping its reservation precondition.
5. Run passing, starter, and repeated-release control through the existing assertion runner.

These fixtures establish local decision contracts. They do not prove a payment provider, database transaction, live subscription policy, or production concurrency behavior.
