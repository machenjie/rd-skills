# Security Privacy Evidence Patterns

Use this reference when a security or privacy gate needs evidence that can support a severity decision, block condition, or accepted residual risk. Load only the rows matching the reviewed trust boundary.

## Evidence Map
- **Authorization or tenant isolation:** capture actor/object matrix, owner-derived identity, denied cross-user or cross-tenant test, same-pattern scan scope, command, exit code, and residual bypass risk.
- **Input/output, injection, SSRF, or file boundary:** prove canonicalization, allowlist or schema, context encoding, malicious-input tests, no-fetch-before-deny behavior, sandboxing, and redacted errors/logs.
- **Secrets or credentials:** prove secret scan output, storage boundary, rotation owner, log/container/CI exposure check, revocation status, and residual propagation risk.
- **Dependency, supply-chain, or IaC/cloud change:** prove scanner or policy command, report artifact, effective permission or exposure diff, Critical/High disposition, rollback path, and exception owner.
- **Privacy or compliance change:** prove data classification, minimization, retention, lawful basis or control objective, evidence owner, freshness date, exception, and audit-ready packet.
- **AI/RAG or tool-action boundary:** prove tool allowlist, permission-aware retrieval, prompt-injection or exfiltration red-team cases, output validation, sandbox/action class, and redaction rule.

## Evidence Rules
- Every accepted evidence item names command or validator, report artifact, exit code when runnable, severity/control basis, freshness, and the exact risk it proves or rules out.
- Every evidence item also states what it does not prove: third-party environment posture, unknown tenants, undiscovered gadget chains, untested prompts, or production-only IAM inheritance.
- Prefer existing SAST, dependency, secret, IaC, authz, and abuse-case tests before adding new scanners or broad manual checklists.
- Do not close Critical or High risk on compensating control language alone; require fix evidence or explicit approved remediation with owner and release consequence.
