# Security Checks

## Threat Surface

Payment creation touches customer identifiers, payment source tokens, provider
metadata, idempotency keys, logs, and retry behavior. Duplicate side effects
and sensitive log exposure are the highest risk areas.

## Required Checks

- Reject missing, empty, overlong, or malformed idempotency keys.
- Hash or normalize payload comparison without storing unnecessary sensitive fields.
- Redact payment source tokens and provider secrets from logs and errors.
- Verify conflict responses do not reveal another customer's payment details.
- Confirm audit records are immutable enough for reconciliation review.

## Rejection Cases

- Any solution that stores full card, token, or secret values in application logs.
- Any solution that allows a repeated key from one customer to read another customer's result.
- Any solution that makes provider retry behavior non deterministic under timeout.