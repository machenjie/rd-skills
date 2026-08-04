# Requirement Structuring Benchmarks And Patterns

Load this reference when an accepted request must become an outcome-first, traceable Behavior-First Structured Requirement. This artifact is a structured requirement, not an implementation-preparation brief; do not load it while blocking authority/current-behavior questions remain or to preselect implementation design.

## Behavior-First Structured Requirement

| Field | Decision-bearing content | Reject |
| --- | --- | --- |
| Current behavior | Actor/system, precondition, trigger, observable output/state/effect, and current evidence. | Internal call sequence treated as user/system behavior. |
| Desired behavior | Observable outcome and behavior that must remain unchanged. | Endpoint, table, class, component, or mechanism as the requirement. |
| Scope and actors | Named surfaces, versions, tenants, data, jobs/events/docs, and relevant human/machine/external actors. | Broad module names or generic “user/system.” |
| Non-goals | Behavior-bound exclusions with forbidden artifacts and not-present checks. | Schedule phrases or future placeholders. |
| Constraints | Measurable or policy-backed security, performance, reliability, accessibility, compatibility, data, and operability limits only when applicable. | “Fast,” “secure,” “simple,” or an unsupported fixed threshold. |
| Dependencies/unknowns | Contract/owner/readiness, blocking status, safe assumption, expiry, and handoff. | Hidden ordering or authority in task notes. |
| Acceptance and trace | Actor/precondition/trigger/result/rejection plus evidence owner and freshness. | “Works,” “tests pass,” or separate unlinked requirement/test lists. |

Convert a mechanism request by asking who triggers it, what must already be true, what observable result/absence follows, what stays compatible, and which implementation choices remain unauthorized. If any answer can change contract, data, authority, migration, release, or compliance, return it to clarification rather than filling it in.

## Trace And Constraint Routing

Map each functional requirement to its scenario and verification owner. Map each non-goal to a forbidden artifact/check and each constraint to a metric/control/standard plus specialist gate. Map each dependency to owner/contract/readiness and each assumption to its safety reason plus expiry. Traceability is created before planning, not retrofitted to justify code.

Route response/capacity/SLO constraints to `performance-budgeting` or `reliability-observability-gate`; API/event/client compatibility to `data-api-contract-changer` or `version-compatibility`; identity/data-visibility risk to `security-privacy-gate` or `permission-boundary-modeling`; migration/retention/deletion to data and release owners; external systems to `integration-change-builder`.

## Evidence And Proof Limits

Classify repository, prior-task, stakeholder, generated, and command evidence as accepted, rejected, stale, partial, or unknown. Source inspection can establish existing code behavior only within inspected paths; it does not prove product intent, production state, external compatibility, or future rollout. Generated artifacts prove only their current source/version.

Reject mechanism-as-requirement, source internals as behavioral truth, hidden non-goals, vague qualities, memory-closed requirements, trace maps written after implementation, and intake that authorizes architecture. Route unresolved facts to `requirement-clarification`, stable scenarios to `scenario-decomposition`, criteria to `acceptance-standard-definition`, exclusions to `non-goal-boundary-definition`, impact discovery to `repository-impact-inspection`, and evidence selection to `quality-test-gate`.
