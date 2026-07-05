# Security Checks

## Threat Surface

Tenant invitation lookup can expose membership existence or allow unauthorized
invite actions when tenant access validation is bypassed.

## Required Checks

- Tenant access validation remains server-side and is reused from the tenant module.
- Unauthorized tenant principals cannot trigger invite lookup or send effects.
- Error handling does not reveal whether an email already has an invitation.

## Rejection Cases

Reject solutions that move tenant authorization into generic utils, skip tenant
access denial tests, or expose invitation existence through distinct errors.
