# Authentication Risk Baselines And Patterns

**Load when:** authentication decisions need more detail on password storage, factors, sessions/cookies, refresh/revocation, recovery, federation, or evidence.

**Do not load when:** the root Skill already determines the bounded control, or no authentication lifecycle boundary changes.

Use current threat model, assurance target, IdP/client/browser capability, deployment environment, organization policy, regulatory need, measured latency/capacity, and recovery UX. Standards such as NIST 800-63B, OWASP ASVS/cheat sheets, FIDO/WebAuthn, OAuth/OIDC BCPs, and applicable regulation are evidence sources, not universal mechanism selections.

## Decision Baselines

1. **Local password storage:** use a maintained platform-supported password hashing/KDF with unique salts and policy-plus-capacity-derived parameters instead of fast hashes, reversible storage, or custom cryptography.
2. **MFA and step-up:** select assurance and factor properties from action impact, phishing/replay threat, IdP/client capability, accessibility, recovery, and policy. WebAuthn/passkeys or hardware factors are phishing-resistant candidates; TOTP, push, SMS, or email may be bounded fallback candidates when the accepted assurance and takeover controls permit them.
3. **Session cookies:** protect the actual browser flow from script, transport, cross-site, and scope exposure through an attribute set derived from credentials, SSO or embedding needs, browser support, and CSRF evidence.
4. **Refresh and revocation:** define replay containment, authoritative session or token state, compromise detection, logout, and privilege-change behavior through mechanisms derived from IdP support, client type, revocation latency, storage, and replay threat.
5. **Recovery and federation:** treat reset, email change, account linking, social/federated callback, device trust, and service credentials as alternate authentication paths. Require explicit identity binding, callback/request integrity, least authority, compromise recovery, and notification/audit outcomes proportional to risk.
6. **Password and authenticator policy:** Derive length/screening, rate controls, factor enrollment, fallback, reset, and lifecycle from current policy and threat evidence. Avoid fixed values that ignore IdP behavior, user population, performance, or regulatory constraints.

## Easy-to-Miss Failures

- Client-side logout leaves authoritative refresh/session material replayable.
- Recovery or account linking accepts a weaker identity proof than the primary path.
- Tokens, reset links, raw credentials, or session identifiers leak through URLs, logs, analytics, crash reports, referrers, or build artifacts.
- Federation accepts broad redirects, unpinned verification behavior, stale keys, or ambiguous issuer/audience/client binding.

## Evidence Outcomes

- `analysis-agent` defines the abuse paths and inspects current provider/config/source evidence without executing state-changing attacks.
- `task-agent` runs accepted post-edit fixation, replay/reuse, revocation, recovery, linking, callback, password-verifier, and denied-step-up checks only where triggered.
- `review-agent` independently inspects the actual diff/artifact and runs only permitted non-modifying checks; unavailable dynamic proof remains an explicit exposure limit.
