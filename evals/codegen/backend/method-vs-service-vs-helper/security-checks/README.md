# Security Checks

## Threat Surface

Order cancellation is permission-sensitive because a misplaced helper can bypass
authorization or transaction sequencing.

## Required Checks

- Authorization is preserved in the service flow before cancellation mutation.
- No shared utility exposes a public cancellation bypass path.
- Repository writes remain behind the existing service boundary.

## Rejection Cases

Reject implementations that move permission-sensitive cancellation decisions to
public helpers, bypass authorization, or make a helper callable from unrelated
modules without the existing service guard.
