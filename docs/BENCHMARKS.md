# Benchmarks

ChangeForge benchmarks are release evidence, not marketing claims. They are local, deterministic, and based on repository fixtures, registries, generated reports, and build manifests. Missing data must remain `unknown` or `not_collected`.

## What Is Measured

| Area | Evidence Source | Command |
| --- | --- | --- |
| Routing correctness | Routing fixtures and expected outputs. | `python3 scripts/eval-routing.py` |
| Professional skill coverage | Professionalism eval report. | `python3 scripts/eval-skill-professionalism.py` |
| Foundation capability coverage | Coverage matrix report. | `python3 scripts/eval-skill-professionalism.py --coverage-matrix` |
| Reference loading precision | Runtime reference links and build manifests. | `python3 scripts/validate-runtime-reference-links.py` |
| Hook validation | Hook runtime validators and tests. | `python3 scripts/validate-hooks.py` |
| Profile build reproducibility | Build manifests for `recommended`, `full`, and `dev`. | `python3 scripts/build.py --profile recommended && python3 scripts/build.py --profile full && python3 scripts/build.py --profile dev` |
| Installation validation | Installer/doctor validation. | `python3 scripts/validate-installation.py` |
| Skill efficacy structural fixtures | evals/skill-efficacy | `python3 scripts/validate-skill-efficacy-benchmarks.py` |
| Business semantic structural fixtures | Business Semantic Pack schemas, deterministic BSP routing/review fixtures under `evals/business-semantic`, and static generator oracle-boundary checks. | `python3 scripts/validate-business-semantic-generator.py`, `python3 scripts/validate-business-semantic-pack.py`, `python3 scripts/generate-business-semantic-actuals.py --check`, `python3 scripts/eval-business-semantic-routing.py`, and `python3 scripts/eval-business-semantic-review.py` |
| Context Control Plane overhead | Deterministic fixtures for context budget, selected/skipped references, JIT packs, tool-output boundaries, compaction snapshots, route repair summaries, and overhead policy. | `python3 scripts/eval-context-control-plane.py` |
| Executor adapter structural fixtures | Deterministic adapter fixtures and sanitized telemetry sample under `evals/executor-adapter` and `reports/`. | `python3 scripts/eval-executor-adapters.py` |
| Activation precision benchmark | Deterministic activation fixtures for stage, skill, capability, reference, language, risk, and overroute precision against the built hook runtime. | `python3 scripts/eval-activation-precision.py --mode built --runtime-root dist/codex/project/.codex/hooks` |
| Codegen benchmark smoke | Codegen benchmark manifest and limited run. | `python3 scripts/validate-codegen-benchmarks.py` and `python3 scripts/run-codegen-benchmarks.py --limit 3` |
| Codex CLI live pass-rate benchmark | Explicit opt-in local Codex CLI runs over selected codegen starter repos, summarized from assertion-backed validated run artifacts. | `python3 scripts/run-codex-live-benchmarks.py --list` and `python3 scripts/validate-codex-live-benchmark-reports.py --summary reports/codex-live-benchmark-summary.json` |
| Codex CLI live capability coverage | Core ChangeForge capability matrix coverage from assertion-backed live cases, process traces, route manifests, and bounded evidence. | `python3 scripts/run-codex-live-benchmarks.py --list` and `python3 scripts/validate-codex-live-benchmark-reports.py --summary reports/codex-live-benchmark-summary.json` |
| Professionalism regression | Baseline-aware regression check. | `python3 scripts/validate-professionalism-regression.py --strict` |

## Scorecard Generation

Generate a public scorecard from the local evidence already present in `reports/` and `dist/`:

```bash
python3 scripts/generate-professional-scorecard.py --out reports/professional-scorecard.md --json-out reports/professional-scorecard.json
```

Render the reader-facing dashboard from the scorecard JSON:

```bash
python3 scripts/render-scorecard-dashboard.py --scorecard reports/professional-scorecard.json --out docs/SCORECARD_DASHBOARD.md --readme README.md
```

Generate the public benchmark summary snapshot:

```bash
python3 scripts/generate-public-benchmark-summary.py --out reports/public-benchmark-summary.md --json-out reports/public-benchmark-summary.json
```

Committed public benchmark snapshots do not embed the current Git HEAD. Release
artifacts or CI jobs that need exact provenance can provide it explicitly:

```bash
python3 scripts/generate-public-benchmark-summary.py --source-commit "$GITHUB_SHA" --out reports/public-benchmark-summary.md --json-out reports/public-benchmark-summary.json
```

