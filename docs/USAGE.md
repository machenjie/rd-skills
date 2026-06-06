# Usage

This guide explains how to use the `rd-skills` repository as the source for ChangeForge runtime skills. The normal flow is:

1. Build a runtime profile into `dist/`.
2. Install the built output into an agent runtime.
3. Ask the agent to use ChangeForge skills while planning, implementing, reviewing, testing, or releasing product/code changes.
4. Use `doctor`, `upgrade`, and `uninstall` to manage the installation.

Do not install `src/` directly. Runtime consumers use generated artifacts from `dist/` only.

## Choose A Profile

Use the smallest profile that fits the target runtime:

| Profile | Use When | Top-Level Runtime Skills |
| --- | --- | --- |
| `recommended` | Default for global/user installs. | 19 professional skills |
| `full` | Project installs where domain extensions should be visible as top-level skills. | 19 professional skills plus 7 domain extensions |
| `dev` | ChangeForge authoring, validation, or debugging only. | 19 professional skills plus 102 foundation capabilities plus 7 domain extensions |

In `recommended` and `full`, foundation capabilities are compiled into professional skill `references/` and loaded selectively by the selected skill route. They are not installed as top-level global skills.

## Build Runtime Artifacts

Build the profile before installing it:

```bash
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
```

The build writes deterministic runtime outputs under `dist/`, including agent-specific layouts for Codex, Claude Code, GitHub Copilot, and OpenAI API zip bundles.

The build also refreshes optional Codex and Claude project hook artifacts. Hooks
are warning-only execution reminders and are not installed by the first-stage
installer flow:

```text
dist/codex/project/.codex
dist/claude/project/.claude
```

See [HOOKS.md](HOOKS.md) before enabling hooks manually.

## Install For GitHub Copilot

Install to the current user's Copilot skills directory:

```bash
python3 scripts/build.py --profile full
python3 installers/install.py --agent copilot --scope user --profile full --dry-run
python3 installers/install.py --agent copilot --scope user --profile full
python3 installers/doctor.py --agent copilot --scope user --profile full
```

Install into a project so the skills travel with that project workspace:

```bash
python3 scripts/build.py --profile full
python3 installers/install.py --agent copilot --scope project --target /path/to/project --profile full --dry-run
python3 installers/install.py --agent copilot --scope project --target /path/to/project --profile full
python3 installers/doctor.py --agent copilot --scope project --target /path/to/project --profile full
```

For project scope, `--target` is the project root. The installer writes the agent-specific skills subdirectory inside that project.

## Install For Codex Or Claude Code

Codex project install:

```bash
python3 scripts/build.py --profile full
python3 installers/install.py --agent codex --scope project --target /path/to/project --profile full --dry-run
python3 installers/install.py --agent codex --scope project --target /path/to/project --profile full
python3 installers/doctor.py --agent codex --scope project --target /path/to/project --profile full
```

Codex user install:

```bash
python3 scripts/build.py --profile recommended
python3 installers/install.py --agent codex --scope user --profile recommended --dry-run
python3 installers/install.py --agent codex --scope user --profile recommended
python3 installers/doctor.py --agent codex --scope user --profile recommended
```

Claude Code project install:

```bash
python3 scripts/build.py --profile full
python3 installers/install.py --agent claude --scope project --target /path/to/project --profile full --dry-run
python3 installers/install.py --agent claude --scope project --target /path/to/project --profile full
python3 installers/doctor.py --agent claude --scope project --target /path/to/project --profile full
```

Claude Code user install:

```bash
python3 scripts/build.py --profile recommended
python3 installers/install.py --agent claude --scope user --profile recommended --dry-run
python3 installers/install.py --agent claude --scope user --profile recommended
python3 installers/doctor.py --agent claude --scope user --profile recommended
```

## Use The Skills In An Agent

After installation, the target agent runtime discovers the installed skill folders. If the runtime was already open and does not immediately see new skills, reload or restart that runtime.

