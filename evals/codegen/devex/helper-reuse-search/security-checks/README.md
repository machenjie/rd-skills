# Security Checks

## Threat Surface

Order display names can leak customer or tenant information when formatting
logic bypasses the existing ownership and permission boundary.

## Required Checks

- Display-name code does not bypass server-side order authorization.
- Shared utility code does not gain access to tenant, customer, or order objects.
- Error messages do not reveal hidden customer details for missing records.

## Rejection Cases

Reject solutions that move order/customer business data into shared utilities,
log sensitive customer fields, or expose hidden order state in display labels.