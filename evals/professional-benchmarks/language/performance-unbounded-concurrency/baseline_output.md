The async fan-out is fine.

I will accept unbounded asyncio gather as faster without measurement, omit
concurrency bound and backpressure, and omit event-loop lag or load-test
evidence because async code should be efficient.
