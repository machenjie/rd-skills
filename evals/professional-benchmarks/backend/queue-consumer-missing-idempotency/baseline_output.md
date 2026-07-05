The consumer should just catch exceptions and retry the message.

At-least-once delivery is expected from the queue, so duplicates are unlikely in normal operation. We can commit offsets after reading the message and rely on retry if the provider sends it again.

No DLQ or replay work is needed for this small handler.