Use `change-forge-router` when the requested work needs classification, routing, or risk sizing:

```text
Use change-forge-router to classify this request, select the minimum sufficient ChangeForge skill path, and list the evidence gates before implementation.
```

Use more specific skills when the work is already scoped:

```text
Use frontend-change-builder and quality-test-gate for this React form change.
```

```text
Use backend-change-builder, data-api-contract-changer, security-privacy-gate, and quality-test-gate for this API permission change.
```

```text
Use delivery-release-gate and reliability-observability-gate to review this deployment plan.
```

Common entry points:

| Skill | Use For |
| --- | --- |
| `change-forge-router` | Classifying a change and selecting the minimum sufficient skill path. |
| `change-intake-compiler` | Turning raw stakeholder input, issues, PR notes, or bug reports into a structured change request. |
| `change-impact-analyzer` | Mapping blast radius across product, UX, API, data, security, testing, release, and observability. |
| `task-dag-planner` | Breaking a change into ordered, reviewable, testable tasks. |
| `frontend-change-builder` | Frontend implementation, state, accessibility, API error handling, and browser behavior. |
| `backend-change-builder` | Backend validation, auth, authorization, transactions, idempotency, jobs, and error handling. |
| `data-api-contract-changer` | Schemas, migrations, DTOs, validation, compatibility, and API contracts. |
| `quality-test-gate` | Risk-based unit, integration, contract, E2E, migration, rollback, and regression testing strategy. |
| `security-privacy-gate` | Auth, object authorization, injection, secrets, dependency, privacy, and abuse-risk review. |
| `delivery-release-gate` | CI/CD, Docker, Kubernetes, environment configuration, rollout, rollback, and release checks. |

Domain extensions are top-level skills in `full` and `dev`. Use them when the work clearly involves AI/ML, big data, IoT/embedded, low-level systems, mobile, payment/trading, or Web3 concerns.

## OpenAI API Zip Output

OpenAI API output is zip-only. Build or package the desired profile, then consume the generated zip bundles through the hosted skill workflow that expects one skill per zip:

```bash
python3 scripts/build.py --profile recommended
python3 scripts/package.py --profile recommended
python3 installers/install.py --agent openai-api --profile recommended --dry-run
```

Zip bundles are written to:

```text
dist/openai-api/zips/<profile>
```

Each zip contains exactly one top-level skill folder and one root `SKILL.md`.

## Upgrade An Existing Install

After pulling repository changes or editing source skills, rebuild the intended profile and upgrade the managed install:

```bash
python3 scripts/build.py --profile full
python3 installers/upgrade.py --agent copilot --scope user --profile full --dry-run
python3 installers/upgrade.py --agent copilot --scope user --profile full
python3 installers/doctor.py --agent copilot --scope user --profile full
```

For project installs, pass the same project root used during install:

```bash
python3 installers/upgrade.py --agent copilot --scope project --target /path/to/project --profile full --dry-run
```

Upgrade replaces only ChangeForge-managed skill directories recorded in `.changeforge-install-manifest.json` and preserves unrelated skills.

## Uninstall Managed Skills

Uninstall removes only skill directories listed in the ChangeForge manifest:

```bash
python3 installers/uninstall.py --agent copilot --scope user --dry-run
python3 installers/uninstall.py --agent copilot --scope user
```

For project installs:

```bash
python3 installers/uninstall.py --agent copilot --scope project --target /path/to/project --dry-run
python3 installers/uninstall.py --agent copilot --scope project --target /path/to/project
```

## Authoring Workflow

