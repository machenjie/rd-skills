# Codex CLI Live Benchmarks

This suite runs selected ChangeForge code-generation benchmarks through the
local Codex CLI. It is intentionally opt-in because it may use credentials,
network access, local model quota, and writable work directories.

Default commands are dry-run or report validation only. They must not invoke
`codex exec` unless one of these explicit gates is present:

- `CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK=1`
- `--allow-live-codex`

`--dry-run` has priority over every live opt-in and never runs Codex. The
`danger-full-access` sandbox has an additional gate:

- `CHANGEFORGE_ALLOW_DANGER_FULL_ACCESS=1`
- `--allow-danger-full-access`

Strict live runs default to `--auth-policy borrow-current`: they borrow the
caller’s saved Codex authentication while using temp `HOME`, hiding user-level
skills, and passing `--ignore-user-config` plus `--ignore-rules`. For fully
isolated runs, use `--auth-policy isolated-api-key` with `CODEX_API_KEY` set for
the subprocess only. To inherit the full current Codex home for smoke testing,
use `--auth-policy current-home-full` and also provide one of these explicit
gates:

- `CHANGEFORGE_ALLOW_CURRENT_CODEX_HOME=1`
- `--allow-current-codex-home`

Current-home-full mode may inherit user-level skills, hooks, config, rules,
auth, and trust state. It is smoke evidence only and cannot publish strict A/B
claims.

## Quick Checks

```bash
python3 scripts/run-codex-live-benchmarks.py --list
python3 scripts/run-codex-live-benchmarks.py \
  --benchmark-mode ablation \
  --auth-policy borrow-current \
  --benchmark security/ssrf-url-allowlist \
  --dry-run \
  --out /tmp/changeforge-codex-live-ablation-dry-run
python3 scripts/validate-codex-live-benchmark-reports.py \
  --run-dir /tmp/changeforge-codex-live-ablation-dry-run
python3 scripts/validate-report-consistency.py
```

## Clean Auth-Borrowed Strict A/B

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

This mode runs `baseline_clean` and `skills_with_hooks_clean` with temp `HOME`.
It may use the current Codex auth source, but it does not load user-level
skills/hooks/config/rules. Publishing is blocked if baseline contamination is
detected or if assertion-backed eligible results are missing.

## Isolated API-Key Strict A/B

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

This mode keeps both `HOME` and `CODEX_HOME` temporary and records only redacted
API-key metadata.

## Clean Ablation Example

```bash
CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK=1 \
python3 scripts/run-codex-live-benchmarks.py \
  --benchmark-mode ablation \
  --auth-policy borrow-current \
  --runs 3 \
  --profile recommended \
  --sandbox workspace-write \
  --out reports/codex-live-runs/ablation-auth-borrowed-$(date +%Y%m%d-%H%M%S) \
  --publish-summary
```

This mode runs `baseline_clean`, `skills_only_clean`, and
`skills_with_hooks_clean` with the same clean auth-borrowing policy. Without a
`--benchmark` or `--tier` filter it runs all enabled cases. Use `--tier core`
for the strongest current core set, or `--tier level1` for the broader
assertion-backed coverage expansion. The registry records each case's tier and
coverage dimensions, and generated summaries include coverage, cost, and
stability sections.
Repeated-run evidence should use at least 3 runs per variant. Single-case
ablation runs are useful pipeline smoke evidence, not broad pass-rate claims.

## Long-Running Run Strategy

Use the smallest evidence mode that answers the current release question:

- PR quick mode: deterministic checks plus a core one-run diagnostic.
- Merge final: `--tier core --runs 3` with all strict variants.
- Weekly/manual: `--tier level1` diagnostic first, then final if setup and
  execution failures are clean.
- Release: extended/full suites only after core and Level 1 evidence are stable.

Selection and recovery flags:

