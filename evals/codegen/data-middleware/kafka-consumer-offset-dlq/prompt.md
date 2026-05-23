# Benchmark Prompt

## Task

Implement a focused change that makes Kafka consumer processing safe for at-least-once delivery with manual offset commits, bounded retries, DLQ handling, and lag alerting.

## Context

The starter repo represents a Kafka consumer group where poison messages block a partition and offset commits are not tied to durable side effects. The implementation should keep the consumer small while making retry and replay behavior explicit.

## Requirements

- Commit offsets only after durable side effects succeed.
- Make duplicate delivery idempotent.
- Send poison messages to a DLQ topic after bounded attempts.
- Expose consumer lag and DLQ depth alerts with replay metadata.

## Constraints

- Do not use `enable.auto.commit=true` for business-critical processing.
- Preserve ordering assumptions in the primary topic unless the implementation documents why they do not apply.
- Do not replace the benchmark with documentation-only output.
- Avoid any network dependency; scripts must run locally from the starter repo.

## Deliverables

- Source changes in the starter repo that implement the requested Kafka consumer behavior.
- Tests or executable checks that prove the required behavior and denial paths.
- A short implementation note describing important tradeoffs and residual risk.

## Completion Evidence

- `bash setup.sh`
- `bash ../test-suite/run.sh`
- `bash ../security-checks/run.sh`
- Review evidence that no automatic failure condition applies.
