# Operating Model

ChangeForge Skill Mesh is a skill-authoring repository. Its source content, registries, validators, builders, packagers, installers, and approved runtime support sources exist to produce generated runtime artifacts in `dist/`; source folders under `src/` are never installed directly.

## Source Repo Vs Runtime Install

The source repo contains authored material:

- `src/professional-skills`: 19 top-level professional skills.
- `src/foundation/capabilities`: 106 implemented foundation capabilities plus `_template`.
- `src/domain-extensions`: 7 optional domain extension skills.
- `src/registry`: `skills.yaml`, `capabilities.yaml`, `domain-extensions.yaml`, and `routing-rules.yaml`.
- `src/hook-runtime`: optional project-level hook runtime source for warning-only execution reminders.

Runtime installs consume only generated outputs under `dist/`. Installed skill directories must contain `SKILL.md` at their root. Raw `src/`, raw registry folders, foundation capability source trees, and raw hook runtime source are not installed.

## No Personal Asset Mapping

ChangeForge is self-contained. It does not ingest, scan, index, summarize, map, package, or install any personal technical asset library. It does not create toolbox mappings or assume any external user-specific content corpus at runtime.

## Change Routing Flow

1. Capture the requested change, missing information, constraints, and intended agent/runtime.
2. Classify change type, blast radius, risk level, domain signals, and quality level from L1 through L5.
3. Select the minimum sufficient professional skill path.
4. Attach only the foundation capabilities required by the selected professional skills.
5. Add a domain extension only when Web3, AI, mobile, big data, IoT/embedded, payment/trading, or low-level systems signals are present.
6. Declare acceptance criteria, risk escalation, quality gates, evidence, and handoff order.
7. Build, package, install, upgrade, uninstall, or doctor from `dist/` only.

## Skill Layers

Professional skills are the runtime entry points Codex, Claude Code, GitHub Copilot, and hosted OpenAI API consumers should invoke for product-change work. They own orchestration, impact analysis, implementation guidance, test gates, release gates, documentation gates, and specialist review.

Foundation capabilities are compact engineering rules and decision aids. In `recommended` and `full`, they are compiled into professional skill references under `references/capabilities/`. In `dev`, they are also exposed as top-level skills for ChangeForge authoring and debugging.

Language capabilities are professional engineering rules, not language tutorials or personal technical asset mappings.

Domain extensions add domain-specific risk and routing rules. They are top-level in `full` and `dev`, and indexed by the router for profile-aware routing.

## Agent Execution Discipline

The `agent-execution-discipline` foundation capability (id 102, group `engineering-workflow`) enforces evidence-driven completion, verified-cause diagnosis, route-repair after repeated failure, same-pattern scan discipline, reuse-and-placement rationale, and proactive closure for every agent-assisted change.

It is a foundation capability, not a top-level professional skill. The router selects it through `change-forge-router` and compiles its reference into the professional skills that consume it. The capability itself does not introduce runtime hooks, persistent state files, entertainment rhetoric, or PUA-style narration.

## Optional Hook Runtime

The optional ChangeForge Hook Runtime is a project-level support artifact, not a skill and not a replacement for `change-forge-router`. It may emit warning-only reminders after tool use or before handoff, but it must not select a complete route, read every compiled reference, ingest personal content, or install raw `src/hook-runtime`.

Hook runtime state is operational cache stored outside the project source tree under the user's cache directory. It is not a PUA state file, not runtime skill content, and not a user-specific corpus mapping. Hooks are built into `dist/` and may be placed into a Codex or Claude project with `installers/install.py --with-hooks` (project scope only), which preserves existing project hook configuration and never auto-trusts hooks.

## Telemetry, Review, And Human Promotion

When the hook runtime is enabled, hooks also append a runtime fact log to the user cache under `${XDG_CACHE_HOME:-~/.cache}/changeforge/telemetry/<repo_hash>/`. Telemetry is operational cache, not project source and not runtime skill content. It records execution-time facts only: changed paths, hook findings, suggested skills and capabilities, and closure-completeness flags. It never records prompts, environment variables, secrets, or full command output, and it never edits `SKILL.md`, `routing-rules.yaml`, or `capabilities.yaml`.

`change-forge-router` emits a machine-readable `changeforge_route` manifest alongside its human-readable result so hooks, `doctor`, telemetry review, and the eval tools can check closure completeness mechanically. Stop-stage closure treats the route manifest as present only when the key routing fields are parseable, not when `changeforge_route` is mentioned in prose. The manifest does not replace the human-readable routing explanation and does not authorize any tool to mutate skill rules.

The improvement loop is observe → review → human-promote: `scripts/review-agent-telemetry.py` analyzes telemetry and writes advisory suggestions; a human reviews them; `scripts/promote-telemetry-suggestion.py` generates candidate golden cases, hook fixtures, or agent-behavior samples for human completion; and `scripts/eval-agent-behavior.py` scores captured outputs against expected route manifests. No tool performs online self-learning or auto-applies a suggestion. See [TELEMETRY.md](TELEMETRY.md).

## Reference Loading Model

`SKILL.md` is loaded when a skill is selected. The `references/` directory is not assumed to be fully loaded automatically, even when the build profile compiles capability references into the runtime skill folder.

The router selects foundation capabilities as part of the route. Professional skills then read only the selected capability references, using `references/capabilities/index.md` as a lookup aid when needed. Capability reference paths are deterministic: `references/capabilities/<capability-id>-<capability-name>.md`.

Reference loading follows the L1 through L5 change level:

- L1 changes do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.

References are a precision mechanism, not a dumping ground. They should make selected work more reliable without turning every small change into broad context loading.

## Minimal Sufficient Routing

Routing should choose the smallest path that can safely complete the change. A small local bug fix should not trigger a full product program. A migration, authentication, payment, Web3, AI, or production rollout change should escalate until the affected contracts, rollback path, security review, and evidence gates are explicit.

## Risk Escalation

Escalate risk when the change may affect authentication, authorization, object-level permission, payment, billing, wallet keys, Web3 assets, user data, PII, file upload, AI prompts or retrieval, external integrations, webhooks, database migrations, production deployment, secrets, security dependencies, or irreversible operations.

Escalation means adding the relevant professional gates, domain extension, foundation capabilities, validation evidence, rollback criteria, and human approval point before release.
