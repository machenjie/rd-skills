# Message Queue Design Checklist

- Define producers, queues or topics, consumers, and message schema.
- State delivery guarantee, acknowledgement point, and ordering scope.
- Define idempotency keys and duplicate-message behavior.
- Define retryable, non-retryable, delayed, and poison message handling.
- Define retry backoff, max attempts, dead-letter routing, and replay criteria.
- Define backpressure behavior for producers and consumers.
- Define observability for lag, age, throughput, failures, retries, and dead letters.
- Test duplicate, delayed, out-of-order, failed, dead-letter, and replay paths.
