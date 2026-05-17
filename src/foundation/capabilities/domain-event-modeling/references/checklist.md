# Domain Event Modeling Checklist

- Name each event as a past-tense domain fact.
- Define producer and commit point.
- Define consumers and their side effects.
- Define payload fields, stable identifiers, and schema version.
- Define idempotency key and duplicate handling.
- Define ordering expectations and partition or aggregate key.
- Define retry, backoff, and dead-letter behavior.
- Define audit, privacy, and retention impact.
- Distinguish domain, integration, notification, audit, and analytics events.
- Map events to producer, consumer, contract, and failure tests.
