# Security Output And Gates

Load this reference when `security-privacy-gate` needs the full output field list, exhaustive quality gate, or detailed handoff table. The skill body keeps default runtime context compact.

## Output Contract
Return a security and privacy review with:
- **Mode selected**: new sensitive surface, modify existing security logic, bug fix, review, dependency/secret/config, or AI/RAG security, with trigger signal.
- **Boundaries inspected**: trust boundaries, object authorization points, tenant filters, input/output contexts, secrets, dependencies, cloud/IaC policies, AI/RAG tool and retrieval boundaries, and audit boundaries inspected or skipped with reason.
- **Professional judgment**: abuse path, control sufficiency, severity, compensating control, and risks ruled out or retained.
- **Risk inventory**: identified vulnerabilities with CWE classification, severity (Critical/High/Medium/Low), and affected code locations.
- **Authorization audit**: object-level authorization analysis for every data access, with IDOR test requirement.
- **Input/output analysis**: trust boundary input validation coverage and output encoding context analysis.
- **Injection risk assessment**: SQL, command, template, SSRF, prompt injection, present or absent with evidence.
- **Secrets audit**: all credentials confirmed in secrets management with rotation schedules.
- **Dependency CVE report**: new and updated dependencies with CVE status and remediation for critical/high findings.
- **Privacy impact**: personal data processed, legal basis, retention, and minimization assessment.
- **Cloud governance review**: cloud IAM escalation, public bucket exposure, SG/NACL/WAF/DNS/CDN/gateway exposure, KMS key policy, account/project boundary, and resource tagging risks.
- **Compliance evidence**: control objective, evidence artifact, control owner, evidence owner, exception owner, evidence freshness, retention period, and audit-ready packet status.
- **Tool permission/sandbox review**: shell/connector/MCP/scanner/IaC/secret-bearing action class, permission state, sandbox boundary, dry-run or revert path, network write scope, and redaction rule.
- **Reuse and placement rationale**: why each authz, validation, encoding, secret, dependency, AI/RAG, or audit control belongs at the selected boundary.
- **Behavior preservation**: existing permissions, tenant isolation, privacy promises, secret lifecycle, dependency posture, and audit controls preserved or intentionally changed.
- **Required fixes**: all Critical and High findings are blocking; fixes are required before merge.
- **Compensating controls**: for accepted residual Medium/Low risks, documented mitigating controls.
- **Validation evidence**: SAST/dependency/secret/authz/IDOR/AI red-team or manual review evidence, what it proves/does not prove, residual risk, and next gate.
- **Evidence limits**: what automated scans, negative tests, policy diffs, or manual reviews prove and what abuse paths, environments, or third-party assessments remain unproven.
- **Gate decision**: Approved / Blocked / Conditionally approved with conditions specified.

## Quality Gate
1. Every data access endpoint has object-level authorization with a cross-user IDOR test.
2. All SQL queries use parameterized queries or ORM methods; no string-interpolated SQL.
3. All user-controlled output is encoded for its rendering context (HTML, JSON, URL).
4. All state-changing browser-facing endpoints have CSRF protection.
5. No user-controlled URLs are used in outbound requests without allowlist validation.
6. All secrets are in a managed secrets service; none in source code, logs, or environment variable printing.
7. All new dependencies have passed CVE scan with no critical/high findings.
8. PII is handled with documented legal basis, minimized, and excluded from logs.
9. AI/LLM prompt injection risk is assessed; model outputs are treated as untrusted.
10. All Critical and High findings are resolved or have approved remediation plans before merge.
11. Cloud IAM, public exposure, network exposure, and KMS policy changes are reviewed against effective policy and least privilege.
12. Regulated changes include control, evidence, owner, exception, freshness, and retention metadata.
13. Risky shell, connector/MCP, scanner, IaC, secret-bearing, network-write, and destructive actions have tool permission/sandbox evidence before execution or approval.

## Handoff
- **backend-change-builder**: implementation of authorization checks, input validation, parameterized queries, and CSRF protection.
- **frontend-change-builder**: XSS prevention, CSP configuration, and secure token handling.
- **integration-change-builder**: webhook signature verification, credential rotation, and OAuth security.
- **data-api-contract-changer**: privacy-by-design obligations affect data model or API contract design.
- **reliability-observability-gate**: security log events, audit trail, and anomaly detection alert requirements.
- **quality-test-gate**: IDOR test obligations, security regression tests, and dependency scan CI integration.
- **change-documentation-gate**: control mapping, audit evidence packet, security advisory, customer notice, or exception documentation.
- **delivery-release-gate**: approval evidence, deploy audit event, artifact digest, and regulated release sequencing.
