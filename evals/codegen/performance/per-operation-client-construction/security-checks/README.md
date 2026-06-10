# Security Checks

## Threat Surface

Client lifecycle defects can exhaust sockets, hide retry storms, and leak
resources or credentials through failed upstream calls.

## Required Checks

- Reject response body or stream leaks on non-2xx and exception paths.
- Verify timeout and cancellation cleanup.
- Reject hidden network IO that bypasses integration security checks.

## Rejection Cases

- Reject per-operation client construction.
- Reject missing response cleanup.
- Reject hidden network IO behind repository or adapter without timeout.
