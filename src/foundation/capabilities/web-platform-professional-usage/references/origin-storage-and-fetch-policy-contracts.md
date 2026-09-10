# Origin, Storage, and Fetch Policy Contracts

Use this Reference only for the named origin-storage-and-fetch-policy-contracts decision.

## Decision Rules

- Choose cookies, session storage, durable storage, or caches from origin, partition, credential use, expiry, quota, clearing, account binding, sensitivity, and lifetime.
- Reconcile request mode, credentials, preflight, redirect, cache mode, response exposure, and server policy; CORS is not authorization.
- Bind CSP delivery, disposition, fallback, nonce or hash ownership, and violation telemetry.

Report-only delivery and permissive fallbacks are not enforced protection.
- Keep CSP as defense in depth, not a replacement for output encoding, and prevent state from crossing accounts or outliving its purpose.

Return origin-bound state, fetch and policy settings, failure behavior, draft limits, and residual risk.
