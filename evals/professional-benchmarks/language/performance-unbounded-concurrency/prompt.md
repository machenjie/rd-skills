Review this Python service change:

The endpoint accepts up to 10,000 customer IDs and starts an unbounded
`asyncio.gather()` fan-out to an upstream API. There is no semaphore, timeout,
backpressure, cancellation propagation, event-loop lag metric, load test, or
pool sizing evidence. The author claims the change is faster because it is
async.
