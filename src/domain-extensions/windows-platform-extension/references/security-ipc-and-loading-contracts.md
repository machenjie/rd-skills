# Security, IPC, and Loading Contracts

Load this Reference only when UAC, AppContainer, DPAPI, Credential Manager,
named pipes, single-instance IPC, or DLL loading changes the decision.

Official Microsoft Learn pages below were accessed on 2026-07-24.

## Trust Decision

- Record caller and server principals, integrity levels, sessions, package
  identities, elevation state, container capabilities, and authorization checks.
- Prefer least privilege; separate elevation from identity and never treat an
  administrator token as application-level authorization.
- Bind DPAPI or Credential Manager data to user/machine scope, account lifecycle,
  migration, logout, password reset, unavailable profile, and recovery.
- Version and authenticate named-pipe or single-instance messages; constrain
  endpoints and reject cross-session, stale, oversized, or malformed input.
- Resolve DLLs only from explicit trusted locations with verified module path
  and architecture.

## Primary Sources

- [User Account Control](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/user-account-control/)
- [AppContainer isolation](https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation)
- [CryptProtectData](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata)
- [Credentials Management](https://learn.microsoft.com/en-us/windows/win32/secauthn/credentials-management)
- [Named Pipes](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipes)
- [DLL security](https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-security)

## Source Limits

These rolling pages do not establish repository threat boundaries, ACLs,
capabilities, recovery policy, enterprise controls, loaded dependency paths,
or penetration evidence.
