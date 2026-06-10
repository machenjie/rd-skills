---
name: code-review
description: Reviews generated or modified code for correctness, maintainability, boundaries, security, tests, dependencies, naming, error handling, and hallucinated APIs.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "78"
changeforge_version: 0.1.0
---

# Mission

Find and categorize **material defects, security risks, design boundary violations, and test gaps** in generated or modified code before they reach production — grounding every finding in file evidence, test behavior, or reproducible reasoning — so that review is actionable, not ceremonial.

# When To Use

Use this capability when reviewing: a pull-request diff, AI-generated implementation, refactored module, dependency version bump, new API or library integration, database migration, production hotfix, configuration change, infrastructure-as-code diff, test update, generated client/server code from an API contract, or any change that touches security-sensitive, payment, data-integrity, or compliance paths.

# Do Not Use When

Do not use this capability as a **style-only pass**, a broad approval ritual, or a substitute for running the tests and static analysis that prove behavior. Do not use `code-review` as the primary pre-implementation structure designer; use `implementation-structure-design` before coding, `refactoring` for behavior-preserving movement, and `code-review` to assess completed diffs. Do not use it as a substitute for `threat-modeling` when the change introduces an entirely new attack surface.

# Stage Fit

Owns code-review; also gates bug-fix and refactoring output. Per-stage focus:

- **code-review**: severity-classified findings with evidence, security surfaces, test gaps, hallucinated-API check.
- **bug-fix**: confirm minimal diff, same-pattern scan, and regression coverage.
- **refactoring**: confirm behavior preservation and characterization-test coverage.

# Non-Negotiable Rules

- **Every finding is grounded in file evidence**, a contract excerpt, a reproducible scenario, or a named failure mode. "I don't like this" is not a finding.
- **Findings are severity-classified**: Critical (must fix before merge) / High (fix before production) / Medium (fix in sprint) / Low (advisory). Severity is calibrated against *operational and user impact*, not aesthetic preference.
- **Spec compliance is reviewed before code quality.** Stage 1 checks whether the change meets the requirement, acceptance criteria, non-goals, plan task, API/schema compatibility, and old-behavior preservation. Stage 2 reviews structure, naming, reuse, test quality, performance, security, and maintainability, and is entered only after Stage 1 passes. Good code that does not meet the requirement fails Stage 1; "the code is clean" never substitutes for a missing requirement. A reviewer who reads only the diff without the requirement and plan, or an implementer self-reviewing in place of independent review, is a process finding.
- **Security surfaces are always reviewed**, regardless of stated scope: authentication, authorization, input handling, output encoding, secrets, SQL/NoSQL injection, deserialization, SSRF, insecure direct object references, privilege escalation, cryptographic misuse. Not reviewing these is a finding of severity High.
- **Hallucinated APIs and libraries are checked.** AI-generated code often invents method signatures, configuration keys, flag names, and version-incompatible APIs. Every new API call, flag, config key, and library must be confirmed to exist in the project's actual dependency graph and documentation. If it cannot be confirmed: severity High — requires verification.
- **Tests cover changed behavior.** For every material behavioral change: at least one new or modified test asserts the new behavior under normal path, at least one test covers the failure/edge case. Absence of tests for changed behavior is a **High** finding.
- **Error handling is explicit and correct.** Swallowed errors (`catch (_) {}`), misleading successes (`return { ok: true }` on failure), unchecked return values, unhandled promise rejections, and silent fallbacks are findings.
- **No accidental data exposure.** Logs, API responses, error messages, URLs, and headers must not contain PII, secrets, tokens, full stack traces with internal paths, or internal system topology.
- **Boundary violations are architectural findings.** A controller calling a repository directly, a domain object importing a framework, a UI component hitting the database — these are High findings with a named boundary and the rule it violates.
- **Deprecated, vulnerable, or license-incompatible dependencies** introduced by the change are findings.
- **Blocking findings must be resolved or explicitly accepted before merge.** Acceptance requires: justification, owner, and a tracked follow-up. "We'll fix it later" with no ticket is not acceptance.
- **Non-findings on checked high-risk surfaces are stated explicitly** — reviewer confirming "checked auth, no exposure found" is as valuable as a finding.

# Industry Benchmarks

