# Security Checks

## Threat Surface

Dependency wiring can leak secrets or bypass credential rotation when clients and global state are unmanaged.

## Required Checks

- Typed configuration binds credentials at the composition root without logging secret values.
- Test overrides cannot point production code to unsafe endpoints.
- Shutdown cleanup does not dump tokens or connection strings.

## Rejection Cases

- Reject hidden service locator access to secrets.
- Fail when global mutable state keeps credentials after test reset.
- Reject wiring that bypasses TLS or provider authentication.
