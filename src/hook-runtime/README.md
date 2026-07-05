# ChangeForge Hook Runtime

ChangeForge Hook Runtime is not a skill.
It does not replace skill routing.
It adds execution-time expert guidance across a compact default lifecycle:
session bootstrap, prompt-level professional injection where supported,
pre-tool structure/material-choice/permission checks, one post-tool collector,
explicit review-capsule subagent checks, real compaction events, and Stop
closure.
Professional process gates are non-blocking by default. They observe bounded
facts, emit natural expert notes, and report quality degradation without
exposing hook state or internal protocol fields. Hard block is reserved for
explicit strict mode, `CHANGEFORGE_CI_MODE=ci`, benchmark, or maintainer policy,
and safety or permission boundaries such as destructive, secret-bearing,
production, or irreversible operations.

The hook runtime is a small project-level reminder layer for agent execution. It
does not route work, does not read all skill references, and does not become a
professional skill. Skill documents remain the semantic source of truth for
selecting ChangeForge skills, capabilities, domain extensions, and quality gates.

## Scope

The default `default_compact` profile provides these hooks:

- Session Bootstrap: at ordinary `SessionStart`, remind the agent to make a
  concise engineering route judgment. Compaction snapshot/reinject and
  professional injection do not run at ordinary session start.
- Professional Injection: at Codex and Claude `UserPromptSubmit`, inject
  action-aware professional context only when `should_inject=true`. Pure
  questions, explanations, translations, and no-engineering-action prompts stay
  quiet. Copilot does not wire `UserPromptSubmit`.
- Pre-Tool Gates: run SDD material-choice, pre-edit structure, and permission
  policy checks before real mutation surfaces. Permission policy is meaningful
  for terminal or permission-capable mutation tools and returns quietly
  elsewhere.
- Post-Tool Collector: `changeforge_post_tool_collector.py` is the single
  default `PostToolUse` entrypoint. It records read/search evidence silently,
  records post-edit structure and risk evidence for edits, records command risk
  and validation results for terminal tools, records review diff evidence, and
  emits tool-output-boundary guidance only for large, unsupported, privacy-fail,
  failure, or batch outputs.
- Stop Closure Gate: before final handoff, emits an engineering quality report
  covering source evidence, changed files, validation freshness, review
  authenticity, residual risk, and recommended human action. By default it
  reports `pass`, `degraded_ready`, or `fail` instead of asking the agent to
  fill internal closure fields. In explicit Stop block mode it can block
  high-confidence safety or strict-policy failures where the adapter supports a
  hard Stop decision; unsupported adapters record degraded enforcement instead
  of a pass.
- Subagent Review Gate: at `SubagentStart` and `SubagentStop`, runs only when a
  review capsule or explicit review workflow is present; otherwise it returns
  quietly. It merges only structured `phase_review_result` records.
- Compaction: `changeforge_compaction.py` handles real compaction events
  (`PreCompact` and `PostCompact` for Codex/Claude; `PreCompact` for Copilot).
  Default templates do not wire compaction from `SessionStart`, including
  compact-source session starts, to avoid duplicate lifecycle work.

## Non-Goals

- Do not replace skill routing.
- Do not turn hooks into professional skills.
- Do not read every `references/` file.
- Do not read, record, log, or echo user prompt text.
- Do not choose the full route; skill documents remain the semantic source of truth.
- Do not block unsupported or advisory-only gates by default.
- Do not fail closed on hook runtime errors unless explicitly configured.
- Do not turn hooks into router, skills, or source-of-truth.
- Do not install `src/hook-runtime` directly.
- Do not install `src/` or `src/registry` as runtime content.

## Runtime State

Per-turn state is stored outside the project source tree:

```text
${XDG_CACHE_HOME:-~/.cache}/changeforge/hooks/<repo_hash>/current-turn.json
```

If the cache cannot be written, hooks emit a warning and continue. Hook failures
must not interrupt normal agent execution.
Normal engineering agents must not inspect, write, or repair this state. Hook
state inspection is reserved for rd-skills maintenance, tests, replay, or human
debugging.

## Build Output

`scripts/build.py` copies this runtime into project and user hook layouts:

```text
dist/codex/project/.codex
dist/codex/user/.codex
dist/claude/project/.claude
dist/claude/user/.claude
dist/copilot/project/.github
dist/copilot/user/.copilot
```