Use severity-ranked findings calibrated against secure code review, defect taxonomy, and maintainability benchmarks. Keep the body focused on decision rules; load [references/finding-taxonomy.md](references/finding-taxonomy.md) when a review needs a detailed finding taxonomy, severity calibration, industry benchmark mapping, or examples for borderline findings.

# Selection Rules

Select this capability when **assessing a concrete code change** is primary. Adjacent routing:

- Prefer `refactoring` when reshaping code structure safely without behavioral change.
- Prefer `failure-diagnosis` when a defect has already appeared in production.
- Prefer `test-strategy` when coverage design is unresolved.
- Prefer `threat-modeling` when the change introduces a new attack surface requiring full adversarial modeling.
- Prefer `dependency-vulnerability-scanning` when the question is SCA supply-chain risk across a release.
- Use **with** `security-privacy-gate` for security-sensitive findings requiring formal sign-off.

# Risk Escalation Rules

Escalate when code touches: authentication or session management, authorization checks (any IDOR or missing boundary), payment processing or financial state mutation, cryptographic key generation or handling, data migration (schema or data transform), external integrations (new OAuth flow, new outbound call, new webhook receiver), production configuration or feature flags, AI-generated code with unverified APIs in a critical path, concurrency primitives with money/inventory invariants, or personally identifiable or regulated data flows. Escalate to `security-privacy-gate` when a Critical or High security finding cannot be resolved within the PR.

# Critical Details

Review focuses on **behavior and risk before style**. Key refinements:

- **Hallucination is the most common and most dangerous AI-code defect.** LLMs invent package methods that don't exist, import removed APIs, and fabricate flag constants. Reviewers of AI-generated code must verify every external call. The risk is asymmetric: hallucinated internal helpers cause test failures; hallucinated *security control bypasses* cause breaches.
- **The "no tests changed" signal.** A PR that modifies business logic without touching tests is either (a) covered by existing tests that now implicitly assert the new behavior — prove this, or (b) adding untested behavior — finding.
- **Error handling is a security surface.** Returning HTTP 500 with a full stack trace leaks internal paths and framework versions. Logging an error with the full SQL query logs schema and data. Returning `ok: true` on a write failure leaves the caller with a false belief about system state.
- **Boundary violations compound over time.** One controller→repository shortcut becomes a pattern; a domain object importing an ORM becomes untestable. Name the boundary rule, cite the ADR or layered-architecture-design output, and treat the finding as High.
- **Structure placement is reviewable.** A new helper that duplicates existing semantics, a class that only groups stateless functions, a feature rule in shared utilities, a one-off directory with no boundary, or a public export used by one module is a maintainability finding with concrete remediation.
- **Structure quality findings have severity.** Unreadable main flow, oversized functions/classes/files, mixed responsibilities, side-effect pollution, weak signatures, boolean traps, weakly typed parameter bags, public API overexposure, change-locality violations, poor test structure, stale compatibility branches, feature flags without removal plans, global singleton misuse, service locator misuse, and dependency-injection bloat are review findings when they increase risk.
- **Severity calibration for structure quality:** High when the issue spreads boundary pollution, blocks public-behavior tests, hides behavior risk, or makes a small change modify unrelated modules; Medium when maintainability risk is local to one module; Low when clarity is minor and easily remediated without behavioral risk.
- **Generated code from OpenAPI / gRPC / GraphQL contracts must be regenerated, not hand-edited.** Hand-edited generated stubs diverge from contracts; the review must check whether generated files are regenerated on contract change.
- **Mass assignment.** Any model binding that accepts all request fields without an allowlist can be exploited to set privileged fields (e.g., `is_admin`, `balance`). Check frameworks' mass-assignment protection (Rails `strong_parameters`, Spring `@JsonIgnoreProperties`, Mongoose `strict`).
- **SQL / NoSQL injection.** Even ORMs can be parameterization-bypassed via raw-query escapes, concatenated filters, or JSON operators (`$where` in Mongo). Verify every dynamic query fragment.
- **Race conditions in review.** Optimistic locking missing on a financial balance update, counter increment using `read + write` instead of atomic increment, cache-aside pattern with no stampede protection — these are concurrency findings visible in code without load test.
- **Professional coding details are reviewable defects.** A list that grows from untrusted input, an unbounded `Promise.all`, a missing API page size, a cache with no eviction, or a retry accumulator with no ceiling is not a style nit. It is a production failure mode.
- **Connection lifecycle is code, not infrastructure trivia.** Per-request HTTP clients, per-message SDK clients, DB pools built inside handlers, missing keep-alive, missing idle/lifetime limits, and response bodies not closed all cause latency cliffs, socket exhaustion, and pool starvation.
- **Cleanup paths include error and cancellation paths.** It is not enough to close a file, cursor, stream, timer, subscription, or lock on the happy path. Review the `catch`, `finally`, timeout, early-return, and cancellation branches.
- **Dependency impact.** A new dependency adds transitive dependencies, bundle size (frontend), and attack surface. A `package-lock.json` or `go.sum` change in the PR must be inspected — it is code.
- **IaC diffs need blast-radius assessment.** Changing a security group `0.0.0.0/0`, removing a bucket policy, or enabling public access is a Critical finding in an IaC review even if infrastructure tests pass.
- **Reviewer decisiveness.** A review that leaves every comment as "maybe consider..." is a failed review. Each finding must be: severity, required action, and resolution expectation. Ambiguity delays.
- **Self-review.** An author must not be the sole approver of their own change in high-risk areas. Conflict-of-interest is a process finding.
- **Review window and size.** PRs > 500 lines of changed code have significantly lower defect detection rate (empirical: Rigby & Bird 2013). Recommend splitting; document why if exceptions are made.
- **Non-findings are review evidence.** For security-sensitive reviews, stating "auth path reviewed: no bypass found" creates evidence that the review was substantive.

