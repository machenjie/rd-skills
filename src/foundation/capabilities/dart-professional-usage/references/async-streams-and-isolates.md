# Dart Async, Streams, and Isolates

Load for Future failures, stream ownership, isolate ordering, or asynchronous cleanup.
Skip styling and platform configuration that preserve Dart runtime behavior.

## Decision Rules

- Validate values entering through `dynamic`, generated bridges, and external serialization.
- Trace a Future's successful and failed completion to an observer.
- Distinguish waiting for a Future from canceling the underlying work.
- Establish each stream's subscription count, event retention, ordering, and pause behavior.
- Preserve error and done delivery when combining or transforming streams.
- Wait for `StreamSubscription.cancel()` when cleanup must finish before the next operation.
- Close controllers and subscriptions through their actual owners.
- Bind isolate messages to request identifiers and a worker generation where restarts matter.
- Handle late replies, terminated workers, and sender failures without accepting stale results.
- Transfer supported values according to the target runtime's message contract.

## Failure Probes

| Probe | Required distinction |
|---|---|
| Null enters a dynamic boundary | Validation precedes a forced assertion |
| Another listener joins a single-subscription stream | Subscription behavior remains explicit |
| A file is deleted immediately after cancellation | Removal waits for relevant cleanup completion |
| An old isolate reply arrives after a new request | Old work cannot overwrite current state |
| Worker terminates before replying | The operation reaches a bounded failure or recovery outcome |
| Stream emits error before done | Consumer observes failure and releases resources |

## Source Limits

- Independent isolate memory does not eliminate business ordering races.

## Sources

- [Dart null safety](https://dart.dev/null-safety/understanding-null-safety)
- [Dart streams](https://dart.dev/libraries/async/using-streams)
- [Subscription cancellation](https://api.dart.dev/dart-async/StreamSubscription/cancel.html)
- [Dart concurrency](https://dart.dev/language/concurrency)
