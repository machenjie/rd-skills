# Validation

This is the canonical developer command set for ChangeForge source, runtime
governance, deterministic fixtures, and local release checks. Other docs should
link here instead of copying the full checklist.

Use `python3`. This repository does not define a `test-suite/run.sh` entrypoint;
the canonical local test runner is `python3 -m unittest discover -s tests`.
Live Codex benchmark runs are opt-in and are not part of default CI or doctor.

## Fast Source Invariants

Run these before handing off changes that touch source governance, skills,
runtime hooks, validation, memory, graph intelligence, or routing behavior:

```bash
python3 scripts/validate-src-invariants.py
python3 scripts/validate-skills.py
python3 scripts/validate-validation-broker.py
python3 scripts/validate-hooks.py
python3 scripts/validate-project-memory.py
python3 scripts/validate-skill-efficacy-benchmarks.py
```

When repository graph or context-pack behavior changes, build temporary
artifacts and validate those exact artifacts:

```bash
python3 scripts/index-repository.py --target . --out /tmp/changeforge-repo-graph.json
python3 scripts/validate-repository-graph.py --graph /tmp/changeforge-repo-graph.json
python3 scripts/build-context-pack.py --task "release validation" --target . --graph /tmp/changeforge-repo-graph.json --out /tmp/changeforge-context-pack.json
python3 scripts/validate-context-pack.py --context-pack /tmp/changeforge-context-pack.json
```

## Focused Governance Tests

Use focused unittest discovery when the change is limited to one governance
surface:

```bash
python3 -m unittest discover -s tests/runtime_governance
python3 -m unittest discover -s tests/hook_runtime
python3 -m unittest discover -s tests/project_memory
python3 -m unittest discover -s tests/repository_intelligence
python3 -m unittest discover -s tests/validation_broker
python3 -m unittest discover -s tests/skill_efficacy
python3 -m unittest discover -s tests/reports
```

These suites cover adapter parity and degraded closure semantics, evidence
ledger and closure sequencing, Project Memory stale-source gates, repository
graph freshness/confidence/source-of-truth behavior, Validation Broker command
mapping/freshness policy, and skill-efficacy context-budget fixtures.

Stop closure treats a missing `changeforge_stage_route` / `stage_route` as
missing evidence for non-trivial engineering tasks; stale, degraded, unknown, or
missing evidence cannot be counted as ready closure. Project Memory retrieval
sorts current closure evidence ahead of stale historical hints, and repository
graph validation checks schema-v2 semantic value domains instead of only field
presence.

Governance docs are not automatically docs-only. Changes to hook, validation,
quality, stage, operating-model, professionalism, benchmark, eval, or routing
reports can change execution or evidence semantics, so Validation Broker routes
them through skill-efficacy and focused governance checks. Plain usage or typo
docs can still remain docs-only when no governance behavior surface matches.

Source invariant validation treats runtime governance adapter, event, gate, and
Validation Broker registry import failures as hard errors. Hook docs matrix,
adapter consistency, and broker path mappings are not considered checked when a
required module cannot import.

## Skill Behavior Evals

Use these deterministic checks for routing, reference-loading, professional
quality, and behavior-fixture regressions:

```bash
python3 scripts/eval-routing.py
python3 scripts/validate-stage-routing-architecture.py
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-skill-professionalism.py --coverage-matrix
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-professionalism-regression.py
python3 scripts/validate-professionalism-regression.py --strict
python3 scripts/validate-professional-routing-coverage.py
python3 scripts/eval-professional-agent-samples.py --promoted-only --strict
python3 scripts/eval-pressure-behavior.py
```

Run the extended routing fixture comparison only when updating or verifying
captured actual router outputs:

```bash
python3 scripts/eval-routing.py --candidate-output-dir evals/routing-outputs
```

## Full Local

Run the full local suite before release handoff or after cross-surface changes:

```bash
python3 scripts/validate-capabilities.py
python3 scripts/validate-domain-extensions.py
python3 scripts/validate-registry.py
python3 scripts/validate-skill-body-links.py
python3 scripts/validate-skill-content-size.py
python3 scripts/audit-skill-content.py
python3 scripts/validate-examples.py
python3 scripts/validate-productization-assets.py
python3 scripts/validate-open-source-readiness.py
python3 scripts/validate-report-consistency.py
python3 -m unittest discover -s tests
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/run-codegen-benchmarks.py --limit 3
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-runtime-reference-links.py
python3 scripts/validate-installation.py
python3 scripts/validate-marketplace-index.py --profile recommended
python3 scripts/validate-marketplace-index.py --profile full
python3 scripts/validate-marketplace-index.py --profile dev
```

## Doctor And CI

`installers/doctor.py` is a structural health check. It prints skill registry,
capability registry, source/dist boundary, hook adapter matrix, Validation
Broker, Project Memory, repository graph freshness, and skill-efficacy fixture
status without running expensive test suites.

```bash
python3 installers/doctor.py --agent codex --scope user --profile recommended
python3 installers/doctor.py --agent codex --scope project --target /path/to/project --profile full --check-hooks
```

CI runs the fast source invariants, deterministic skill-efficacy fixtures,
focused governance tests, productization smoke checks, and the full unittest
suite. It does not run live Codex benchmarks by default.

## Live Benchmark Boundary

Listing and dry-run validation are safe as local smoke checks:

```bash
python3 scripts/run-codex-live-benchmarks.py --list
python3 scripts/run-codex-live-benchmarks.py --benchmark-mode ablation --auth-policy borrow-current --benchmark security/ssrf-url-allowlist --dry-run --out /tmp/changeforge-codex-live-ablation-dry-run
python3 scripts/validate-codex-live-benchmark-reports.py --run-dir /tmp/changeforge-codex-live-ablation-dry-run
```

Real live benchmark runs require explicit maintainer intent, temp `HOME`, hidden
user-level skills/hooks/config/rules, `--ignore-user-config`, `--ignore-rules`,
and report consistency validation before any public claim is updated.
