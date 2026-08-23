# Authentication Security Checklist

- Identify the IdP, clients/browsers, credential/authenticator types, session/token authority, assurance target, threat model, and applicable policy.
- Define issuance, transport, storage, renewal, privilege change, compromise, revocation, logout, recovery, and audit outcomes only for affected flows.
- When local passwords are stored, prove a maintained purpose-built password hashing or KDF with policy- and latency-derived parameters, excluding fast hashes and custom cryptography.
- For cookie sessions, derive script, transport, cross-site, scope, and lifetime controls from the actual browser, SSO, or embedding flow.
- Verify the intended protection instead of requiring one universal attribute set.
- Select MFA/step-up, refresh rotation/reuse detection, sender constraints, revocation, and recovery controls from assurance, IdP/client capability, replay/takeover risk, UX, and policy.
- Ensure secrets, credentials, tokens, reset links, and session identifiers do not leak through URLs, logs, analytics, crash reports, referrers, or artifacts.
- `analysis-agent` defines attack paths and validation plans and inspects already-existing source/provider/config/test evidence; it does not run dynamic validation.
- `task-agent` runs only accepted post-edit dynamic checks that the changed flow triggers: fixation, replay/reuse, logout/revocation, recovery/linking, enumeration, password verification, callback, or denied step-up.
- `review-agent` independently inspects the actual diff/evidence and runs only host-permitted, non-modifying checks; missing dynamic proof remains an explicit residual exposure.

## Anti-Patterns

- Clearing a client cookie is not revocation when a refresh token or server session remains valid.
- Recovery, email change, federation, or account linking can bypass stronger controls on the primary login path.

## Execution Checklist

1. Map actors, credentials, IdP trust, session/token families, privilege transitions, recovery paths, and compromise events.
2. Verify current provider capabilities, signing/key policy, browser cookie model, revocation store, performance/UX constraints, and applicable organizational policy before choosing controls.
3. Prove reachable attack paths and record untested paths, evidence limits, and residual takeover risk.
