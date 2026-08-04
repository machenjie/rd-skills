# Acceptance Standard Definition Benchmarks And Patterns

Load this reference when an accepted behavior needs falsifiable pass/fail standards, evidence ownership, freshness, or release-blocking classification. Do not load it while the underlying actor, desired behavior, or authority is unresolved.

## Criterion Contract

Each criterion names the actor or system, precondition, trigger, observable result, rejection condition, and validator.
Add environment, version, data scope, accepter, freshness, and proof limits when they affect verifiability.
Keep one independently diagnosable behavior per criterion.

| Risk | Candidate evidence | Required limit |
| --- | --- | --- |
| Functional or workflow | Focused unit plus integration/E2E at the changed boundary. | Does not cover unlisted roles, states, browsers, data, or external systems. |
| Public API/event/client | Contract/schema diff, consumer fixture, generated-client check, and error/compatibility example. | Does not prove unknown consumers or implementation internals. |
| Permission/privacy/security | Allowed and wrong-role/owner/tenant/abuse cases plus audit or policy evidence. | Does not prove policies/entry points outside the mapped surface. |
| Failure/recovery | Fault injection and durable user/operator outcome. | Local/stub evidence does not prove provider or production outage behavior. |
| Performance/reliability | Current budget, dataset/load/environment/window/percentile or ratio, query/report, and owner. | Does not generalize beyond measured load/environment. |
| Accessibility | Applicable automated, keyboard, focus, semantic, and assistive review. | Does not prove every technology, locale, viewport, or unrelated page. |
| Migration/release/operations | Pre/post integrity, mixed version, rollback/cutover, alerts/runbook/drill as risk requires. | Rehearsal does not prove production lock, lag, operator response, or scale. |

Release-blocking status follows the consequence of failure—correctness, data, security, compliance, irreversible effect, compatibility, or agreed service/product outcome—not a universal artifact checklist. Subjective judgment needs one accountable approver, artifact, date, and rejection condition.

## Evidence And Routes

Repository search selects artifacts but does not satisfy a criterion. Prior reports, generated summaries, or command output predating the final relevant edit are stale. Record accepted, rejected, partial, and not-verified evidence per blocking criterion.

Reject vague claims such as “tests pass,” “no regressions,” “secure enough,” or “looks good.”

Also reject whole-workflow criteria, remembered old criteria, and operational follow-up without an owner or blocking decision.
Route missing decisions to `requirement-clarification`.
Route scenario gaps to `scenario-decomposition` and excluded behavior to `non-goal-boundary-definition`.
Route executable tests to `quality-test-gate`.
Route security, reliability, and release criteria to their Professional gates.
