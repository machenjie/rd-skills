# ChangeForge Hook Runtime

ChangeForge Hook Runtime is not a skill.
It does not replace change-forge-router.
It adds execution-time reminders across the agent lifecycle: at session and
subagent start, per user prompt, before and after tools run, and before the
agent or a subagent stops.
Default mode is warn, not block.

The hook runtime is a small project-level reminder layer for agent execution. It
does not route work, does not read all skill references, and does not become a
professional skill. The router remains the semantic source of truth for selecting
ChangeForge skills, capabilities, domain extensions, and quality gates.

## Scope

The runtime provides these reminder hooks:

- Session Bootstrap: at `SessionStart` (both Codex and Claude, including the
  Codex `compact` source) and `SubagentStart`, remind the agent to run a
  `change-forge-router` preflight before engineering work. Also ships as an
  advisory install-time fragment.
- Route Reminder: at Codex `UserPromptSubmit`, add a concise per-prompt reminder
  to route and emit a `changeforge_route` manifest. Never reads or records the
  prompt text.
- Pre-Edit Risk Preview: at Codex `PreToolUse`, preview risk surfaces before an
  edit or command runs. Advisory only; never denies the tool call.
- Post-Edit Structure Gate: after edit tools run, detect structural code changes
  that should preserve reuse, placement, ownership, dependency direction, public
  API decisions, same-pattern scans, and nearby tests.
- Risk Surface Gate: after edit tools or shell commands run, detect high-risk
  surfaces such as auth, data contracts, cache, queue, Kubernetes, Helm, and big
  data work so the agent remembers the matching gate.
- Stop Closure Gate: before final handoff, remind the agent to include the
  ChangeForge path used, changed files, validation evidence, residual risk, and
  next actions.
- Subagent Closure Reminder: at Codex `SubagentStop`, remind the subagent to
  carry closure evidence back to the parent. Advisory only; never forces
  continuation and never touches the parent turn's closure state.

## Non-Goals

- Do not replace `change-forge-router`.
- Do not turn hooks into professional skills.
- Do not read every `references/` file.
- Do not block agents by default.
- Do not install `src/hook-runtime` directly.
- Do not install `src/` or `src/registry` as runtime content.

## Runtime State

Per-turn state is stored outside the project source tree:

```text
${XDG_CACHE_HOME:-~/.cache}/changeforge/hooks/<repo_hash>/current-turn.json
```

If the cache cannot be written, hooks emit a warning and continue. Hook failures
must not interrupt normal agent execution.

## Build Output

`scripts/build.py` copies this runtime into project-level hook layouts:

```text
dist/codex/project/.codex
dist/claude/project/.claude
```

Each generated project hook layout includes `.changeforge-hook-manifest.json`
so installation validation can prove which hook scripts were emitted.

Installer integration is intentionally deferred. The first phase validates and
builds hook artifacts only.
