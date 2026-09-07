# Observability and Privacy

Use this Reference only for the named BigData observability-and-privacy decision.

## Decision Rules

- Select freshness, lag, volume, bad-record, task-failure, state or partition growth, replay or backfill progress, correction-debt, quality-drift, or cost signals for the named pipeline decision. Bound labels. When a signal triggers an operational response, name its alert owner and recovery action.
- Apply data classification to samples, logs, dead-letter or quarantine records, temporary storage, exports, and human-review or evaluation stores. Applicable policy and debugging needs determine access, retention, deletion, masking, tokenization, isolation, or exclusion.