The generator does not mark a validator as passed just because a command name exists. If a tool does not emit a machine-readable report, that status is reported as `not_collected` and the verification command is listed.

Skill efficacy benchmarks are currently structural/local evidence. The current
fixtures validate routing and evidence shape; they do not provide live pass-rate
evidence, empirical before/after agent performance, or measured token/turn
overhead.

Business semantic fixtures are structural/local evidence for source-backed
semantic packs, route selection, overroute avoidance, review findings, memory
verdict buckets, and golden-case expectations. The routing and review evals now
compare expected fixture fields with deterministic actual outputs under
`evals/business-semantic-outputs/`; those actuals are generated and checked by
`generate-business-semantic-actuals.py --check`. The generator reads fixture
input signals, `input_route_hint`, resolver/routing rules, and source/diff
context only; `validate-business-semantic-generator.py` statically rejects direct
generator access to `expected_*` oracle fields. `input_route_hint` is the only
route override input and is limited to `stage`,
`business_semantic_pack_required`, and `business_semantic_scope`; fixture authors
must add `route_hint_diff_rationale` when it intentionally differs from
`expected_route`. `expected_*` fields are oracle assertions for evals, not
generator inputs. Routing fixtures compare selected skills, selected
capabilities, quality gates, BSP sections, BSP scope, canonical triggers, and
structured reference decisions, including forbidden skills/capabilities and max
selection limits to catch over-route failures. Review fixtures check
`expected_evidence`, not only finding text, while actual review evidence is
derived from source/diff snippets, prompt, and routing triggers. Actual metadata
uses `review_source: deterministic source/diff/prompt/trigger review skeleton`
to avoid implying a live agent review or generic semantic review engine. The
schema validator checks both JSON Schema valid/invalid samples and semantic
invariants, including non-empty rule `reason_codes` and `entry_points`. They do
not prove live agent behavior, live LLM behavior, production routing quality, or
live business correctness, and memory or repository graph signals remain
selectors until current source, owner review, user source, or validation evidence
confirms the claim. BSP selected/skipped references require structured rationale, not
string lists.

Executor adapter benchmarks are also structural/local evidence. They validate
canonical event recognition, adapter degradation, privacy redaction, validation
freshness, and closure effects across supported executor runtimes. The generated
runtime telemetry fixture sample is bounded and sanitized, but it is not live
runtime telemetry; live runtime telemetry, live pass-rate, token overhead, and
turn overhead remain `not_collected` unless separately measured or collected.

Context Control Plane evidence is split deliberately: structural fixture pass,
live pass-rate, live runtime telemetry, token overhead, and turn overhead are
separate evidence types. A passing structural context-control eval does not
make high token overhead a success. High overhead without pass-rate improvement
is reported as `partial` and must not be described as Context Control Plane
quality improvement. Live benchmark commands remain opt-in and are not default
validation.

Codex CLI live benchmarks are optional local evidence. They are disabled by
default because they may use local credentials, network access, model quota, and
writable candidate repositories. Dry-run and skipped reports are valid
diagnostics, but they are not publishable benchmark evidence.

The canonical strict report path, `reports/codex-live-benchmark-summary.*`,
is reserved for the strongest currently available validated strict benchmark
summary. A clean-paired smoke run must be retained as
`reports/codex-live-smoke-summary.*` or a run-local artifact under
`reports/codex-live-runs/<run-id>/`; it must not overwrite the canonical
strict ablation summary and must not be counted as broad improvement evidence.

```bash
python3 scripts/run-codex-live-benchmarks.py --list
python3 scripts/run-codex-live-benchmarks.py --benchmark-mode ablation --auth-policy borrow-current --benchmark security/ssrf-url-allowlist --dry-run --out /tmp/changeforge-codex-live-ablation-dry-run
python3 scripts/validate-codex-live-benchmark-reports.py --run-dir /tmp/changeforge-codex-live-ablation-dry-run
```

To run a strict clean A/B smoke benchmark, enable the explicit live gate and
borrow Codex authentication only. This uses temp `HOME`, hides user-level
skills/hooks/config/rules, passes `--ignore-user-config` and `--ignore-rules`,
runs `baseline_clean` against `skills_with_hooks_clean`, and is publishable
only when baseline contamination is absent:

```bash
CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK=1 \
python3 scripts/run-codex-live-benchmarks.py \
  --benchmark security/ssrf-url-allowlist \
  --benchmark-mode clean-paired \
  --auth-policy borrow-current \
  --runs 1 \
  --profile recommended \
  --sandbox workspace-write \
  --out reports/codex-live-runs/clean-auth-borrowed-$(date +%Y%m%d-%H%M%S) \
  --publish-summary
```

