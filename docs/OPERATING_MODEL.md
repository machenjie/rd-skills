# Operating Model

ChangeForge Skill Mesh is a skill-authoring repository. Its source content, registries, validators, builders, packagers, and installers exist to produce runtime skill folders in `dist/`; source folders under `src/` are never installed directly.

## Source Repo Vs Runtime Install

The source repo contains authored material:

- `src/professional-skills`: 19 top-level professional skills.
- `src/foundation/capabilities`: 82 implemented foundation capabilities plus `_template`.
- `src/domain-extensions`: 7 optional domain extension skills.
- `src/registry`: `skills.yaml`, `capabilities.yaml`, `domain-extensions.yaml`, and `routing-rules.yaml`.

Runtime installs consume only generated outputs under `dist/`. Installed skill directories must contain `SKILL.md` at their root. Raw `src/`, raw registry folders, and foundation capability source trees are not installed in `recommended` or `full`.

## No Personal Asset Mapping

ChangeForge is self-contained. It does not ingest, scan, index, summarize, map, package, or install any personal technical asset library. It does not create toolbox mappings or assume any external personal knowledge base at runtime.

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

Domain extensions add domain-specific risk and routing rules. They are top-level in `full` and `dev`, and indexed by the router for profile-aware routing.

## Minimal Sufficient Routing

Routing should choose the smallest path that can safely complete the change. A small local bug fix should not trigger a full product program. A migration, authentication, payment, Web3, AI, or production rollout change should escalate until the affected contracts, rollback path, security review, and evidence gates are explicit.

## Risk Escalation

Escalate risk when the change may affect authentication, authorization, object-level permission, payment, billing, wallet keys, Web3 assets, user data, PII, file upload, AI prompts or retrieval, external integrations, webhooks, database migrations, production deployment, secrets, security dependencies, or irreversible operations.

Escalation means adding the relevant professional gates, domain extension, foundation capabilities, validation evidence, rollback criteria, and human approval point before release.
