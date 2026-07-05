<!-- ChangeForge route-judgment bootstrap. Advisory guidance, not a router. -->
# Engineering Route Judgment

This fragment is an optional, install-time bootstrap reminder. It is the no-trust
alternative to the executable `SessionStart` bootstrap hook (now wired for both
Codex and Claude): it carries the same route-judgment discipline as plain
guidance text for users who prefer not to trust executable hooks, or for project
instructions (for example AGENTS.md) that should always reference it. It does not
select a full route and does not load compiled references.

## Judgment Rules

Before engineering work, start from the fixed entry skill
`change-forge-router` for classification, then hand off to the smallest
specific owner and reviewer path. Make a concise route judgment:

- Possible engineering change — code, review, debug, test, refactor, release, or
  skill authoring — use `change-forge-router` as the entry classification skill
  to determine task type, risk level, owner concern, validation focus, and
  residual risk before acting.
- Requirement clarification comes first: record current behavior, desired
  behavior, non-goals, constraints, acceptance/TDD signal, blocking questions,
  assumptions, and proceed/block status before engineering action.
- Read before planning: inspect relevant target-project code, tests, configs,
  docs, existing implementation, conventions, and call chain before writing a
  plan. A plan without inspected boundaries is invalid.
- Use TDD-oriented planning before implementation: name the failing, new, or
  updated test, eval, validation command, acceptance check, or explicit
  not-verified risk.
- Material design choices: state the trigger, decision, options or rationale,
  validation evidence, and residual risk in normal prose. A no-choice rationale
  must cite prompt, fixture, explicit user instruction, repository convention,
  existing pattern, or reuse evidence.
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
  include the business-semantic concern; memory and graph are selectors until
  verified by current source, owner review, or validation evidence.
- The user already named a narrow skill path and the scope is known — respect it
  and do not reclassify through the router, but still run requirement
  clarification, read-before-plan, TDD/validation signal, action/review mapping,
  repair/re-review, and evidence handoff through that skill path.
- Pure question, explanation, or translation with no engineering action — no
  routing needed.

When you route an engineering change, summarize the route naturally when it helps
the next reader: task type, risk level, relevant owner skill or professional
concerns, source and test context to read, validation focus, assumptions, and
residual risk. Strong routing evidence comes from runtime-observed context,
validation records, or replay/evaluation artifacts, not from hand-authored
protocol fields.

## Loading Discipline

- A possible engineering change enters through `change-forge-router` for a
  concise route judgment, not a full load.
- A confirmed risk, stage, or surface signal selects the skill path.
- Deep rules load only the selected references, never every reference.
- Pure question, explanation, or translation with no engineering action may skip
  the full engineering flow after stating that no engineering action is being
  taken.

This bootstrap is advisory. It never blocks execution and never overrides an
explicit, in-scope instruction from the user.
