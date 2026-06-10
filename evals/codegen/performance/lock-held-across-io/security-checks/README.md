# Security Checks

## Threat Surface

Stalled locks around IO can create denial-of-service risk and can leave shared
state in ambiguous ownership during timeout.

## Required Checks

- Reject lock scope that spans untrusted network calls.
- Verify timeout and cancellation release resources.
- Reject notification side effects that bypass invariant safety.

## Rejection Cases

- Reject a lock held across network or storage IO.
- Reject missing timeout and cancellation cleanup.
- Reject deadlock-prone lock ordering.