- `--tier core|level1|experimental` selects registered case tiers.
- `--changed-only` selects cases whose task, starter, grading, or cases registry
  paths changed.
- `--failed-only <run-id-or-dir>` and `--rerun-failures-from <run-id-or-dir>`
  select failed case/variant/run cells from a previous run and mark the run as
  diagnostic selection metadata.
- `--max-cases N` limits selected cases for diagnostics.
- `--max-runtime-minutes N` stops launching new cells after the budget.
- `--case-shard INDEX/TOTAL` partitions sorted case ids deterministically;
  variants remain balanced within each selected case.
- `--resume-run <run-dir>` reuses a run directory and skips cells that already
  have `result.json`.
- `--parallel-cases N` is recorded for governance, but this runner executes
  serially in-process; use shards for external parallel execution.

Final strict runs do not reuse baselines. Diagnostic runs may record
`baseline_reuse_policy`, but the default and current final policy is `none`.

## Level 1 Diagnostic

Level 1 cases are assertion-backed coverage expansion and must not dilute core
pass claims. Run Level 1 separately after the core summary is pass/positive:

```bash
CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK=1 \
python3 scripts/run-codex-live-benchmarks.py \
  --benchmark-mode ablation \
  --auth-policy borrow-current \
  --tier level1 \
  --runs 1 \
  --profile recommended \
  --sandbox workspace-write \
  --out reports/codex-live-runs/ablation-level1-diagnostic-$(date +%Y%m%d-%H%M%S) \
  --publish-summary
```

Only claim Level 1 coverage after actual Level 1 results exist in the summary;
coverage summaries distinguish registered cases from actual run cases.

## Structured Logs and Process Traces

Live and dry-run directories include sanitized run-level logs:

- `run.log.jsonl`
- `timeline.jsonl`

Live result cells include `process-trace.json` with compact PDD, DDD, SDD, TDD,
implementation, validation, and review status. Validate these artifacts with:

```bash
python3 scripts/validate-codex-live-logs.py --run-dir <run-dir>
python3 scripts/validate-process-traces.py --run-dir <run-dir>
```

## Current-Home Smoke Example

Run current-home smoke only to verify the real installed local Codex
environment. This can inherit user-level skills, hooks, config, rules, auth, and
trust state. It is not a baseline comparison and cannot publish the strict
benchmark summary:

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

Run output is stored under the selected run directory. Published strict
summaries are blocked when baseline artifacts contain ChangeForge/user-level
contamination, when current-home-full results are present, when user
skills/config/rules are visible, or when pass rates are not backed by real
assertion checks. Dry-run, skipped, telemetry-only, and current-home smoke
reports cannot satisfy strict scorecard/public benchmark claims.

Strict published summaries include failure-category buckets, ablation deltas,
mean/median/min/max usage and metric counts, and per-case/per-variant pass
rates. Ablation summaries must include all three comparisons:
`skills_only_clean_vs_baseline_clean`,
`skills_with_hooks_clean_vs_skills_only_clean`, and
`skills_with_hooks_clean_vs_baseline_clean`.

Artifacts deliberately store bounded metadata:

- redacted Codex command shape, not raw environment values;
- parsed event counts and token usage, not raw command bodies or assistant
  messages;
- candidate diffs, git status, final answer, and grading logs for the isolated
  starter repository;
- limitations explaining what was and was not measured.

Published summaries are committed; detailed per-run artifacts remain local-only
for privacy. Use sanitized artifact export manually when needed. Committed
repository reports publish only sanitized summary artifacts such as
`reports/codex-live-benchmark-summary.json`, professional scorecards, and public
benchmark summaries. Per-run directories under `reports/codex-live-runs/` remain
local-only by default because they can contain candidate diffs, redacted command
metadata, grading logs, and final messages that are useful for diagnosis but not
suitable as broad public artifacts without a separate sanitization review.

Do not add cases that require external private paths, network-only resources,
personal archives, or user-specific corpora.
