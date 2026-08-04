# Use Case Modeling Evidence Patterns

Use this reference when use-case closure depends on current repository inspection, prior task evidence, observable action sequence, stakeholder-owned docs, tests, validation freshness, or tool permission boundaries. Keep it as an evidence map, not a second use-case tutorial.

## Use-Case Claim-To-Evidence Map

| Use-case claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Actor-goal boundary is current | Current source, docs, tests, route/job/webhook entry point, actor role, goal statement, rejected combined goals, and owner | The inspected behavior has one primary actor and one goal | Other actors, UI navigation, or downstream scenarios are fully modeled |
| Preconditions are enforced gates | Enforcement point, permission or lifecycle guard, fixture or test path, and denied/prerequisite outcome | The inspected use case cannot start unless the listed gates hold | Every caller, client, job, or external integration enforces the same gates |
| Main path matches current behavior | Source/test/doc path, sequence of observable domain steps, durable state/event side effect, and validation command or report | The described path matches the inspected current implementation or accepted design source | Production-only behavior, unavailable stakeholder decisions, or future implementation work is correct |
| Alternate path has defined outcome | Alternate trigger, preserved data, retry/continue rule, postcondition, and acceptance or test trace | The alternate path does not end in vague UI-only behavior | Exhaustive scenario coverage or state-machine legality is complete |
| Failure path has minimal guarantee | Failure trigger, terminal or recoverable state, compensation/retry owner, support/audit visibility, and validation or residual-risk owner | The system promise when the actor goal fails is explicit | Recovery automation, live provider behavior, or operational runbook execution is proven |
| External/system actor is modeled | Actor identity, authentication/trust boundary, idempotency or duplicate rule, timeout/replay behavior, and terminal outcome | The background trigger is visible as actor-facing product behavior | Full integration reliability, provider SLA, or security review is complete |
| Business rule and acceptance trace are linked | Rule id/source, use-case path step, acceptance criterion id, test/validator/report path, and owner | The use case can drive acceptance or implementation handoff | All rule variants, UI states, or downstream consumers are covered |
| Memory/graph/execution claim is current | Prior claim source/date, current source/test/doc reread, graph delta, accepted/rejected mismatch, command, exit code, and report path | The accepted prior evidence still matches the inspected use case boundary | Future edits, dynamic callers, or uninspected production data remain safe |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, old requirements, generated summaries, prior acceptance traces, and observable action sequence as selectors until current source, tests, docs, registry entries, or stakeholder-owned artifacts confirm them.
- Accept a prior "use case exists", "precondition already enforced", "alternate path covered", "failure path is handled", or "acceptance trace is complete" claim only when current paths and fresh validation still match.
- Mark evidence stale after edits to requirements, source, tests, docs, policy files, schemas, generated clients, route/job/webhook entry points, fixtures, reports, validation commands, or acceptance traces.
- Record inspected or skipped boundaries: primary and secondary actors, UI entry, API route, service method, job, webhook, durable state, emitted event, side effect, rule source, acceptance criteria, tests, docs, and registry.
- A final confidence claim for an in-scope use case requires a current command, source or test path, document section, rule ID, report, or owner review that traces it. Otherwise the claim remains explicitly unverified residual risk.

- If stakeholder document export, production behavior sample, telemetry query, or connector read, require owner, bounded scope, redaction, timestamp, and evidence-limit disclosure.
- If requirement, acceptance, API contract, policy, or workflow source update, record owner, diff, rollback/revert path, validation map, and downstream handoff.

## Blocking Conditions

Block closure when actors and goals span multiple use cases, preconditions are unenforced, postconditions are UI-only, or alternate paths lack durable outcomes. Also block implicit external actors, stale prior evidence, validation predating the final edit, and state mutation without permission, isolation, and rollback disclosure.
