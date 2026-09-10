# rd-skills

rd-skills helps AI coding tools turn a plain-language engineering request into a scoped change backed by current code and relevant validation.

## Why rd-skills

You describe the outcome. rd-skills selects relevant professional guidance,
finds the owning code, and validates the change after the final edit. An ordinary
local task can finish there. Deeper Analysis and independent Review are added
when your request or a concrete unresolved question calls for them.

## Install

Requirements: Python 3.11 or newer and a checkout of this repository. From the repository root:

```bash
python3 -m pip install .
python3 scripts/quickstart.py --agent codex --scope user
```

That command builds the current checkout, installs it for Codex, and checks the installed files. Other tools and project-local installation are covered in [Quickstart](docs/QUICKSTART.md).

## First task

Open or restart Codex, then enter:

```text
$engineering-control-plane

Payment callbacks sometimes create the same order twice.
Find the cause and fix it. Add the necessary regression test and verify the change.
```

Invocation syntax is host-specific. Codex uses `$engineering-control-plane`; see the [Quickstart host invocation table](docs/QUICKSTART.md#host-invocation) for verified Claude Code and Copilot CLI syntax, Cline's current limitation, and OpenAI API packaging.

You can add paths, acceptance criteria, constraints, or a test command when you know them. You do not need to investigate the repository first.

## What rd-skills does

For an implementation request, rd-skills:

- reads the current code before changing it;
- finds the owning code and checks nearby consumers;
- applies guidance suited to the task and its risks;
- makes the smallest complete change it can support;
- validates after the final edit;
- uses independent Review when you request it or a concrete risk needs a second judgment; and
- reports changed files, results, limits, and any decision still needed from you.

The implementing agent discovers local files, owners, and tests as part of the task. It asks for deeper Analysis when an unresolved decision could change the implementation, and stops for any missing authorization or user-owned decision.

## Supported hosts

Supported hosts are `codex`, `claude`, `copilot`, `cline`, and `openai-api`.

| Host or surface | Artifact delivery | Live Skill invocation | Full rd-skills workflow | Limit |
| --- | --- | --- | --- | --- |
| Codex | Skills + Agent Profiles | `$engineering-control-plane` | Available | Artifacts checked; live loading not proved |
| Claude Code | Skills + Agent Profiles | `/engineering-control-plane` | Available | Artifacts checked; live loading not proved |
| Copilot CLI | Skills + Agent Profiles | `/engineering-control-plane` | Available | Copilot CLI only |
| Cline | Skills only | Not established | Not established | Artifact delivery only |
| OpenAI API | Zip packages | Not applicable | API integration owns orchestration | API integration only |

Project scope requires `--target` with the project root. Exact paths, scopes, and recovery rules live in [Advanced Installation & Recovery](docs/INSTALLATION.md).

## Reading path

Continue with [Quickstart](docs/QUICKSTART.md) to verify installation, then
[Usage](docs/USAGE.md) for everyday requests and [How it works](docs/HOW_IT_WORKS.md)
for the small set of ideas behind the behavior. The [documentation map](docs/README.md)
continues into architecture, operating and subagent models, and maintainer material.

## Learn more

- [Documentation map](docs/README.md)
- [Advanced Installation & Recovery](docs/INSTALLATION.md)
- [How the system is structured](docs/HOOKLESS_ARCHITECTURE.md)
- [Support](SUPPORT.md)

This repository authors and validates rd-skills. Install built artifacts from `dist/`; never install `src/` directly.

Static panel evidence does not prove real-host Profile startup, wall-clock performance, provider behavior, production accuracy, or installed user experience.

Community policies: [Contributing](CONTRIBUTING.md), [Governance](GOVERNANCE.md), [Security](SECURITY.md), and [Code of Conduct](CODE_OF_CONDUCT.md).
