# ChangeForge Professional Contract

Use this contract when a runtime cannot load the full ChangeForge router or when
an action hook needs a compact reminder.

- Classify the current action stage before acting: planning, read, edit, review,
  repair, test, permission, release, compaction, or subagent.
- Select an owner professional skill and a different reviewer skill.
- Read only the selected capability references needed for the current risk.
- Do not store prompt text, secrets, environment variables, or full command
  output in hook state or telemetry.
- Before handoff, include route manifest, stage manifest when non-trivial,
  changed files, validation evidence, residual risk, and rollback note.
- Review-only work must lead with findings or explicitly state no findings.
- Repair work must trace each finding to a fix, re-review, validation, and
  residual risk.

