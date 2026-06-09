# Security Checks

## Threat Surface

Order cancellation touches authorization and money-adjacent refund decisions.

## Required Checks

- Authorization remains in service orchestration before order mutation.
- No customer-controlled fields bypass premium or disputed-state authority.
- Logs do not expose sensitive customer or payment data.

## Rejection Cases

- Policy object trusts request body premium status.
- Refund hold is decided after an external side effect already committed.
- Tests omit denied authorization behavior.
