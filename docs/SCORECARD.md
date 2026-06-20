# Scorecard

The professional scorecard is a conservative health view of ChangeForge. It should help users understand what is verified, what is partial, and what still requires maintainer action.

Generate it with:

```bash
python3 scripts/generate-professional-scorecard.py --out reports/professional-scorecard.md --json-out reports/professional-scorecard.json
```

Render the dashboard and generated README summary with:

```bash
python3 scripts/render-scorecard-dashboard.py --scorecard reports/professional-scorecard.json --out docs/SCORECARD_DASHBOARD.md --readme README.md
```

`reports/professional-scorecard.*`, `docs/SCORECARD_DASHBOARD.md`, and
the README scorecard summary block are release snapshots. They should be
regenerated together before release decisions, but ordinary CI does not treat
them as per-PR freshness gates.

CI smoke checks use the stricter profile-build mode after all profiles are built:

```bash
python3 scripts/generate-professional-scorecard.py --strict-profile-builds --out /tmp/professional-scorecard.md --json-out /tmp/professional-scorecard.json
```

## Dimensions

| Dimension | Status Source | Verification Command | Repair Path |
| --- | --- | --- | --- |
| Routing coverage | `reports/professionalism-release-readiness.json` routing summary. | `python3 scripts/validate-professional-routing-coverage.py` | Add or repair routing fixtures for uncovered risks. |
| Professional skill coverage | Professional skill coverage summary. | `python3 scripts/eval-skill-professionalism.py` | Improve skill contracts without keyword stuffing. |
| Foundation capability coverage | Coverage matrix summary. | `python3 scripts/eval-skill-professionalism.py --coverage-matrix` | Improve selected capability references and evidence contracts. |
| Reference loading discipline | Build manifests and runtime link validation. | `python3 scripts/validate-runtime-reference-links.py` | Keep references selected and linked; do not top-level all capabilities in recommended/full. |
| Hook safety | Hook validator. | `python3 scripts/validate-hooks.py` | Preserve advisory/fail-open behavior unless a stricter mode is explicitly enabled. |
| Runtime governance validators | Repository intelligence, context pack, Project Memory, Validation Broker, and trajectory validators. | `python3 scripts/index-repository.py --target . --out /tmp/changeforge-repo-graph.json && python3 scripts/validate-repository-graph.py --graph /tmp/changeforge-repo-graph.json && python3 scripts/build-context-pack.py --task "release validation" --target . --graph /tmp/changeforge-repo-graph.json --out /tmp/changeforge-context-pack.json && python3 scripts/validate-context-pack.py --context-pack /tmp/changeforge-context-pack.json && python3 scripts/validate-project-memory.py && python3 scripts/validate-validation-broker.py && python3 scripts/validate-trajectory.py` | Rebuild graph/context-pack artifacts, repair privacy or validation parser regressions, and rerun the affected unit suites. |
| Validation suite coverage | Validation command list in scorecard JSON. | Full suite in [RELEASE.md](RELEASE.md) | Run missing commands and include results in release handoff. |
| Installation reproducibility | Build manifests and installer validation. | `python3 scripts/validate-installation.py` | Rebuild profiles, repair manifest/install mismatches, rerun doctor. |
| Marketplace index validation | Source-derived marketplace exporter and profile validator. | `python3 scripts/validate-marketplace-index.py --profile recommended && python3 scripts/validate-marketplace-index.py --profile full && python3 scripts/validate-marketplace-index.py --profile dev` | Rebuild profiles and repair schema, visibility, or runtime path mismatches. |
| Runtime governance structural fixtures | Local structural fixtures for executor adapters, repository intelligence, project memory, validation broker, and trajectory. | `python3 scripts/validate-professional-routing-coverage.py` | Add or repair fixture YAML under `evals/executor-adapters`, `evals/repository-intelligence`, `evals/project-memory`, `evals/validation-broker`, and `evals/trajectory`; do not treat structural fixtures as live empirical pass-rate evidence. |
| Executor adapter structural fixtures | Deterministic fixture report for runtime adapter normalization, degradation, privacy, validation freshness, and closure behavior. | `python3 scripts/eval-executor-adapters.py` | Repair fixture expectations or adapter normalization until deterministic cases pass; do not treat structural fixtures as live runtime pass-rate evidence. |
| Activation precision benchmark | Deterministic route activation precision/recall report for stage, skill, capability, reference, language, risk, and overroute metrics against the built hook runtime. | `python3 scripts/eval-activation-precision.py --mode built --runtime-root dist/codex/project/.codex/hooks` | Repair fixture expectations or built resolver precision until all activation metrics pass. |
| Runtime telemetry fixture sample | Sanitized bounded sample generated from executor adapter fixture facts. | `python3 scripts/eval-executor-adapters.py` | Regenerate the sample and keep it clearly labeled as fixture-derived evidence. |
| Live runtime telemetry sample | Sanitized bounded facts from an actual hook runtime execution, when available. | Manual live runtime collection. | Keep `not_collected` until a real hook-runtime sample exists; do not use executor adapter fixtures for this dimension. |
| Executor adapter live pass-rate | Measured real-task executor adapter success rate, when available. | `python3 scripts/eval-executor-adapters.py` | Keep `not_collected` until a real measured run exists. |
| Executor adapter token overhead | Measured additional token cost, when available. | `python3 scripts/eval-executor-adapters.py` | Keep `not_collected` until a real measured run exists. |
| Executor adapter turn overhead | Measured additional turn cost, when available. | `python3 scripts/eval-executor-adapters.py` | Keep `not_collected` until a real measured run exists. |
| Codex CLI live benchmark | Published `reports/codex-live-benchmark-summary.json` from an explicit opt-in local Codex CLI run. | `python3 scripts/validate-codex-live-benchmark-reports.py --summary reports/codex-live-benchmark-summary.json` | Keep `not_collected` until a real validated live run is published; dry-run and skipped reports cannot satisfy this dimension. |
| Open-source readiness | `config/open-source-release.yaml`, [LICENSE_DECISION.md](LICENSE_DECISION.md), [OPEN_SOURCE_READINESS.md](OPEN_SOURCE_READINESS.md), `pyproject.toml`, `CONTRIBUTING.md`, `SECURITY.md`, and root `LICENSE`. | `python3 scripts/validate-open-source-readiness.py` | Owner chooses license, adds exact license text, updates package metadata, confirms contribution licensing, and confirms private vulnerability reporting or private security contact before open-source publication. |
| Example coverage | `examples/` scenario structure. | `python3 scripts/validate-examples.py` | Add prompt, route, and evidence files for each scenario. |
| Productization assets | Productization docs, schema, and generation/validation scripts. | `python3 scripts/validate-productization-assets.py` | Restore required productization assets. |

