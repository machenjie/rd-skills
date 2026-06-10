# Security Checks

## Threat Surface

Async overload can become a denial-of-service vector when CPU work, blocking IO,
or unbounded fan-out monopolizes the event loop.

## Required Checks

- Reject unbounded fan-out from untrusted request size.
- Reject blocking IO that can starve other requests.
- Verify cancellation releases resources on timeout.

## Rejection Cases

- Reject missing request-size or concurrency bounds.
- Reject worker offload that drops cancellation.
- Reject sync file or network IO on the event loop.
