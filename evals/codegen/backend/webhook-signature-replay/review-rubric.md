# Review Rubric

## Passing Standard

The implementation must fail closed for invalid webhook requests and process
valid provider events once. The verifier, replay store, and shipment update
order must be clear enough to audit.

## Scoring

- 30 percent security correctness for raw body HMAC, timestamp checks, and constant time compare.
- 25 percent idempotency and replay safety for durable event tracking and side effect order.
- 20 percent tests for valid, invalid, stale, duplicate, and configuration failure cases.
- 15 percent operational quality for logs, metrics, and rotation documentation.
- 10 percent maintainability for small verifier and event store boundaries.

## Automatic Failure Conditions

- Shipment state can change before signature verification succeeds.
- Replay protection is process local only.
- Missing signing secret allows requests through.
- Secrets or full signatures are logged.

## Reviewer Notes

Reward implementations that make raw body handling explicit and avoid mixing
provider verification with business state changes. Penalize clever abstractions
that obscure when the side effect actually becomes durable.