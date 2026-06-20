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

By default, each live run gets an isolated `HOME` and `CODEX_HOME` under the
selected output directory. To reuse the caller's existing local Codex login,
provider configuration, and trust state, set `--codex-home-mode current` and
also provide one of these explicit gates:

- `CHANGEFORGE_ALLOW_CURRENT_CODEX_HOME=1`
- `--allow-current-codex-home`

Current Codex home mode may inherit user-level hooks and config, including
global ChangeForge hooks. Use a controlled Codex home before publishing
comparative baseline/changeforge claims.

## Quick Checks

```bash
python3 scripts/run-codex-live-benchmarks.py --list
python3 scripts/run-codex-live-benchmarks.py \
  --benchmark devex/helper-reuse-search \
  --dry-run \
  --out /tmp/changeforge-codex-live-dry-run
python3 scripts/validate-codex-live-benchmark-reports.py \
  --run-dir /tmp/changeforge-codex-live-dry-run
```

## Live Smoke Example

```bash
CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK=1 \
python3 scripts/run-codex-live-benchmarks.py \
  --benchmark security/ssrf-url-allowlist \
  --variant baseline \
  --variant changeforge \
  --runs 1 \
  --profile recommended \
  --sandbox workspace-write \
  --out reports/codex-live-runs/local-$(date +%Y%m%d-%H%M%S)
```

Run output is stored under the selected run directory. Published summaries are
only produced from real live runs and are validated before scorecard ingestion.
Dry-run or skipped reports cannot be published.

If local Codex auth is stored in your current `~/.codex` login/config, run the
same smoke with current Codex home mode:

```bash
CHANGEFORGE_ENABLE_CODEX_LIVE_BENCHMARK=1 \
CHANGEFORGE_ALLOW_CURRENT_CODEX_HOME=1 \
python3 scripts/run-codex-live-benchmarks.py \
  --benchmark security/ssrf-url-allowlist \
  --variant baseline \
  --runs 1 \
  --profile recommended \
  --sandbox workspace-write \
  --codex-home-mode current \
  --out reports/codex-live-runs/local-$(date +%Y%m%d-%H%M%S)
```

Artifacts deliberately store bounded metadata:

- redacted Codex command shape, not raw environment values;
- parsed event counts and token usage, not raw command bodies or assistant
  messages;
- candidate diffs, git status, final answer, and grading logs for the isolated
  starter repository;
- limitations explaining what was and was not measured.

Do not add cases that require external private paths, network-only resources,
personal archives, or user-specific corpora.