When changing ChangeForge itself, edit source content under `src/`, then validate, build, and reinstall from `dist/`:

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-domain-extensions.py
python3 scripts/validate-registry.py
python3 scripts/validate-skill-body-links.py
python3 scripts/validate-stage-routing-architecture.py
python3 scripts/audit-skill-content.py
python3 scripts/audit-professionalism-coverage.py
python3 scripts/validate-skill-content-size.py
python3 scripts/eval-routing.py
python3 scripts/validate-hooks.py
python3 scripts/eval-agent-behavior.py
python3 -m unittest discover -s tests
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/run-codegen-benchmarks.py --limit 3
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-installation.py
```

`scripts/audit-skill-content.py` writes the advisory content audit to
`reports/skill-content-audit.md` and `reports/skill-content-audit.json`; it never
fails the workflow. `scripts/validate-skill-content-size.py` warns when a `SKILL.md`
body, section, table, or duplicated block crosses a budget defined in
[SKILL_CONTENT_GOVERNANCE.md](SKILL_CONTENT_GOVERNANCE.md) without a recorded
exception in `config/skill-content-exceptions.yaml`; it is warning-only by default
and only exits non-zero with `--strict`. Neither tool blocks the build.

`scripts/validate-stage-routing-architecture.py` is a blocking structural check: it
verifies that the engineering stage model, the `engineering-stage-professionalism`
launcher, the router Stage Professionalism contract and stage manifest, and the
stage routes are present and that no language-deep checklist or stage matrix is
copied into the router or launcher body. `scripts/audit-professionalism-coverage.py`
is review-only: it writes `reports/professionalism-coverage.md` and
`reports/professionalism-coverage.json` to flag stage/surface ownership gaps,
over-long bodies, duplicated rules, and broad triggers, and exits 0 unless run with
`--strict`. It does not block the build.

Then use `installers/upgrade.py` for an existing managed install, or `installers/install.py --backup` when replacing a managed install intentionally.

## Telemetry Review Workflow

When the optional hook runtime is enabled, hooks record a runtime fact log in the
user cache. You can review it offline and promote findings into golden cases.
Telemetry never edits skill rules; promotion is always a human decision.

```bash
# Review real agent behavior and write a report plus suggestions:
python3 scripts/review-agent-telemetry.py

# Turn one reviewed suggestion into a candidate (dry run, then write):
python3 scripts/promote-telemetry-suggestion.py --id <suggestion-id> --suggestions <path>
python3 scripts/promote-telemetry-suggestion.py --id <suggestion-id> --suggestions <path> --write

# Score captured, human-reviewed agent outputs against expected route manifests:
python3 scripts/eval-agent-behavior.py

# Summarize telemetry from doctor (advisory only):
python3 installers/doctor.py --telemetry-root ~/.cache/changeforge/telemetry
```

See [TELEMETRY.md](TELEMETRY.md) for the full data flow, privacy guarantees, and
the route manifest contract.

## Troubleshooting

Run doctor first when a runtime does not see expected skills or a target looks inconsistent:

```bash
python3 installers/doctor.py --agent copilot --scope user --profile full
python3 installers/doctor.py --agent copilot --scope project --target /path/to/project --profile full
```

Common fixes:

| Symptom | Fix |
| --- | --- |
| No skills were installed. | Build the selected profile first with `scripts/build.py`. |
| Install refuses to overwrite a matching directory. | Review the unmanaged conflict, then move it, uninstall the managed copy, or rerun with `--force` only when replacement is intentional. |
| Doctor reports an old source version. | Rebuild and run `installers/upgrade.py` for the same agent, scope, target, and profile. |
| Doctor reports duplicate skill names. | Keep one active copy in the intended scope and remove or uninstall the duplicate. |
| The agent does not see newly installed skills. | Reload or restart the target agent runtime after confirming doctor passes. |

## Safety Boundaries

- Install only from `dist/`, never directly from `src/`.
- Do not install raw registry files or `src/registry` as runtime content.
- Do not create or install personal asset mappings.
- Do not expect ChangeForge to ingest, scan, index, summarize, or map a personal knowledge corpus.
- Treat `references/` as selected support material. The selected professional skill reads only the references required by its route and L1/L2/L3/L4/L5 loading policy.
