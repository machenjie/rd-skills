# ChangeForge Professional Contract

Use this contract when a runtime cannot load the full ChangeForge router or when
an action hook needs a compact reminder.

- Classify the current action stage before acting: question, read, plan, edit,
  test, review, repair, refactor, release, skill_authoring, hook_runtime,
  permission, subagent, compaction, or unknown.
- Pure questions, explanations, translations, and no-action lifecycle events do
  not need a route manifest and must not create closure state.
- Select an owner professional skill and a different reviewer skill.
- Read only the selected capability references needed for the current risk.
- Before editing code, identify setup/test entrypoints, public API, reuse
  candidates, and the owning object/module.
- Apply compact PDD -> DDD -> SDD -> TDD gates before implementation: PDD
  acceptance criteria/constraints/non-goals; DDD invariants and side-effect
  boundaries; SDD public API/module/failure/logging/security/performance
  constraints; TDD validation mapped to those facts.
- Before implementation, SDD must classify material design choices. If a wrong
  answer would change architecture, public API, data, security, migration,
  rollback, acceptance, or user-visible behavior, stop and ask the user with
  options. Material decision points need non-empty id, trigger, decision,
  boolean blocking, status, at least two options, recommendation, user-choice
  rationale, resolution evidence, and residual risk. If proceeding under a safe
  assumption, record why it is reversible, local, conventional,
  acceptance-neutral, and backed by prompt, fixture, repository convention, or
  reuse evidence. Do not silently resolve blocking design choices.
- Preserve setup and test harness scripts unless the task explicitly requires a
  change. Keep setup runnable from the candidate root, compatible with
  environment-provided roots, and free of external network or HOME/CODEX_HOME
  writes. Do not rely on fixed-depth parent traversal to locate the repository
  root. Do not add package dependencies unless the task explicitly requires
  them; prefer the standard library and existing local files.
- Do not satisfy professional evidence by prose only. Back reuse, placement,
  security, and reliability claims with code or tests unless the task is
  documentation-only.
- Do not store prompt text, secrets, environment variables, or full command
  output in hook state or telemetry.
- Do not mark a route manifest as present unless a handoff manifest was parsed.
- Before handoff, include route manifest, stage manifest when non-trivial,
  changed files, validation evidence, residual risk, and rollback note.
- Review-only work must lead with findings or explicitly state no findings.
- Repair work must trace each finding to a fix, re-review, validation, and
  residual risk.
