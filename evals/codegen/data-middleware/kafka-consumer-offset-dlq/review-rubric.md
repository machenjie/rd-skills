# Review Rubric

## Passing Standard

The implementation must satisfy the benchmark behavior, prove the duplicate and poison-message rejection paths, and keep Kafka delivery evidence reviewable from executable checks.

## Scoring

- 30 percent correctness for manual commits, idempotency, retries, and DLQ behavior.
- 25 percent safety for durable side effects, replay, and partition blocking.
- 20 percent test evidence that runs through the benchmark scripts.
- 15 percent maintainability of the consumer boundary and metadata.
- 10 percent documentation or operational evidence for future reviewers.

## Automatic Failure Conditions

- enable.auto.commit=true for business-critical processing.
- Ack/commit before durable write.
- Infinite immediate retry.
- No DLQ replay procedure.

## Reviewer Notes

Reward solutions that keep processing semantics explicit while making failure handling observable. Penalize broad rewrites that remove the Kafka signal or rely on manual inspection instead of executable checks.
