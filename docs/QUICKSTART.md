# Quickstart

This path starts at a fresh checkout and ends with a first bounded engineering
request. Run commands from the repository root.

## Prepare

rd-skills requires Python 3.11 or newer. Install its declared dependencies:

```bash
python3 --version
python3 -m pip install .
```

Do not install `src/` or source registries. The quickstart builds the selected
profile into `dist/` before using the installer.

## Choose A Profile

| Profile | Top-level Skills | Choose it for |
| --- | ---: | --- |
| `recommended` | 27 | Normal use; all Professional Skills with focused compiled guidance. |
| `full` | 40 | Normal use that also needs Domain Skills at top level. |
| `dev` | 190 | Skill authoring, registry work, and development visibility. |

Automatic selection currently chooses `recommended`. Specify `--profile` when
you need another profile. The normal profiles deliver 154/9 and 141/9
targeted-companion/routing-only entries respectively; `dev` delivers all 190
Skills at the top level. [Build profiles](BUILD_PROFILES.md) owns the exact
composition and manifest contract.

For client work, use the concrete target: ordinary Android and iOS/iPadOS
requests select their successor platform Domains. Cross-platform frameworks
also require the cross-platform Domain and every proven concrete target Domain.
The obsolete mobile Domain and compatibility mode have been removed. Removed
legacy Skill ids are unsupported and are not redirected.

## Choose A Host And Scope

Supported hosts are `codex`, `claude`, `copilot`, `cline`, and `openai-api`.
Codex supports `project`, `user`, and `admin`; Claude, Copilot, and Cline support
`project` and `user`. OpenAI API produces zip files and has no installation
scope. Codex, Claude, and Copilot receive four native Agent Profile files; Cline
and OpenAI API receive standard Skills only.

Use `user` for a personal default. Use `project` to keep installation inside a
specific checkout; replace `/absolute/path/to/project` below with the real
project root. Use Codex `admin` only with explicit administrative approval; see
[Installation](INSTALLATION.md#host-scope-and-default-targets).

## Preview Before Writing

Preview a user installation:

```bash
python3 scripts/quickstart.py --agent codex --scope user --profile recommended --dry-run
```

Preview a project installation:

```bash
python3 scripts/quickstart.py --agent claude --scope project --target /absolute/path/to/project --profile recommended --dry-run
```

The preview prints the build, install, and doctor plan but does not execute it.

## Install And Run Doctor

Run the selected plan without `--dry-run`:

```bash
python3 scripts/quickstart.py --agent codex --scope user --profile recommended
```

For project scope:

```bash
python3 scripts/quickstart.py --agent claude --scope project --target /absolute/path/to/project --profile recommended
```

Quickstart builds, installs, and runs doctor for Codex, Claude, Copilot, and
Cline. Repeat doctor independently when diagnosing a changed installation:

```bash
python3 installers/doctor.py --agent codex --scope user --profile recommended
```

A healthy result confirms the selected Skill count, manifest, source/core
bindings, and the host-specific Profile expectation. It describes declared
host enforcement and limitations; it does not prove that the real host loaded
the files.

## OpenAI API Zip Path

Preview and then generate the `recommended` bundle set:

```bash
python3 scripts/quickstart.py --agent openai-api --profile recommended --dry-run
python3 scripts/quickstart.py --agent openai-api --profile recommended
```

The second command builds and validates one zip per top-level Skill under
`dist/openai-api/zips/recommended/`. It does not install files or run runtime
doctor. See [OpenAI API zip output](INSTALLATION.md#openai-api-zip-output) for
the direct build/validation commands and package boundary.

## Submit A First Task

Slash Skill syntax is `/skill-name`. Open a small test repository in the
configured host. Start with `/engineering-control-plane`, then replace the
example path and command with real values:

```text
/engineering-control-plane

Goal: Add an empty-string check to `src/example.py` without changing its public API.
Acceptance: Empty input returns the existing validation error; valid input is unchanged.
Allowed scope: `src/example.py` and its existing test file only.
Verify: Run `python3 -m unittest tests.test_example`.
Stop if ownership, contract risk, or verification differs from this request.
```

Some hosts do not provide native Slash UI or autocomplete. Put the literal
`/engineering-control-plane` in the request text in that case. It expresses
routing intent; it does not prove native Slash support.

Expected outcome: the main profile chooses the Direct Task path, a task agent
implements and validates the latest edit, and a separate review agent inspects
the actual diff. The final handoff records changed files, commands and results,
freshness, unverified scope, and residual risk. Unknown ownership or material
risk switches to Analyzed Work before editing.

Continue with [Usage](USAGE.md) for three request patterns and expected decision
points. If setup fails, use [Installation troubleshooting](INSTALLATION.md#troubleshooting-and-recovery)
instead of adding `--force` without inspecting the conflict.
