# Claude Code Instructions

Treat this repository as a ChangeForge Skill-authoring project. Author, validate, build, package, install, upgrade, and uninstall standard Skills and Agent Profiles only. Build output belongs in `dist/`; never install `src/` or source registries directly.

Do not ingest, index, summarize, map, package, or install personal technical archives. Do not create `src/toolbox` or `registry/toolbox.yaml`. Do not add executable interception, internal task-state machinery, private evidence storage, hidden Skill packaging, or another sandbox/workspace manager.

Use the four bounded profiles from `src/agent-profiles/role-agents.json` and the authoritative control prompt in `src/control-prompts/main-control-agent.md`. Route one primary Professional Skill per task and load Foundation or Domain references only for concrete signals.

Validate every Skill-system change before handoff with the complete canonical command set in `AGENTS.md` and `docs/VALIDATION.md`. If a validator is replaced, update both files and CI in the same change.

Execution discipline:

1. No evidence, no completion.
2. No verified cause, no diagnosis.
3. Stop repeating a failed path after two attempts.
4. Scan for the same pattern before calling a local fix complete.
5. Explain reuse and placement before adding structure.
6. Hand off with scope, commands, results, unverified areas, and residual risk.