### Anti-examples

| Anti-pattern | Consequence |
| --- | --- |
| Accept AI-generated code without verifying API calls | Hallucinated method ships; fails in production or worse, silently no-ops |
| Review comments only on formatting | Behavioral regression, IDOR, missing test all ship undetected |
| "Looks good to me" on a migration with no down path | Unrecoverable schema change; incident during deploy |
| `catch (e) {}` accepted without comment | Silent failure hides data corruption for months |
| `console.log(user)` accepted in prod code | PII in log aggregator; GDPR breach |
| New dependency added, `package-lock.json` not inspected | Malicious transitive package added; supply-chain attack vector |
| High finding accepted with "we'll fix it next sprint" and no ticket | Never fixed; ships to production |
| Test changed to match broken behavior | Test now passes, defect still exists |

# Failure Modes

- Review comments focus on formatting while a behavioral regression, security bypass, or hallucinated API ships.
- AI-generated method calls are accepted without checking the project's actual dependency graph.
- Security surfaces (auth, authz, injection, data exposure) not reviewed because "it's not in scope of this PR."
- Tests assert implementation details (specific method calls) rather than observable behavior — passing regardless of the bug.
- Error handling swallows exceptions; production failures are silent; monitoring sees nothing.
- PII or secrets logged; discovered during security audit or incident.
- `try/catch` silently returns success on a write failure; downstream consumers assume consistency they do not have.
- Blocking finding accepted with "we'll fix later" and no ticket; ships in the next deploy.
- Boundary violation approved; pattern propagates across the codebase; architecture becomes unmaintainable.
- Structure placement drift approved; duplicate helpers, speculative classes, mixed-responsibility files, polluted shared utilities, and accidental public APIs accumulate across the codebase.
- Unreadable main flow is approved because tests pass; the next bug fix changes the wrong branch.
- A feature flag ships without owner or expiry and leaves old and new behavior tangled in the same function.
- Test helpers become a shared dumping ground for business fixtures, hiding module ownership and making tests hard to delete.
- Mass assignment accepted; attacker sets `is_admin: true` via unguarded field.
- IaC diff approved without blast-radius review; security group opens 0.0.0.0/0 to production DB.
- Generated code (OpenAPI stubs) hand-edited rather than regenerated; contract drift accumulates silently.
- Unbounded array/list/map/buffer accepted from request body, query `limit`, provider response, or database result; memory grows with attacker-controlled input.
- HTTP/DB/SDK client constructed inside a request loop; connection reuse is lost; sockets and TLS handshakes spike under load.
- Response body, cursor, stream, or subscription not closed on non-2xx/error/cancellation path; pool slots leak until requests fail.
- Review performed on a 1000-line PR in 5 minutes; defect detection rate near zero.
- Self-review on security-sensitive path; conflict of interest unaddressed.
- No stated non-findings on checked surfaces; review provides no evidence it was substantive.

