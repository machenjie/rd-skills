---
name: dart-professional-usage
description: "For analysis/task/review agents: use for Dart null safety, Future, Stream, isolate, or cleanup semantics; skip framework labels and non-Dart work."
---

# dart-professional-usage

## Registry Trigger

**Use when**

- Dart nullability, asynchronous errors, stream subscription, isolate messages, or resource completion changes behavior.
- Generated or dynamic boundaries can invalidate static type assumptions.

**Do not use when**

- A Flutter or Dart name appears without a language or runtime decision.
- The change is platform metadata, visual styling, or package policy without Dart semantics.

## Skill Role

Protect Dart value validity, asynchronous ownership, stream contracts, and isolate communication.

## High-Value Rules

- Validate dynamic values, null assertions, and late initialization at their actual runtime boundaries.
- Define the operation that owns Future completion and error observation.
- Distinguish single-subscription and broadcast streams before changing listeners or delivery expectations.
- Await cancellation cleanup when later resource use depends on subscription shutdown.
- Preserve error, done, cancellation, and backpressure behavior through stream transformations.
- Correlate isolate messages with operation identity and current state.
- Reject stale completion when a request, view, or worker generation has changed.

## Anti-Patterns

- Static null safety is treated as validating dynamic input or every forced assertion.
- A Future error is detached from the caller that reports success.
- A second listener is attached to a single-subscription stream.
- A resource is reused or removed before asynchronous cancellation finishes.

## Stop Conditions

- Resolve Future, subscription, and isolate ownership before accepting completion or cancellation behavior.

## Output Contract

- Return nullability, asynchronous error, transfer, and resource-end decisions with outstanding-work evidence.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [async streams and isolates](references/async-streams-and-isolates.md) | targeted | Future failures, stream ownership, isolate ordering, or asynchronous cleanup | styling and platform configuration that preserve Dart runtime behavior | analysis-agent, task-agent, review-agent | decision-record, failure-decision, validation-plan |
