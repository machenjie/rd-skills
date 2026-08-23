# Observability and Privacy

Use this Reference only for the named BigData observability-and-privacy decision.

## Decision Rules

- Monitor freshness, lag, volume, bad records, task failure, state or partition growth, replay or backfill progress, correction debt, quality drift, and cost. Each signal has bounded labels, an alert owner, and a recovery action.
- Apply data classification to samples, logs, dead-letter or quarantine records, temporary storage, exports, and human-review or evaluation stores. Applicable policy and debugging needs determine access, retention, deletion, masking, tokenization, isolation, or exclusion.