# Reference Loading Policy

Read `references/checklist.md` when the diff is AI-generated, security-sensitive, cross-module, dependency-changing, migration/release-sensitive, or when review findings depend on a surface-specific checklist. Do not load it for a tiny local diff where spec compliance, changed behavior, and validation evidence are already obvious from the patch and tests.

# Output Contract

Return a code review report with, per finding:

- `finding_id` (stable within review)
- `severity` (Critical / High / Medium / Low)
- `surface` (correctness / security / API-hallucination / error-handling / data-exposure / tests / boundary / structure-placement / clarity-maintainability / concurrency / dependency / performance / config-infra)
- `file`, `line_range` (or logical unit if multi-file)
- `description` (what is wrong, evidence)
- `impact` (operational/security/user consequence if not fixed)
- `reproduction` (steps or scenario that triggers the defect)
- `required_remediation` (specific fix or acceptable alternatives)
- `test_gap` (what test would catch this)
- `resolution` (open / accepted-with-ticket:TICKET-N / resolved)

Plus a review summary with:
- `explicit_non_findings` (high-risk surfaces checked, no issue found — per surface)
- `blocking_count` (Critical + High unresolved)
- `spec_compliance_result` (Stage 1 pass/fail, naming the requirement, acceptance criterion, non-goal, or compatibility gap that fails)
- `code_quality_result` (Stage 2 result, recorded only after spec compliance passes)
- `re_review_required` (which stage must be re-reviewed after a fix)
- `approval_scope` (what the approval covers and what it explicitly does not)
- `overall_status` (Approved / Approved-with-conditions / Changes-required / Blocked)
- `owner` (reviewer identity)

# Evidence Contract

Close a code review only when the output states the reviewed requirement/non-goal, diff boundaries, high-risk surfaces checked, severity rationale, reuse/placement issues, validation commands or not-verified disclosure, explicit non-findings, what evidence proves, what it does not prove, residual risk, and re-review or next gate. A "LGTM" or style-only pass is not review evidence.

# Quality Gate

The review is complete only when:

1. Security surfaces (auth, authz, injection, data exposure, crypto) have been explicitly checked and either findings raised or non-findings stated.
2. Every new API call, library, and config key in AI-generated code is confirmed to exist in the project's actual dependency graph.
3. All material behavioral changes have at least one passing test; absence is a High finding.
4. All Critical and High findings are either resolved or have a named acceptance decision with a tracked ticket.
5. Error handling paths are reviewed for swallowed errors and misleading success responses.
6. No PII/secret exposure in logs, URLs, response bodies, or error messages.
7. All blocking findings have explicit resolution status before approval.
8. Review summary states non-findings on high-risk surfaces.
9. Growth surfaces, client/pool lifecycle, and cleanup paths are reviewed whenever code touches bulk data, external calls, async work, caches, files, cursors, streams, or long-lived handles.
10. Structure placement is reviewed whenever code adds functions, classes, files, directories, components, hooks, services, repositories, adapters, helpers, utilities, imports, or exports.
11. Code clarity and maintainability are reviewed whenever the diff adds branch-heavy flow, long functions/classes/files, boolean flags, weakly typed bags, fallback or compatibility paths, feature flags, shared test helpers, public exports, or cross-module edits.
12. Feature flags, deprecated APIs, dead code, and compatibility branches have owner and removal evidence or receive a finding.
13. Stage 1 spec compliance (requirement, acceptance criteria, non-goals, plan, API/schema compatibility, old-behavior preservation) passed before Stage 2 code-quality approval; out-of-order review or implementer self-review in place of independent review is a process finding.

# Used By

- ai-code-review-refactor
- quality-test-gate

# Handoff

Hand off to `refactoring` for safe structural changes following findings; `security-privacy-gate` for Critical/High security findings requiring formal sign-off; `test-strategy` for coverage gaps identified in review; `failure-diagnosis` for unresolved production failures; `threat-modeling` for new attack surfaces; `dependency-vulnerability-scanning` for supply-chain risk from new dependencies.

# Completion Criteria

The capability is complete when the reviewed change has **evidence-backed, severity-classified findings on every material defect and every checked high-risk surface, all blocking findings are resolved or accepted with accountability, and the approval decision is unambiguous** — including explicit non-findings on the security surfaces that were checked.
