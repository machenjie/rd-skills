# Secret Configuration Security Checklist

- Identify secrets, credentials, certificates, keys, and production-sensitive config.
- Confirm real secrets are not committed, logged, documented, exposed to frontend, or embedded in images.
- Define approved storage, access scope, audit, owner, and break-glass process.
- Define rotation, revocation, rollout order, and old-secret retirement.
- Validate safe defaults, required environment variables, and fail-closed behavior.
- Review CI, build, container, logs, metrics, traces, and support-tool exposure paths.
- Use placeholders in docs and examples.
- Test missing config, wrong config, redaction, and rotation behavior.
