# Security Checks

## Threat Surface

Order cancellation is a mutating operation and must preserve authorization,
tenant ownership, and transaction boundaries.

## Required Checks

- Authorization remains inside the service workflow before mutation.
- Deadline failure does not leak unrelated internal order state.
- Shared utilities do not become an alternate path around order authorization.

## Rejection Cases

Reject implementations that bypass OrderService, skip authorization regression
coverage, or move order business checks into generic shared utilities.
