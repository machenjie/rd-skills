# ChangeForge Copilot Professional Contract

Copilot hook coverage is intentionally flatter than Codex and Claude. When a
prompt-stage hook is unavailable, treat this contract as the always-loaded
professional injection fallback.

- Use repository instructions first, then ChangeForge routing.
- Infer the current stage from the action: read/search, edit, review, repair,
  test, permission, release, compaction, or subagent.
- Preserve Copilot-safe output: context hooks emit `additionalContext`; the Stop
  hook may emit top-level `decision` and `reason`.
- Do not create or depend on user-specific content corpora, archive indexes, or
  personal mapping catalogs.
- Do not store prompts, secrets, environment variables, or full command output.
- Final handoff must include validation evidence or an explicit not-run
  disclosure, rollback note, residual risk, and the ChangeForge route/stage
  manifests for non-trivial engineering work.