This single-case command is useful for validating the pipeline, not for broad
rd-skills improvement claims. It is smoke evidence: scorecard and public
summary status should remain `partial` when `evidence_scope=smoke`,
`evidence_scope_ready=false`, or `effect_status=inconclusive`.

For a fully isolated strict A/B run, provide an API key only to the subprocess
environment and keep both `HOME` and `CODEX_HOME` temporary:

```bash
CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK=1 CODEX_API_KEY=... \
python3 scripts/run-codex-live-benchmarks.py \
  --benchmark security/ssrf-url-allowlist \
  --benchmark-mode clean-paired \
  --auth-policy isolated-api-key \
  --runs 1 \
  --profile recommended \
  --sandbox workspace-write \
  --out reports/codex-live-runs/clean-isolated-api-key-$(date +%Y%m%d-%H%M%S) \
  --publish-summary
```

To run the core strong-evidence hook ablation subset, use the same clean
auth-borrowing policy with `baseline_clean`, `skills_only_clean`, and
`skills_with_hooks_clean`. The core tier is currently 16 assertion-backed cases
and is the focused capability/pass-rate subset used by the latest canonical
summary. Use `--runs 3` or higher when making repeated-run local evidence
claims:

```bash
CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK=1 \
python3 scripts/run-codex-live-benchmarks.py \
  --benchmark-mode ablation \
  --auth-policy borrow-current \
  --runs 3 \
  --profile recommended \
  --sandbox workspace-write \
  --tier core \
  --out reports/codex-live-runs/ablation-auth-borrowed-$(date +%Y%m%d-%H%M%S) \
  --publish-summary
```

To cover all registered publishable assertion-backed live cases, use
`--tier all`. This includes core and Level 1 publishable assertion cases and
excludes telemetry-only experimental cases:

```bash
CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK=1 \
python3 scripts/run-codex-live-benchmarks.py \
  --benchmark-mode ablation \
  --auth-policy borrow-current \
  --runs 3 \
  --profile recommended \
  --sandbox workspace-write \
  --tier all \
  --out reports/codex-live-runs/ablation-all-auth-borrowed-$(date +%Y%m%d-%H%M%S) \
  --publish-summary
```

Publishable assertion-backed live cases currently include the original
`security`, `backend`, `devex`, `structure`, and `reliability` quality cases
plus core capability cases for professional injection, staged injection,
repository graph evidence, project memory, validation freshness, full
PDD/DDD/SDD/TDD/review flow, minimal-correct reuse, pressure resistance,
repair/re-review, and logging/security decisions. Telemetry-only cases are
listed in run outputs but do not contribute to pass-rate or capability coverage
evidence.

Coverage claims must distinguish registered coverage from actual run coverage.
When Level 1 cases are registered but not run, the live summary must keep them
in `registered_but_not_run_cases`; pass-rate and capability results from a core
run must not be promoted as full publishable assertion coverage.

The scorecard intentionally splits Codex live evidence into two dimensions:
the pass-rate benchmark shows assertion-backed codegen quality deltas, while
the capability coverage dimension shows whether rd-skills core capabilities
were explicitly covered by live cases and evidence. A pass-rate `pass` must not
be read as broad core capability coverage unless the capability coverage
dimension is also `pass`.

Only ablation evidence with all of `baseline_clean`, `skills_only_clean`, and
`skills_with_hooks_clean`, at least 5 assertion-backed cases, and at least 3
runs per variant can support broad local improvement evidence. The ablation
deltas distinguish hook increment from skill-only increment:
`skills_only_clean_vs_baseline_clean`,
`skills_with_hooks_clean_vs_skills_only_clean`, and
`skills_with_hooks_clean_vs_baseline_clean` must all be present. Clean-paired
smoke compares baseline directly with skills plus hooks and can diagnose the
pipeline, but it cannot isolate hook increment because it lacks
`skills_only_clean`.

Process trace strictness is validated by deterministic parser and validator
tests. The published `reports/codex-live-benchmark-summary.json` reflects the
previous collected strict live run until maintainers explicitly publish a new
live run; do not treat parser/schema improvements as new live pass-rate evidence.
When live summaries include process compliance data, explicit PDD, DDD, SDD,
and TDD trace rates are reported separately from inferred/fallback rates.
Inferred-only process traces are warnings and must not be described as fully
explicit process compliance.

