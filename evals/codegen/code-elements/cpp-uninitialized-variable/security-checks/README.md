# Security Checks

## Threat Surface

Undefined behavior from uninitialized reads can bypass status checks.

## Required Checks

- Reject warning suppression instead of initialization.
- Fail if status behavior changes without compatibility review.

## Rejection Cases

- Reject uninitialized reads in any branch.
- Reject global state added for a local branch defect.

