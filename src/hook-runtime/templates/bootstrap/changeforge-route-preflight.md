<!-- ChangeForge route-preflight bootstrap. Advisory guidance, not a router. -->
# ChangeForge Route Preflight

This fragment is an optional, install-time bootstrap reminder for runtimes that
do not expose a session-start hook (for example Codex). It carries the same
route-preflight discipline that the Claude `SessionStart` bootstrap hook emits.
It does not replace `change-forge-router`, does not select a full route, and
does not load compiled references.

## Preflight Rules

Run this preflight before engineering work, then load the minimum sufficient
skill path:

- Possible engineering change — code, review, debug, test, refactor, release, or
  skill authoring — run `change-forge-router` preflight before acting. Do not
  skip routing because a change "looks small".
- Adds or changes a function, class, file, directory, helper, service,
  repository, adapter, or utility — require `implementation-structure-design`
  (reuse search and placement rationale) before new structure is accepted.
- A completion claim is coming — bind it to `agent-execution-discipline`: no
  completion claim without fresh validation evidence and residual risk.
- The user already named a narrow skill path and the scope is known — respect it
  and do not re-route.
- Pure question, explanation, or translation with no engineering action — no
  routing needed.

When you route an engineering change, emit a `changeforge_route` manifest naming
`selected_skills`, `selected_capabilities`, `required_references`, and
`required_quality_gates`, and restate it at handoff. A route described only in
prose is not closure evidence.

## Loading Discipline

- A possible engineering change triggers a route preflight, not a full load.
- A confirmed risk, stage, or surface signal selects the skill path.
- Deep rules load only the selected references, never every reference.

This preflight is advisory. It never blocks execution and never overrides an
explicit, in-scope instruction from the user.
