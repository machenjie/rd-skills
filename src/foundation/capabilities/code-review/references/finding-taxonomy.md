# Code Review Finding Taxonomy

Load this reference only when a review needs detailed finding taxonomy, severity calibration, industry benchmark mapping, or examples for borderline findings. Do not load it for ordinary L1/L2 review guidance.

## Industry Benchmarks

- Use **OWASP Code Review Guide v2**, **OWASP ASVS v4**, **Microsoft SDL Code Review**, and **SAFECode Fundamental Practices** section 4.3 for secure review practice.
- Use **OWASP Top 10 2021**, **OWASP API Security Top 10 2023**, and **CWE Top 25 2024** for vulnerability taxonomy and precise defect naming.
- Use **Google Engineering Practices - Code Review Guide** and **Conventional Comments** for reviewer etiquette and structured comments.
- Use **NIST SP 800-218 SSDF** Verify tasks and **A Practical Guide to Static Analysis** for verification and SAST context.
- Use **SonarQube**, **Semgrep**, and **CodeQL** taxonomies for automated finding classification.
- Use **Architecture Decision Records** for boundary-rule references.
- For AI-generated code, inspect known generation failures such as invented APIs, missing null checks, error propagation defects, and version mismatch.

## Severity Classification

| Severity | Definition | Merge policy |
| --- | --- | --- |
| **Critical** | Reachable consequence threatens catastrophic compromise, irreversible data loss or corruption, or equivalent safety or availability impact under current exposure and recovery limits. | Follow current release policy; normally block while the consequence remains reachable without authoritative acceptance. |
| **High** | Reachable consequence causes material user, contract, security, data, or availability harm with significant exposure or difficult recovery. | Follow current policy; require correction or accountable acceptance before the affected exposure. |
| **Medium** | Reachable defect has bounded impact, exposure, or reversibility, or creates material maintainability or operational risk. | Correct or track with a named owner and due condition according to policy. |
| **Low** | Evidence supports a localized clarity, style, or minor efficiency concern without demonstrated operational consequence. | Advisory unless current policy assigns a stronger consequence. |
| **Non-finding** | High-risk surface explicitly checked and no issue found | Stated explicitly in review |

Severity follows reachable consequence, exposure, reversibility, evidence confidence, and current review or release policy. Test and validation status support reachability and confidence; they do not set severity alone.

## Code Review Checklist By Surface

| Surface | Key checks |
| --- | --- |
| **Correctness** | Logic errors; off-by-one; wrong operator; incorrect nullability; branch coverage of changed paths; edge cases named in requirements |
| **Security** | Injection (SQL/NoSQL/command/LDAP/header/template); auth bypass; IDOR/BOLA; mass assignment; insecure deserialization; SSRF; open redirect; cryptographic misuse; secrets hardcoded or logged |
| **API / Hallucination** | For each new or changed external surface in the reviewed diff, verify the API call and method signature against the project's actual dependency version, and verify configuration keys, flags, and library presence against current project or provider evidence; treat an inaccessible or unverified surface as residual review risk or a finding. |
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
├─ Yes → Apply the relevant specialist checklist and establish consequence, exposure, and recovery evidence.
Does the change include AI-generated code?
├─ Yes → Verify every new API call, config key, flag, and external call against project deps.
│         Treat unverifiable scope as an evidence gap or finding under current policy and reachable consequence.
Are there failing or missing tests for changed behavior?
├─ Yes → Identify the unproved behavior and consequence; use test state to calibrate confidence, not severity alone.
Does current review or release policy classify a supported finding as blocking?
├─ Yes → Return it for correction or authoritative risk acceptance.
No blocking findings AND high-risk surfaces explicitly checked?
└─ Approve with stated non-findings.
```
