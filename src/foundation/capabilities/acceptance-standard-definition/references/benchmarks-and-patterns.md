# Acceptance Standard Definition Benchmarks And Patterns

Use this reference when `acceptance-standard-definition` needs benchmark anchors, acceptance-to-validation mapping, graph/memory/execution coupling, rejection-condition depth, or anti-pattern review beyond the inline `SKILL.md` body.

## Benchmark Anchors

| Benchmark | Acceptance implication | Evidence to require |
| --- | --- | --- |
| ISO/IEC/IEEE 29148 | Requirements must be necessary, unambiguous, complete, consistent, feasible, verifiable, and traceable. | Requirement id, trace map, acceptance owner, and explicit ambiguity rejection. |
| Gherkin / BDD | Criteria should state actor, precondition, trigger, observable result, and unacceptable result. | `given`, `when`, `then`, `not_then`, and verification method. |
| INVEST | A criterion should be independent, small, and testable enough to verify without unrelated behavior. | One behavior per criterion and isolated pass/fail evidence. |
| ATDD / Specification by Example | Shared examples prevent stakeholder and implementer interpretation drift. | Concrete examples, boundary values, and reviewed example table. |
| Pact / contract testing | API acceptance must preserve consumer-visible request, response, error, and compatibility behavior. | Contract examples, consumer list, generated-client check, and breakage rule. |
| WCAG | Accessibility acceptance needs specific success criteria and assistive-tech evidence. | WCAG SC id, keyboard/screen-reader procedure, and not-verified disclosure. |
| SRE SLI/SLO | Reliability and performance claims need a measured indicator, threshold, window, and scope. | SLI, percentile or ratio, load/environment, dashboard/query, and owner. |
| OWASP ASVS | Security acceptance must include allowed, denied, abuse, and audit evidence paths. | ASVS control id, denied test, abuse case, audit/log expectation. |

## Acceptance Standard Quality Matrix

| Standard dimension | Strong answer | Weak answer to reject |
| --- | --- | --- |
| Actor | Named role, system, tenant, or external actor. | "The user" when role or permission matters. |
| Preconditions | State, data, permissions, feature flag, environment, and version are stated. | Hidden setup known only to the author. |
| Action | Trigger is observable and includes relevant inputs. | "Works" or "handles" without a trigger. |
| Expected outcome | Measurable behavior, state change, status, or artifact. | Subjective adjective or implementation task. |
| Rejection condition | Observable `not_then` explains how acceptance fails. | No stated unacceptable result. |
| Evidence type | Test id, command, dashboard, log query, screenshot, scanner report, or signed review. | "Tested" or "reviewed" without artifact. |
| Owner | Evidence owner and accepter are named. | Team or committee owns subjective sign-off. |
| Freshness | Evidence is run or reviewed after final relevant edit. | Old output, memory, or ticket comment closes the criterion. |

## Acceptance-To-Validation Matrix

| Criterion type | Preferred validation | Required evidence limit |
| --- | --- | --- |
| Functional user behavior | Integration or E2E test plus focused unit tests for business branches. | Does not prove unrelated roles, browsers, or data sizes. |
| API contract | Contract test, schema diff, generated-client check, and error example. | Does not prove backend implementation internals beyond the contract. |
| Permission or tenant behavior | Allowed and denied tests, audit/log expectation, and same-pattern scan. | Does not prove all policies unless the matrix covers them. |
| Error or recovery path | Negative test, dependency-failure simulation, and user/operator outcome. | Does not prove provider or production outage behavior unless exercised. |
| Performance or reliability | Load/benchmark report with percentile, window, dataset, and environment. | Does not prove production capacity outside declared scope. |
| Accessibility | Automated scan plus keyboard and assistive-tech walkthrough where material. | Does not prove every assistive technology or unrelated page. |
| Data migration | Pre/post counts, checksum or sample diff, rollback rehearsal, and query evidence. | Does not prove production lock/lag without production-like rehearsal. |
| Operational readiness | Dashboard/log/alert/runbook review, drill, or release checklist artifact. | Does not prove on-call response quality unless drilled. |
| Subjective product judgment | Single accountable approver, artifact, date, and rejection condition. | Does not prove objective usability unless paired with research or metrics. |

## Graph, Memory, And Execution Coupling

| Evidence source | Use as | Reject as |
| --- | --- | --- |
| Repository graph | A selector for affected source paths, tests, docs, runbooks, dashboards, contracts, and owners. | Proof that a criterion is met without inspecting current artifacts. |
| Project memory | A lead to prior decisions, fragile paths, stale criteria, and repeated acceptance disputes. | Authority to close acceptance when source, owner, or date is unverified. |
| Execution trajectory | A freshness ledger for commands run, repairs made, repeated failures, and stale validations. | Evidence for final acceptance when output predates final edits. |
| Generated plans or summaries | A checklist of candidate criteria and unknowns. | Product authority or stakeholder sign-off. |

Strong outputs state accepted, rejected, and not-verified graph/memory/trajectory inputs for each release-blocking criterion.

## Rejection-Condition Decision Tree

```text
Can the criterion describe an observable failure state?
  NO -> Rewrite; it is not falsifiable.
  YES -> Continue.

Can a reviewer verify the failure state without asking the author?
  NO -> Add artifact, owner, command, query, or manual procedure.
  YES -> Continue.

Would failing this criterion block release, require rollback, or require owner sign-off?
  YES -> Mark release_blocking and map to the next gate.
  NO  -> Record residual risk or non-blocking follow-up.

Does evidence cover the final edited behavior and declared scope?
  NO -> Mark stale/not verified.
  YES -> Criterion can be considered ready for downstream validation.
```

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| "Done when tests pass." | Test scope, assertion, and evidence limit are unknown. | Name tests, assertions, command, exit code, and what they do not prove. |
| "No regressions." | Regression surface is undefined. | Name scenarios, tags, contracts, or dashboards that must remain green. |
| "Secure enough." | Security bar is subjective. | Map to ASVS/CWE/abuse case, allowed and denied paths, and security gate. |
| "Looks good." | Subjective acceptance has no accountable accepter. | Name approver, artifact, date, and rejection condition. |
| "Use the same criteria as last time." | Prior criteria may be stale. | Confirm current source, graph, owners, and validation freshness. |
| "Operational follow-up later." | Release can ship without rollback, alert, or runbook evidence. | Add release-blocking operational criteria or named residual owner. |
| "One criterion for the whole workflow." | Partial failure cannot be diagnosed. | Split by step, actor, state, error path, and end-to-end flow. |

## Handoff Boundaries

- Use `requirement-clarification` when a missing owner decision can change the standard.
- Use `scenario-decomposition` when criteria cannot be complete until scenarios are split.
- Use `non-goal-boundary-definition` when acceptance must prove excluded behavior is absent.
- Use `quality-test-gate` when criteria need executable test strategy, fixture ownership, or validation freshness.
- Use `security-privacy-gate` for security, privacy, audit, or permission acceptance.
- Use `reliability-observability-gate` for SLO, alert, dashboard, runbook, or incident-readiness acceptance.
- Use `delivery-release-gate` when criteria decide rollout, rollback, release notes, or production evidence.