Codex live summaries aggregate per-variant pass rates, security pass rates,
failure categories, mean/median/min/max usage and metric counts, ablation
deltas, and per-case/per-variant pass rates. Pass-rate confidence text remains
descriptive because these are local small-sample runs.

In the current quality-first phase, token usage, command executions, and file
changes are telemetry only. They are reported for later analysis, but they do
not gate the quality result, and the reports must not claim cost reduction or
efficiency improvement.

The `danger-full-access` sandbox also requires
`CHANGEFORGE_ALLOW_DANGER_FULL_ACCESS=1` or `--allow-danger-full-access`.

To verify the user's real installed Codex environment, run a separate
current-home smoke check. Current-home smoke may inherit user-level skills,
hooks, config, rules, auth, and trust state. It is not a baseline comparison and
is published only to `reports/codex-current-home-smoke-summary.*`:

```bash
CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK=1 \
CHANGEFORGE_ALLOW_CURRENT_CODEX_HOME=1 \
python3 scripts/run-codex-live-benchmarks.py \
  --benchmark security/ssrf-url-allowlist \
  --benchmark-mode current-home-smoke \
  --auth-policy current-home-full \
  --runs 1 \
  --sandbox workspace-write \
  --out reports/codex-live-runs/current-home-smoke-$(date +%Y%m%d-%H%M%S) \
  --publish-current-home-smoke \
```

Only strict summaries with `auth-policy=borrow-current` or `isolated-api-key`
can be published as comparative evidence. The published strict summary is
blocked when user skills/config/rules are visible, `--ignore-user-config` or
`--ignore-rules` is absent, baseline artifacts contain ChangeForge/user-level
contamination, current-home-full results are present, a variant has no
assertion-backed eligible result, or an ablation summary omits any of
`skills_only_clean_vs_baseline_clean`,
`skills_with_hooks_clean_vs_skills_only_clean`, or
`skills_with_hooks_clean_vs_baseline_clean`:

```bash
python3 scripts/generate-codex-live-summary.py --run-dir reports/codex-live-runs/<run-id> --publish
python3 scripts/validate-codex-live-benchmark-reports.py --summary reports/codex-live-benchmark-summary.json
```

## Recommended Evidence Refresh

Before publishing a scorecard, run **Release Gate** from
[VALIDATION.md](VALIDATION.md), then regenerate the scorecard, dashboard, README
summary block, and public benchmark summary through their generator scripts.
`docs/VALIDATION.md` is the canonical command source; this page describes the
evidence model and publication boundaries rather than duplicating the full
suite.

Longer comparisons such as `python3 scripts/eval-routing.py --candidate-output-dir evals/routing-outputs` should be run when maintaining captured router outputs, not as a default PR blocker.

## Report Policy

`reports/` contains release snapshots that document local evidence. Regenerate them before release decisions and include the generation command in handoff notes. Do not edit scorecard or public benchmark numbers by hand.

Ordinary CI freshness checks are limited to stable generated documentation whose inputs are refreshed during the productization smoke step:

- `docs/SHOWCASE.md`
- `docs/MARKETPLACE_CATALOG.md`

Release snapshot artifacts are committed for reader context but are not guaranteed to be refreshed on every pull request:

- `reports/public-benchmark-summary.md`
- `reports/public-benchmark-summary.json`
- `reports/context-control-plane-eval.md`
- `reports/context-control-plane-eval.json`
- `reports/professional-scorecard.md`
- `reports/professional-scorecard.json`
- `docs/SCORECARD_DASHBOARD.md`
- the README scorecard summary block generated from `reports/professional-scorecard.json`
- `reports/executor-adapter-eval.md`
- `reports/executor-adapter-eval.json`
- `reports/activation-precision.md`
- `reports/activation-precision.json`
- `reports/runtime-telemetry-sample.json`
- `reports/codex-live-benchmark-summary.md`
- `reports/codex-live-benchmark-summary.json`
- `reports/codex-current-home-smoke-summary.md`
- `reports/codex-current-home-smoke-summary.json`

When updating release snapshots, refresh context-control, executor adapter, and activation precision evidence, rebuild all three profiles, refresh the scorecard, render the dashboard and README block, then regenerate the public benchmark summary. The public benchmark summary reuses scorecard dimensions for marketplace, context-control overhead, activation precision, and executor adapter status so those artifacts do not disagree about generated evidence.

See [SCORECARD.md](SCORECARD.md) and [SCORECARD_DASHBOARD.md](SCORECARD_DASHBOARD.md) for the reader-facing scorecard interpretation.
