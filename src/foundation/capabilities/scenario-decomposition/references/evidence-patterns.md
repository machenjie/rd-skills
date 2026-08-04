# Scenario Decomposition Evidence Patterns

Use this reference when scenario decomposition closure depends on validation freshness, prior source or task evidence reuse, release-critical scenario proof, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second scenario discovery catalog.

## Scenario-Claim-To-Validation Map

| Scenario claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Applicable scenario coverage is complete | Each retained category has a task-local decision or failure trigger plus actor, precondition, stimulus, outcome, verification, criticality, and applicable omission rationale | The active slice covers its evidenced applicable scenario categories | Coverage of inapplicable categories, or complete implementation and test coverage |
| Non-goals bound the scenario space | Requirement non-goals, excluded surfaces, omitted scenarios, owner decision, and escalation record for conflicts | Scenario expansion did not silently override approved scope | Future releases or backlog sequencing are decided |
| Release-critical scenario is covered | Scenario ID, MUST-HANDLE/SHOULD-HANDLE/DEFERRED decision, validation method, owner, and blocker status | Planning can distinguish release blockers from accepted residual risk | The downstream implementation has already passed tests |
| Fault and recovery assumptions are explicit | Timeout, unexpected schema, validation rejection, permission denial, conflict, partial write, retry exhaustion, downstream rejection, and terminal state rows when applicable | Important negative and recovery paths were considered | All production fault modes or chaos experiments are complete |
| Abuse path is not reduced to validation | Intentional misuse case, actor/tenant boundary, denial behavior, security handoff or residual risk | Hostile behavior was separated from accidental bad input | A full threat model or penetration test has run |
| Prior source or task evidence reuse is current | Current source/tests/docs/registry inspection, accepted/rejected prior scenario, freshness date, and changed-scenario delta | Reused scenario facts match inspected current behavior | repository inspection or memory is a complete source of truth |
| Validation is fresh after final scenario edit | Command/report/artifact path, scenario IDs covered, exit code or manual result, final edit scope, and freshness status | Evidence covers the final inspected scenario matrix | Unmeasured production data, live dependencies, or all dashboards are proven |
| Tool output is safe to retain | Action class, permission state, redaction rule, artifact path, retention owner, and rollback or cleanup path | Scenario evidence collection avoids obvious sensitive output leakage | Every future test log, connector export, or debug artifact is safe |

## Current Evidence And Freshness

- Treat repository inspection, prior scenario sets, prior task evidence, incident notes, support signals, generated artifacts, and validation output as selectors until current source, tests, docs, registry, and owner evidence confirm them.
- Accept a prior scenario only when actor, role, tenant boundary, state model, side effect, integration contract, data shape, and validation method still match the active slice.
- Mark scenario evidence stale after edits to requirements, non-goals, actors, state machines, permissions, API contracts, schemas, integrations, jobs, events, UI flows, tests, runbooks, or generated artifacts.
- Map every scenario ID, release-critical decision, validation method, handoff boundary, accepted/rejected reuse claim, tool-output artifact, and residual risk to current evidence or explicit not-run disclosure.

- If failure injection, replay harness, integration sandbox, load or abuse simulation, record environment, data class, stop condition, redaction, and cleanup path.
- If live external dependency, support console, production replay, admin action, or connector write, require owner approval, containment path, rollback or compensation plan, and redaction rule.
- Classify each retained scenario as normal, alternate, edge, failure, abuse, recovery, or operational with release criticality.
- Require a task-local decision or failure trigger for each retained category row.