## Status Rules

- `pass`: machine-readable evidence exists and the check passed.
- `partial`: evidence exists but has warnings, needs-review items, or owner decisions.
- `fail`: evidence shows a broken invariant.
- `unknown`: the expected evidence artifact is absent or incomplete.
- `not_collected`: the command is known, but no machine-readable result is available for the scorecard to consume.

Do not replace `unknown` or `not_collected` with `pass` by hand. Run the verification command and update the scorecard generator only when the underlying tool emits reliable machine-readable evidence.

## Evidence Levels

| Evidence | Meaning |
| --- | --- |
| structural fixture | Local deterministic structure sample passed; this is not live task success evidence. |
| runtime telemetry fixture sample | Deterministic executor-adapter fixture-derived bounded facts; this is not live runtime telemetry. |
| live runtime telemetry sample | Sanitized bounded facts from an actual hook runtime execution; it may still require human review before promotion. |
| promoted golden case | Human-reviewed case admitted to regression coverage. |
| live pass-rate | Measured real-task success rate. |
| token overhead | Measured additional token cost. |
| turn overhead | Measured additional turn cost. |
| local_codex_cli_live_benchmark | Explicit opt-in local Codex CLI benchmark run with sanitized bounded artifacts. |

Generated telemetry candidates with `generated_from_telemetry: true` and
`requires_human_review: true` are candidate evidence only. They must not count as
measured evidence, promoted golden cases, live pass-rate, token overhead, or turn
overhead until a maintainer reviews and promotes them.

Executor adapter fixture telemetry can make `runtime telemetry fixture sample`
pass when the generated sample is bounded, sanitized, and explicitly labeled as
fixture-derived. It does not make `live runtime telemetry sample`,
`live pass-rate`, `token overhead`, or `turn overhead` pass; those dimensions
remain `not_collected` until separately measured or collected.

Codex CLI live benchmark evidence is separate from executor adapter telemetry.
The scorecard and public summary only read `reports/codex-live-benchmark-summary.json`;
they never run Codex. A summary must come from a real opt-in run and pass
`validate-codex-live-benchmark-reports.py --summary` before it can change the
dimension from `not_collected`.

Open-source readiness is conservative: a root `LICENSE` alone is not enough. Proprietary `pyproject.toml` license metadata fails the dimension once a license file exists. `config/open-source-release.yaml:selected_license` must be non-null, contribution licensing must be owner-confirmed, and GitHub private vulnerability reporting or a private security contact must be owner-confirmed before the dimension can be `pass`.

## README Summary

The README should stay short. Link here for details instead of copying the full table into the front page.

See [SCORECARD_DASHBOARD.md](SCORECARD_DASHBOARD.md) for the generated dashboard and [BENCHMARKS.md](BENCHMARKS.md) for the benchmark system behind the scorecard.
