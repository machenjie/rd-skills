# Security Checks

## Threat Surface

Architecture drift can let UI, API, or generated code bypass authorization, validation, or secret-handling boundaries.

## Required Checks

- Forbidden dependency rules protect security-sensitive layers such as auth, secrets, and persistence.
- Generated code exceptions cannot import privileged runtime modules.
- CI failures cannot be bypassed by local-only scripts.

## Rejection Cases

- Reject architecture rules that allow UI to import secret or persistence internals.
- Fail when generated-code exceptions are broad enough to include handwritten code.
- Reject manual-only enforcement for security boundaries.
