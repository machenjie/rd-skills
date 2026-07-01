<!-- ChangeForge route-preflight bootstrap. Advisory guidance, not a router. -->
# ChangeForge Route Preflight

This fragment is an optional, install-time bootstrap reminder. It is the no-trust
alternative to the executable `SessionStart` bootstrap hook (now wired for both
Codex and Claude): it carries the same route-preflight discipline as plain
guidance text for users who prefer not to trust executable hooks, or for project
instructions (for example AGENTS.md) that should always reference it. It does not
replace `change-forge-router`, does not select a full route, and does not load
compiled references.

## Preflight Rules

Run this preflight before engineering work, then load the minimum sufficient
skill path:

- Possible engineering change — code, review, debug, test, refactor, release, or
  skill authoring — run `change-forge-router` preflight before acting. Do not
  skip routing because a change "looks small".
- Requirement clarification comes first: record current behavior, desired
  behavior, non-goals, constraints, acceptance/TDD signal, blocking questions,
  assumptions, and proceed/block status before engineering action.
- Read before planning: inspect relevant target-project code, tests, configs,
  docs, existing implementation, conventions, and call chain before writing a
  plan. A plan without inspected boundaries is invalid.
- Use TDD-oriented planning before implementation: name the failing, new, or
  updated test, eval, validation command, acceptance check, or explicit
  not-verified risk.
- SDD material choice gate is strict: each material design decision point needs
  non-empty `id`, `trigger`, `decision`, boolean `blocking`,
  `user_choice_status`, at least two `options` for material/blocking choices,
  `recommended_option`, `why_user_choice_is_needed`, `resolution_evidence`, and
  `residual_risk`. A no-choice rationale must cite prompt, fixture, explicit
  user instruction, repository convention, existing pattern, or reuse evidence.
- Split work into actions. Each action needs an owner skill or capability and a
  different review skill or capability.
- Review findings must route to repair, then return to review before handoff.
- Adds or changes a function, class, file, directory, helper, service,
  repository, adapter, or utility — require `implementation-structure-design`
  (reuse search and placement rationale) before new structure is accepted.
- Object/method placement work must locate the existing object/module owner
  before creating helpers. Prefer extending the owning method/object when it
  already protects the invariant; reject shared utilities or helper bags unless
  reuse evidence proves current multi-owner value. If the prompt asks for an
  Object-Method Encapsulation Decision, put accepted/rejected object candidates
  and side-effect adapter boundaries in candidate-visible evidence.
- A completion claim is coming — bind it to `agent-execution-discipline`: no
  completion claim without fresh validation evidence and residual risk.
- Business semantics are in scope — business terms, rule authority, workflow
  state, golden cases, stale business memory, or graph/memory business hints —
  select `business-semantic-control-plane`; memory and graph are selectors until
  verified by current source, owner review, or validation evidence.
- The user already named a narrow skill path and the scope is known — respect it
  and do not re-route, but still run requirement clarification, read-before-plan,
  TDD/validation signal, action/review mapping, repair/re-review, and evidence
  handoff through that skill path.
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
- Pure question, explanation, or translation with no engineering action may skip
  the full engineering flow after stating that no engineering action is being
  taken.

This preflight is advisory. It never blocks execution and never overrides an
explicit, in-scope instruction from the user.
