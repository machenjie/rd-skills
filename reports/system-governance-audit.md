# System Governance Audit

Generated: 2026-06-25

This audit summarizes the developer-visible integration path for source
invariants, runtime governance, Project Memory, repository intelligence,
Validation Broker, adapter parity, skill efficacy, and context-budget controls.
It records structural/local evidence only; live benchmark and live runtime
claims are not inferred from these checks.

## Coverage Summary

| Area | Coverage | Evidence |
| --- | --- | --- |
| Source invariant coverage | Present | `python3 scripts/validate-src-invariants.py` passed and covers registries, capability references, source/runtime boundary, hook runtime, Validation Broker, Project Memory, and repository intelligence invariants. |
| Evidence ledger sequence coverage | Present | `python3 -m unittest discover -s tests/runtime_governance` passed 87 tests, including evidence ledger and closure-contract sequencing. |
| Memory stale-source gate coverage | Present | `python3 scripts/validate-project-memory.py` passed; `python3 -m unittest discover -s tests/project_memory` passed 31 tests. |
| Graph confidence/freshness coverage | Present | Repository graph index/validate passed with 4327 files and 8702 edges; context pack validate passed with 13 relevant files and 11 validation candidates; `tests/repository_intelligence` passed 27 tests. |
| Adapter parity coverage | Present | `python3 scripts/validate-hooks.py` passed and printed the runtime adapter matrix; `tests/hook_runtime` passed 314 tests; `tests/runtime_governance` passed 87 tests. |
| Skill efficacy/context budget coverage | Present | `python3 scripts/validate-skill-efficacy-benchmarks.py` passed 3 benchmark fixtures; `tests/skill_efficacy` passed 9 tests; routing coverage passed 118 golden cases and 15 runtime fixtures. |
| Report evidence consistency | Present | `python3 scripts/validate-report-consistency.py` passed; `tests/reports` passed 5 tests. |
| Doctor structural status | Present | `python3 installers/doctor.py --agent codex --scope user` passed and printed all governance source statuses as present. |

## Daily Maintenance Path

- Canonical command source: `docs/VALIDATION.md`.
- README, Usage, Quality Model, Installation, Hooks, Telemetry, Operating Model,
  Engineering Stage Model, and Professionalism Enhancement Standard now link or
  summarize rather than duplicating long validation lists.
- CI exposes separate steps for source governance invariants, core validation,
  skill behavior deterministic fixtures, focused governance tests,
  productization smoke, and full unittest discovery.
- Doctor prints structural status for skill registry, capability registry,
  source/dist boundary, hook adapter matrix, Validation Broker, Project Memory,
  repository graph freshness support, and skill efficacy fixtures. It does not
  execute expensive test suites.

## Long Skill Context Slimming

The current content audit still identifies low-priority P2 body-size candidates:
`quality-test-gate`, `security-privacy-gate`, `delivery-release-gate`, and the
`agent-execution-discipline` capability. No skill content was moved in this
integration pass because the requested work was docs/CI/doctor/report plumbing
and safe slimming would require a separate behavior-preservation review of
reference loading and generated compiled references.

## Commands Run

| Command | Result |
| --- | --- |
| `python3 scripts/validate-src-invariants.py` | Passed. |
| `python3 scripts/validate-skills.py` | Passed; validated 21 professional skills. |
| `python3 scripts/validate-validation-broker.py` | Passed. |
| `python3 scripts/validate-hooks.py` | Passed; printed adapter matrix. |
| `python3 scripts/validate-project-memory.py` | Passed. |
| `python3 scripts/validate-skill-efficacy-benchmarks.py` | Passed; validated 3 benchmark fixtures. |
| `python3 scripts/validate-stage-routing-architecture.py` | Passed. |
| `python3 scripts/eval-routing.py` | Passed; 118 golden cases. |
| `python3 scripts/validate-professional-routing-coverage.py` | Passed; 118 routing cases, 15 runtime fixtures, 0 findings. |
| `python3 scripts/validate-report-consistency.py` | Passed. |
| `python3 scripts/index-repository.py --target . --out /tmp/changeforge-repo-graph.json` | Passed; wrote 4327 files and 8702 edges. |
| `python3 scripts/validate-repository-graph.py --graph /tmp/changeforge-repo-graph.json` | Passed. |
| `python3 scripts/build-context-pack.py --task "release validation" --target . --graph /tmp/changeforge-repo-graph.json --out /tmp/changeforge-context-pack.json` | Passed. |
| `python3 scripts/validate-context-pack.py --context-pack /tmp/changeforge-context-pack.json` | Passed; 13 relevant files and 11 validation candidates. |
| `python3 installers/doctor.py --agent codex --scope user` | Passed; governance source status present. |
| `python3 installers/doctor.py --agent codex --scope user --profile recommended` | Failed due local installed profile being `full`, not `recommended`; this is an installation-state mismatch, not a governance status failure. |
| `python3 -m py_compile installers/doctor.py` | Passed. |
| `python3 -m unittest discover -s tests/runtime_governance` | Passed; 87 tests. |
| `python3 -m unittest discover -s tests/hook_runtime` | Passed; 314 tests. |
| `python3 -m unittest discover -s tests/project_memory` | Passed; 31 tests. |
| `python3 -m unittest discover -s tests/repository_intelligence` | Passed; 27 tests. |
| `python3 -m unittest discover -s tests/validation_broker` | Passed; 41 tests. |
| `python3 -m unittest discover -s tests/skill_efficacy` | Passed; 9 tests. |
| `python3 -m unittest discover -s tests/reports` | Passed; 5 tests. |
| `python3 -m unittest discover -s tests` | Passed; 777 tests. |
| `command -v python` | Not available in this environment. |
| `python3 -m pytest --version` | Failed; pytest is not installed. |

## Not Run

- Real Codex live benchmark execution was not run. Live benchmark commands remain
  opt-in and must not run by default in CI or doctor.
- Full build/profile productization smoke (`build.py --profile recommended/full/dev`
  plus `validate-installation.py`) was not rerun in this pass; the P2 validation
  target was source governance, docs, CI, doctor, and local test coverage.
- `pytest` commands were not run because this environment has no `python`
  executable and no installed `pytest` module. The canonical local commands use
  `python3 -m unittest`.

## Known Gaps

- Long skill context slimming remains advisory and should be handled as a
  separate behavior-preserving content migration if maintainers choose to move
  heavy sections into references.
- Structural fixtures and deterministic validators do not prove live runtime
  pass-rate, token overhead, turn overhead, or real adapter telemetry.
- The local Codex user install is currently `full`; specifying
  `--profile recommended` in doctor correctly reports a profile mismatch.