Project layouts resolve their command path from the project git root; user
layouts resolve it from the agent home (`${CODEX_HOME:-$HOME/.codex}`,
`${CLAUDE_CONFIG_DIR:-$HOME/.claude}`, `${HOME}/.copilot`). VS Code Copilot uses
the flat (matcher-less) hook config format with `version: 1` and `timeoutSec`
and loads every `*.json` in its hook folder, so its config is the dedicated
`changeforge-hooks.json` and the scripts, manifest, and bootstrap fragment live
in a `changeforge/` subfolder. Copilot context output is top-level
`additionalContext` for supported context events. Copilot uses `permission`
decisions for `PreToolUse` and decision output for `SubagentStop`; unsupported
advisory paths are recorded as degraded evidence rather than a pass. Claude commands set
`CHANGEFORGE_AGENT=claude` explicitly, emit `hookSpecificOutput.additionalContext`
for context-bearing events, and use 10-second `timeout` values because Claude
Code measures timeout in seconds.
Each layout includes `.changeforge-hook-manifest.json` so installation
validation can prove which hook scripts and scope were emitted.

Supported Codex, Claude, and Copilot project/user installs include the
`default_compact` hooks by default. Use `--without-hooks` or
`--activation-level none` to opt out. `--activation-level bootstrap` installs
only the non-executable route-preflight fragment. `--with-hooks` remains
accepted as a backward-compatible explicit enable, but is no longer required.
User-authored hook entries stay in place, while ChangeForge-managed entries are
reconciled to the current built template. Hooks are never trusted automatically.

## Action-Aware Professional Injection

The hook runtime now adds an action-aware layer around the original reminders:

- `changeforge_action_classifier.py` classifies the current lifecycle stage
  (`question`, `read`, `plan`, `edit`, `test`, `review`, `repair`, `refactor`,
  `release`, `skill_authoring`, `hook_runtime`, `permission`, `subagent`,
  `compaction`, or `unknown`) and detects compact source/reason/matcher names.
  Pure questions, explanations, translations, and no-action lifecycle events do
  not receive professional injection and do not create Stop closure surface.
- `changeforge_runtime_route_resolver.py` maps the action, canonical stage,
  product surfaces, language surfaces, risk surfaces, and domain extensions to
  the minimum owner/reviewer skill set, selected capabilities, reference paths,
  skipped rationale, and quality gates. `changeforge_skill_index.py` remains a
  compatibility wrapper and does not contain static edit/repair owner routing.
- `changeforge_runtime_adapters.py` isolates output protocol differences across
  Codex, Claude, Copilot, and generic text runtimes.
- `changeforge_professional_injector.py`, `changeforge_post_tool_collector.py`,
  permission, compaction, and subagent review gates update bounded cache-side
  state and emit advisory context only when useful.
  The injector never marks AI-authored route prose as strong route evidence.
  Strong route evidence comes from runtime-observed context, selected skill
  injection, validation records, or replay/evaluation artifacts.

The runtime stores only bounded facts such as stage, paths, skill names, gate
names, and compact signal names. It does not persist prompt text, secrets,
environment variables, full command arguments, command output, user archives, or
personal content indexes.

## Policy and State

Global hook mode remains:

```bash
CHANGEFORGE_HOOK_MODE=off|observe|monitor|advisor|report|warn|block
```

Gate-specific modes override it:

```bash
CHANGEFORGE_PRE_EDIT_MODE=off|observe|monitor|advisor|report|warn|block
CHANGEFORGE_SDD_CHOICE_MODE=off|observe|monitor|advisor|report|warn|block
CHANGEFORGE_SDD_CHOICE_PRETOOL_MODE=off|observe|monitor|advisor|report|warn|block
CHANGEFORGE_SDD_CHOICE_STOP_MODE=off|observe|monitor|advisor|report|warn|block
CHANGEFORGE_PROCESS_PHASE_MODE=off|observe|monitor|advisor|report|warn|block
CHANGEFORGE_PROCESS_PHASE_PRETOOL_MODE=off|observe|monitor|advisor|report|warn|block
CHANGEFORGE_PROCESS_PHASE_STOP_MODE=off|observe|monitor|advisor|report|warn|block
CHANGEFORGE_PERMISSION_MODE=off|observe|monitor|advisor|report|warn|block
CHANGEFORGE_STOP_MODE=off|observe|monitor|advisor|report|warn|block
CHANGEFORGE_STOP_CLOSURE_MODE=off|observe|monitor|advisor|report|warn|block
CHANGEFORGE_SUBAGENT_REVIEW_MODE=off|observe|monitor|advisor|report|warn|block
CHANGEFORGE_HOOK_FAILURE_MODE=fail_open|fail_closed
```

