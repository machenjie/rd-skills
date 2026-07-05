# Security Checks

## Threat Surface

Status fallthrough can incorrectly permit behavior intended for another state.

## Required Checks

- Reject unexplained fallthrough between status cases.
- Fail if public status names change without compatibility review.

## Rejection Cases

- Reject warning suppression without behavior clarification.
- Reject suspended status taking active behavior.

