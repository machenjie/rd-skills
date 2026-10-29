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

- Check dynamic values, null assertions, and late initialization at their actual runtime boundaries.
- Bind Future completion and error observation to the owning operation.
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

## Targeted References

- No task-local Reference is indexed for this Skill.