Default professional-process gate modes are non-blocking:
`sdd_material_choice=warn`, `sdd_material_choice_pretool=warn`,
`sdd_material_choice_stop=warn`, `pre_edit_structure=warn`,
`process_phase=monitor`, `process_phase_pretool=monitor`,
`process_phase_stop=warn`, and `stop_closure=warn`.
`CHANGEFORGE_HOOK_MODE=block` does not upgrade professional process gates
unless `CHANGEFORGE_STRICT_BLOCKING=1`, `CHANGEFORGE_CI_MODE=ci`, or benchmark
strict mode is set. A
Stop hook can hard block only when `CHANGEFORGE_STOP_MODE=block` or its own
`*_STOP_MODE`/`CHANGEFORGE_STOP_CLOSURE_MODE` sets block. Repeated identical
Stop missing sets report advisory/degraded closure unless validation failed,
explicit security/privacy, destructive permission denial, or
destructive/migration rollback blockers are present.
Final handoff phase text is stored only as weak disclosure and cannot create
reviewed phase ledgers or satisfy later `PreToolUse` readiness. Unsupported
adapters record degraded closure instead of claiming enforcement. Unspecified
gates fallback to `warn`, and ordinary advisory gates default to `warn`. Hook
runtime failures still fail open unless explicitly configured fail-closed.
`changeforge_hook_policy.py` also exposes timeout, retry,
retry-delay, max-concurrency, and queue-limit policy fields for future lifecycle
adapters, without changing the synchronous script behavior.

`changeforge_state_reducer.py` owns state merge semantics. Lists are additive,
deduped, and capped; booleans use OR semantics; scalar stage/owner fields keep
the last non-empty value; and empty `active_skill_context` updates do not erase
existing compacted context. The runtime never stores raw prompts, secrets,
environment variables, full command output, or user-specific content corpora.

Strong phase review requires provenance. Passing phase results must come from
`subagent_review_gate`, `parent_independent_review_gate`, or `ci_review_gate`;
must include `review_source`, `capsule_id`, `expected_artifact_digest`,
`review_context_strength: strong`, and `reviewer_boundary`; and must match the
current artifact digest. ClosureContract reuses the canonical
`phase_review_passes(..., require_strong_source=True)` check, so score below 4,
matching owner/reviewer skill, blocking findings, missing expected digest,
missing approved scope, or stale digest cannot pass closure. Final handoff
`phase_reviews` are weak disclosure only. If no real artifact digest exists,
the process phase gate reports degraded review authenticity; it does not ask
ordinary agents to fill hook protocol fields.

Implementation review is a separate closure signal from PDD/DDD/SDD/TDD review.
It must cover the actual changed files and reviewed diff digest. Missing or weak
implementation review with targeted validation reports degraded-ready residual
risk and names the natural review action: review the current diff, cover
changed files, and bind the review to the latest material edit. Weak, failed,
or unrelated review keeps closure degraded. Final handoff prose cannot satisfy
implementation review.

Report files should not carry timestamp-only diffs. `reports/*.json` and
`reports/*.md` changes that only refresh `generated_at`, `timestamp`, or
`report_generated_at` are rejected by report consistency validation; commit only
substantive report content changes.

Hard Stop blockers preserve closure-surface state. In explicit Stop block mode,
validation failures, destructive/security/privacy blockers, phase/review
blockers, SDD choice blockers, and implementation review blockers keep changed
paths, validation results, review findings, phase ledgers, review capsules,
choices, and liveness counters. Non-blocking advisory/ready exits can clear work
state while preserving liveness.

State reducer updates append/merge phase, review, choice, implementation review,
and validation evidence. Empty lists are ignored for those evidence families;
only `clear_fields`, `reset_for_new_prompt`, or `clear_state()` clear them.

Example preflight:

```yaml
changeforge_implementation_preflight:
  stage: edit
  read_evidence:
    target_files:
      - src/module/file.py
    sibling_files:
      - src/module/sibling.py
    nearby_tests:
      - tests/test_file.py
  placement_decision:
    target_file: src/module/file.py
    owner_module: module
    reason: existing module owns this behavior and test boundary
    rejected_locations:
      - path: src/common/utils.py
        reason: wrong ownership
  reuse_decision:
    direct_reuse:
      - symbol_or_path: src/module/existing.py
        reason: existing behavior
    new_code_justification: no compatible extension point
  object_boundary:
    artifact_type: module
    owner: module
    state_or_invariant: module owns the changed behavior boundary
    public_api_change: false
    compatibility_notes: no public API change
  test_plan:
    validation_commands:
      - python3 -m unittest discover -s tests
  risk:
    rollback_or_revert_path: revert this patch
```

Additional install flags:

```bash
python3 installers/install.py --agent codex --scope project --target <repo>
python3 installers/install.py --agent codex --scope project --target <repo> --with-universal-bootstrap
python3 installers/install.py --agent codex --scope project --target <repo> --without-hooks
python3 installers/install.py --agent copilot --scope project --target <repo> --with-copilot-instructions
```

Supported project/user installs include hooks and professional injection by
default. `--without-hooks` installs skills without executable hooks.
`--with-hooks` and `--professional-injection` remain backward-compatible
explicit enables. `--activation-level bootstrap` installs only the
non-executable route-judgment fragment; `--with-universal-bootstrap` installs
both the route-judgment and professional bootstrap fragments under
`.changeforge/`.
`--with-copilot-instructions` creates
`.github/copilot-instructions.md` only when that file does not already exist.
