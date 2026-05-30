# Security Checks

## Threat Surface

Security settings UI can mislead users if reminder state or copy leaks into a
generic shared component without preserving account-security context.

## Required Checks

- Reminder copy remains scoped to the security settings feature.
- No global hook exposes security-state mutation for unrelated features.
- User-visible states do not imply recovery codes were generated when they were not.

## Rejection Cases

Reject implementations that place security-specific rules in common components,
make a generic hook responsible for security state, or hide missing recovery-code
state behind vague props that reviewers cannot audit.
