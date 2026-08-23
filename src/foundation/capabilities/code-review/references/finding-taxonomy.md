# Code Review Finding Taxonomy

Load this reference only when a review needs detailed finding taxonomy, severity calibration, industry benchmark mapping, or examples for borderline findings. Do not load it for ordinary L1/L2 review guidance.

## Industry Benchmarks

- Secure-review and taxonomy sources: **OWASP Code Review Guide v2**, **OWASP
  ASVS v4**, **OWASP Top 10 2021**, **OWASP API Security Top 10 2023**,
  **CWE Top 25 2024**, **Microsoft SDL Code Review**, and **SAFECode
  Fundamental Practices** 4.3.
- Review and evidence sources: **Google Engineering Practices - Code Review
  Guide**, **Conventional Comments**, **NIST SP 800-218 SSDF**, **A Practical
  Guide to Static Analysis**, **SonarQube**, **Semgrep**, **CodeQL**, and
  **Architecture Decision Records**.
- AI-generated surfaces include invented APIs/configuration, version mismatch,
  null/error propagation gaps, and unsupported assumptions.

## Severity Classification

| Severity | Definition | Merge policy |
| --- | --- | --- |
| **Critical** | Catastrophic reachable consequence, irreversible loss/corruption, or equivalent safety/availability harm under current recovery limits. | Follow current policy; normally block absent authoritative acceptance. |
| **High** | Material reachable user, contract, security, data, or availability harm with significant exposure or difficult recovery. | Correct or obtain accountable acceptance under current policy. |
| **Medium** | Bounded impact/exposure/reversibility or material maintainability/operational risk. | Correct or track with owner and due condition. |
| **Low** | Localized concern without demonstrated operational consequence. | Advisory unless current policy says otherwise. |
| **Non-finding** | Named high-risk surface checked with no supported defect. | Record explicitly with proof limits. |

Severity follows reachable consequence, exposure, reversibility, evidence
confidence, and current policy. Tests affect reachability confidence; they do
not set severity alone.

## Code Review Checklist By Surface

| Surface | Key checks |
| --- | --- |
| **Correctness / contract** | Logic, invariant, error, compatibility, boundary, side-effect, and observable-output preservation. |
| **Security** | Injection, authorization, tenant/data exposure, deserialization, SSRF/redirect, cryptography, and secret handling. |
| **API / Hallucination** | Verify API/signature/version plus config keys, flags, dependency presence, and provider behavior from current source; inaccessible claims remain a finding or evidence gap. |
| **Concurrency** | Shared state, lock ordering, cancellation, idempotency, duplicate effects, and admissible schedules. |
| **Dependencies** | Vulnerability, license, provenance, version, install-time behavior, and artifact impact. |
| **Performance** | Unbounded work/fan-out, N+1, blocking, pagination, cache contract, and measured resource consequence. |
| **Resource lifecycle** | Client/pool reuse and closure of streams, timers, listeners, cursors, files, sockets, or handles. |
| **Config / Infra** | Target identity, environment separation, hard-coded authority, IaC blast radius, recovery, and secret exposure. |
| **Tests / evidence** | Changed behavior and critical failures proved at the causal boundary; green status alone does not close risk. |

## Approval, Finding, And Evidence Boundary

- Invoke the relevant specialist for auth/authorization, payments, cryptography,
  regulated data, migrations, native systems, or another material domain.
- Report a **finding** only with a reachable violated contract and consequence.
- Report an **evidence gap** when a material surface cannot be verified.

Do not manufacture severity from uncertainty.
- Failing or missing tests lower confidence by naming unproved behavior; test
  state alone neither creates nor erases severity.
- Approve only when current-policy blockers are absent and required high-risk
  surfaces have explicit non-findings and proof limits.
