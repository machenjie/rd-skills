# Security Privacy Evidence Patterns

Use this reference when a security or privacy gate needs evidence that can support a severity decision, block condition, or accepted residual risk. Load only the rows matching the reviewed security boundary or privacy lifecycle consequence.

## Evidence Map
- **Authorization or tenant isolation:** capture actor/object matrix, owner-derived identity, denied cross-user or cross-tenant test, same-pattern scan scope, command, exit code, and residual bypass risk.
- **Input/output, injection, SSRF, or file boundary:** identify the actual source, sink, and selected control.
- **Selected input/output controls:** prove applicable validation/canonicalization, parameter binding or contextual encoding, malicious-input denial, and safe errors/logs.
- **Fetch or execution controls:** require no-fetch-before-denial or sandbox evidence only when the reachable boundary needs those controls.
- **Secrets or credentials:** prove secret scan output, storage boundary, rotation owner, log/container/CI exposure check, revocation status, and residual propagation risk.
- **Dependency, supply-chain, or IaC/cloud change:** prove scanner or policy command, report artifact, effective permission or exposure diff, Critical/High disposition, rollback path, and exception owner.
- **Privacy or compliance change:** prove classification, purpose, minimization, retention, deletion, and other affected lifecycle outcomes and individual consequences against supplied policy or control authority with current source and validation.
- **AI/RAG or tool-action boundary:** prove tool allowlist, permission-aware retrieval, prompt-injection or exfiltration red-team cases, output validation, sandbox/action class, and redaction rule.

## Evidence Rules
- Every accepted evidence item names command or validator, report artifact, exit code when runnable, severity/control basis, freshness, and the exact risk it proves or rules out.
- For each security or privacy evidence item used by the gate, state its exact proof scope and any material unproven boundary. Examples include third-party environment posture, unknown tenants, undiscovered gadget chains, untested prompts, or production-only IAM inheritance.
- Prefer existing SAST, dependency, secret, IaC, authz, and abuse-case tests before adding new scanners or broad manual checklists.
- Require fix evidence or explicit approved remediation with owner and release consequence before closing Critical or High risk supported only by compensating-control language.
