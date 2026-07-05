# Code Review Finding Taxonomy

Load this reference only when a review needs detailed finding taxonomy, severity calibration, industry benchmark mapping, or examples for borderline findings. Do not load it for ordinary L1/L2 review guidance.

## Industry Benchmarks

Anchor against: **OWASP Code Review Guide v2** and **OWASP ASVS v4** for security checklist (V1 architecture, V2 auth, V3 session, V4 access control, V5 input validation, V6 crypto, V7 error handling, V10 malicious code); **OWASP Top 10 2021** and **OWASP API Security Top 10 2023** for vulnerability taxonomy. **CWE Top 25 Most Dangerous Software Weaknesses 2024** for precise defect naming. **Google Engineering Practices - Code Review Guide** for reviewer-author etiquette (author clarity, reviewer decisiveness, finding priority framing). **Microsoft SDL Code Review** for security-focused checklist. **"A Practical Guide to Static Analysis" (Chess & West)** for SAST integration context. **NIST SP 800-218 SSDF** Verify tasks (PW.7, PW.8) for security code review as a practice. **SAFECode Fundamental Practices for Secure Software** section 4.3. **SonarQube / Semgrep / CodeQL** rule taxonomies for automated finding classification. **"Clean Code" (Martin) / "Refactoring" (Fowler)** for maintainability and naming vocabulary. **ADR (Architecture Decision Records)** for boundary rule reference. **Conventional Comments** spec for structured review comment format. For AI-generated code specifically: **GitHub Copilot / Cursor / Codeium** known generation failure modes (hallucinated APIs, missing null checks, incorrect error propagation, version mismatch).

## Severity Classification

| Severity | Definition | Merge policy |
| --- | --- | --- |
| **Critical** | Exploitable security vulnerability; data corruption; system compromise; production data loss | **Block merge** |
| **High** | Unhandled failure mode causing outage; missing auth/authz check; hallucinated API; logic error with user impact; missing test for changed behavior | **Block merge**; fix or named acceptance with ticket |
| **Medium** | Maintainability risk; missing edge-case coverage; suboptimal but not incorrect; dependency risk | Fix within sprint; tracked |
| **Low** | Style, naming, minor optimization, advisory; no operational impact | Advisory; author's discretion |
| **Non-finding** | High-risk surface explicitly checked and no issue found | Stated explicitly in review |

## Code Review Checklist By Surface

| Surface | Key checks |
| --- | --- |
| **Correctness** | Logic errors; off-by-one; wrong operator; incorrect nullability; branch coverage of changed paths; edge cases named in requirements |
| **Security** | Injection (SQL/NoSQL/command/LDAP/header/template); auth bypass; IDOR/BOLA; mass assignment; insecure deserialization; SSRF; open redirect; cryptographic misuse; secrets hardcoded or logged |
| **API / Hallucination** | All new API calls exist in project deps at correct version; method signatures match; config keys exist; flags documented; no invented library |
| **Error handling** | No swallowed errors; no misleading success on failure; structured error returns; retry/timeout set; fallback documented |
| **Data exposure** | PII not logged; stack traces not in user-visible errors; tokens not in URLs; response bodies not over-sharing internal ids |
| **Tests** | Material behavior changes are tested; critical failure paths are tested; tests assert behavior (not implementation internals); no test that passes regardless of code |
| **Boundaries** | No layer violation (controller to repository, UI to database, domain to framework); coupling delta is intentional; imports respect module boundaries |
| **Structure placement** | New functions reuse existing behavior when semantics match; new classes require state/lifecycle/invariants/polymorphism; new files have one owner; new directories represent real boundaries; shared/common/utils are not polluted with business logic; exports are minimal; imports respect dependency direction |
| **Clarity and maintainability** | Main flow readable; oversized functions/classes/files assessed; signatures structured; pure logic separated from side effects; change locality preserved; compatibility and feature flag cleanup planned |
| **Concurrency** | Race conditions; shared mutable state; lock ordering; missing idempotency key; duplicate-submit risk |
| **Dependencies** | No new CVE-impacted package; license compatible with project; version pinned; tree-shaking / bundle impact assessed (frontend) |
| **Performance** | N+1 queries; unbounded collection operations; missing pagination; synchronous blocking in async path; unbounded fan-out; missing caching where contractually warranted |
| **Resource lifecycle** | Per-operation HTTP/DB/SDK client construction; missing connection reuse; response body/stream not closed; timers/listeners/subscriptions/cursors/file handles leaked; pools lacking max size/idle timeout |
| **Config / Infra** | No hard-coded endpoints, resource names, account ids; env-specific config injected not baked; IaC change blast radius assessed |

## Decision Tree: Escalate Vs Accept Vs Approve

```
Does the change touch auth, authz, payments, crypto, regulated data, or migrations?
├─ Yes → Apply security surface checklist before any other review.
│         Finding of Critical or High → Block; do not approve without resolution.
Does the change include AI-generated code?
├─ Yes → Verify every new API call, config key, flag, and external call against project deps.
│         Unverifiable → severity High.
Are there failing or missing tests for changed behavior?
├─ Missing test for material behavior change → High finding.
├─ Failing test in PR → Critical; do not merge.
No blocking findings AND high-risk surfaces explicitly checked?
└─ Approve with stated non-findings.
```
