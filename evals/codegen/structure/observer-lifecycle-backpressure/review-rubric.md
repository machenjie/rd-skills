# Review Rubric

## Passing Standard

The solution passes when event fan-out is explicit, bounded, observable, and
lifecycle-owned, with subscriber failures isolated from the main transaction.

## Scoring

- 30 percent observer/pubsub pattern decision quality.
- 25 percent lifecycle, unsubscribe, shutdown, and cleanup behavior.
- 20 percent backpressure, bounded fan-out, and timeout behavior.
- 15 percent subscriber failure isolation and transaction safety.
- 10 percent metrics, logs, and tests.

## Automatic Failure Conditions

- Unbounded observers or unbounded queue fan-out.
- No unsubscribe or lifecycle cleanup.
- Observer exception breaks main transaction.
- No metrics or logs for subscriber failures or queue health.
- Subscriber network IO runs inside the order transaction.

## Reviewer Notes

Observer is acceptable only when lifecycle and overload behavior are designed.
Direct service calls may be better for simple synchronous obligations.
