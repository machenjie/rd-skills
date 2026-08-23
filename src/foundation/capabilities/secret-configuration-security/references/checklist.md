# Secret Configuration Security Checklist

- Scope storage and decrypt authority by principal, purpose, operation, environment, tenant, and lifetime; include audit, break-glass, deletion recovery, and inaccessible-consumer ownership where material.
- Separate sensitivity from mechanism: environment variables, encryption, masking, or a managed store do not by themselves prove least privilege, non-exposure, rotation safety, or recovery.
- Escalate security-sensitive defaults or config changes that weaken authentication, transport, authorization, isolation, rate control, or data protection; general config semantics remain with `configuration-runtime-policy`.

- Identify secrets, credentials, certificates, keys, and production-sensitive config.
- Confirm real secrets are not committed, logged, documented, exposed to frontend, or embedded in images.
- Define approved storage, access scope, audit, owner, and break-glass process.
- Define rotation, revocation, rollout order, and old-secret retirement.
- Validate safe defaults, required environment variables, and fail-closed behavior.
- Review CI, build, container, logs, metrics, traces, and support-tool exposure paths.
- Use placeholders in docs and examples.
- Test missing config, wrong config, redaction, and rotation behavior.
