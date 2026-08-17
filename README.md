# rd-skills

rd-skills is an engineering control plane for AI coding agents. It routes one
task to one Professional Skill, separates analysis, implementation, and review,
loads focused guidance only when needed, and requires current evidence before
completion.

This repository authors and validates rd-skills Skills and Agent Profiles.
Install built artifacts from `dist/`; never install `src/` directly.

## Start

Requirements: Python 3.11 or newer and a checkout of this repository.

```bash
python3 --version
python3 -m pip install .
```

Choose a profile:

- `recommended`: normal use.
- `full`: also exposes Domain Skills at the top level.
- `dev`: Skill authoring and registry development.

Supported hosts are `codex`, `claude`, `copilot`, `cline`, and `openai-api`.
Project scope requires `--target` with the project root. See
[Installation](docs/INSTALLATION.md) for supported scopes and paths.

Preview a Codex user installation:

```bash
python3 scripts/quickstart.py --agent codex --scope user --profile recommended --dry-run
```

Install and run the built-in checks:

```bash
python3 scripts/quickstart.py --agent codex --scope user --profile recommended
python3 installers/doctor.py --agent codex --scope user --profile recommended
```

Use another host or project scope through [Quickstart](docs/QUICKSTART.md).

## Submit A First Task

Slash Skill syntax: `/skill-name`.

Start with `/engineering-control-plane`. Replace the sample paths and command
with facts from a small test repository:

```text
/engineering-control-plane

Goal: Add an empty-string check to src/example.py without changing its public API.
Acceptance: Empty input returns the existing validation error; valid input is unchanged.
Allowed scope: src/example.py and its existing test file only.
Verify: Run python3 -m unittest tests.test_example.
Stop if: Ownership, the public contract, or the verification command differs.
```

Some hosts do not provide native Slash UI or autocomplete. Enter the literal
`/engineering-control-plane` in the request text in that case. It expresses
routing intent; it does not prove native Slash support.

A bounded implementation should produce:

- one primary Professional Skill;
- implementation by a `task-agent`;
- validation after the final edit;
- independent review by a `review-agent`;
- a handoff with changed files, results, Unverified scope, and Residual risk.

Unknown ownership, placement, impact, or verification switches the request to
Analyzed Work before editing. [Usage](docs/USAGE.md) provides Direct Task,
Analyzed Work, and review-only examples.

## Boundaries

- `main-control-agent` dispatches only.
- `analysis-agent` reads and analyzes; it alone may perform claim-triggered,
  read-only external evidence lookup when the host explicitly supports it.
- `task-agent` implements and validates bounded work.
- `review-agent` independently reviews without repairing its own findings.
- Shared-workspace writes are serial.
- Foundation and Domain guidance loads only for a concrete task signal.

For Analyzed Work, the current Engineering Brief is the sole operational
analysis authority and contains the complete First Executable Slice. Main
dispatches that Task Contract v2 verbatim; DAGs and handoffs only project it.
Discovery does not expand repair scope: only current-task findings may enter the
repair loop, scope blockers return to analysis, and adjacent findings are
reported without preempting the requested task. Review depth comes from the
existing Effective Level rather than a separate review-level system.

## Evidence Limits

Repository checks cover static contracts, deterministic and captured fixtures,
builds, packages, and simulated installation. They do not prove real-host
startup, host-enforced permissions, wall-clock performance, production
accuracy, provider behavior, official marketplace publication, or installed
user experience.

## Documentation

- [Documentation map](docs/README.md)
- [Quickstart](docs/QUICKSTART.md)
- [Installation and recovery](docs/INSTALLATION.md)
- [Usage](docs/USAGE.md)
- [Validation](docs/VALIDATION.md)
- [Release](docs/RELEASE.md)
- [Skill content governance](docs/SKILL_CONTENT_GOVERNANCE.md)

Community policies: [Contributing](CONTRIBUTING.md),
[Governance](GOVERNANCE.md), [Security](SECURITY.md),
[Support](SUPPORT.md), and [Code of Conduct](CODE_OF_CONDUCT.md).
