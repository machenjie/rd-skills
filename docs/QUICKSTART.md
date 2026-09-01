# Quickstart

This guide starts at a fresh checkout and ends with your first successful rd-skills task. Run commands from the repository root.

## 1. Install

You need Python 3.11 or newer. Install the repository's declared dependencies:

```bash
python3 --version
python3 -m pip install .
```

Do not copy `src/` into an AI coding tool. The setup command builds and installs the supported artifacts for you.

## 2. Choose your AI coding tool

For a personal Codex installation:

```bash
python3 scripts/quickstart.py --agent codex --scope user
```

Use the matching tool name for another personal installation:

```bash
python3 scripts/quickstart.py --agent claude --scope user
python3 scripts/quickstart.py --agent copilot --scope user
python3 scripts/quickstart.py --agent cline --scope user
```

To keep rd-skills inside one project, provide that project root:

```bash
python3 scripts/quickstart.py --agent codex --scope project --target /absolute/path/to/project
```

Preview the exact plan without building or writing files:

```bash
python3 scripts/quickstart.py --agent codex --scope user --dry-run
```

Add `--verbose` when you need the command plan and detailed command output.

Supported hosts are `codex`, `claude`, `copilot`, `cline`, and `openai-api`.
Codex supports `project`, `user`, and `admin`; Claude, Copilot, and Cline support `project` and `user`.
OpenAI API produces zip files and has no installation scope.

For OpenAI API packages, run:

```bash
python3 scripts/quickstart.py --agent openai-api
```

For Codex admin scope, non-default targets, exact installed paths, and permission boundaries, use [Advanced Installation & Recovery](INSTALLATION.md#host-scope-and-default-targets).

## 3. Verify

Quickstart checks the installation automatically for Codex, Claude, Copilot, and Cline. You can run the check again:

```bash
python3 installers/doctor.py --agent codex --scope user
```

A healthy result is intentionally short:

```text
✓ rd-skills installed
✓ expected configuration found
✓ installation healthy

Next:
Open or restart Codex.
Start with $engineering-control-plane and describe the task in natural language.
The full rd-skills workflow is available on Codex.
```

Use `--verbose` to see inventory, source binding, host configuration, and digest details:

```bash
python3 installers/doctor.py --agent codex --scope user --verbose
```

Doctor verifies installation artifacts. It does not prove your AI coding tool loaded rd-skills. Open or restart the tool before the first task.

## 4. Run your first task

Open a small repository in your AI coding tool. If the table below gives a verified invocation for that host or surface, start the request with it.

### Host invocation

| Host or surface | Artifact delivery | Live Skill invocation | Full rd-skills workflow | Limit |
| --- | --- | --- | --- | --- |
| Codex | Skills + Agent Profiles | `$engineering-control-plane` | Available | Artifacts checked; live loading not proved |
| Claude Code | Skills + Agent Profiles | `/engineering-control-plane` | Available | Artifacts checked; live loading not proved |
| Copilot CLI | Skills + Agent Profiles | `/engineering-control-plane` | Available | Copilot CLI only |
| Cline | Skills only | Not established | Not established | Artifact delivery only |
| OpenAI API | Zip packages | Not applicable | API integration owns orchestration | API integration only |

Other Copilot surfaces are separate surfaces. Do not assume the Copilot CLI invocation or workflow availability applies to them.

For Codex, enter this normal engineering request:

```text
$engineering-control-plane

Payment callbacks sometimes create the same order twice.
Find the cause and fix it. Add the necessary regression test and verify the change.
```

Do not type `/engineering-control-plane` at the start of a Codex request. Codex reserves leading Slash input for its own command menu and uses the `$skill-name` form for Skills.

You do not need to know the responsible file, the exact test, or rd-skills internals. If you already know useful facts, add them below the request:

```text
The callback handler is probably under payments/.
Keep the public response unchanged.
The repository test command is pytest -q.
```

rd-skills should inspect the current code, identify the cause and affected boundary, make a bounded change, run relevant checks after the edit, have the change independently inspected, and report what changed and what remains unverified.

Continue with [Usage](USAGE.md) for everyday task examples and result interpretation.

## 5. If it did not work

- If quickstart failed, rerun the same command with `--verbose` and keep the first specific error.
- If doctor reports a file, configuration, permission, ownership, or migration problem, follow [Troubleshooting and Recovery](INSTALLATION.md#troubleshooting-and-recovery). Do not add `--force` until you have inspected the exact conflict.
- If doctor is healthy but the tool does not respond to the invocation in the table, restart the tool and confirm you installed for the same tool and scope. Doctor does not prove that a live host loaded the files.
- In Codex, type `$engineering-control-plane`, not `/engineering-control-plane`.
- For other Copilot surfaces, confirm that surface's current Skill invocation support instead of assuming the Copilot CLI syntax applies.
- For Cline, doctor can verify installed files, but the current host contract does not establish live Skill loading, an explicit invocation, validation, or independent review.
- If the task stops for a decision, answer the concrete scope, safety, compatibility, or production question instead of broadening the request implicitly.
- For a reproducible problem, use [Support](../SUPPORT.md) and remove secrets from the output you share.
