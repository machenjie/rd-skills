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
  --benchmark-mode clean-paired \
  --auth-policy borrow-current \
  --benchmark security/ssrf-url-allowlist \
  --dry-run \
  --out /tmp/changeforge-codex-live-borrow-auth-dry-run
python3 scripts/validate-codex-live-benchmark-reports.py \
  --run-dir /tmp/changeforge-codex-live-borrow-auth-dry-run
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
  --benchmark security/ssrf-url-allowlist \
  --benchmark-mode ablation \
  --auth-policy borrow-current \
  --runs 1 \
  --profile recommended \
  --sandbox workspace-write \
  --out reports/codex-live-runs/ablation-auth-borrowed-$(date +%Y%m%d-%H%M%S) \
  --publish-summary
```

This mode runs `baseline_clean`, `skills_only_clean`, and
`skills_with_hooks_clean` with the same clean auth-borrowing policy.

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

Artifacts deliberately store bounded metadata:

- redacted Codex command shape, not raw environment values;
- parsed event counts and token usage, not raw command bodies or assistant
  messages;
- candidate diffs, git status, final answer, and grading logs for the isolated
  starter repository;
- limitations explaining what was and was not measured.

Do not add cases that require external private paths, network-only resources,
personal archives, or user-specific corpora.
