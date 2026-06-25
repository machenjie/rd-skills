# Core99 Ablation 发布报告

- 生成日期: 2026-06-25
- 发布对象: ChangeForge / rd-skills core capability ablation evidence
- 权威运行目录: `reports/codex-live-runs/core99-ablation-rootfix-20260625-031010`
- 发布结论: 有条件可发布。99-result run-specific 证据已通过；公开 scorecard / public summary 仍引用旧顶层摘要，外部发布前必须再生成或明确标注为未同步。

## 1. 范围

本报告只覆盖 `core99-ablation-rootfix-20260625-031010` 这次 Codex CLI live benchmark ablation 结果，以及与该结果相关的发布判断。

本报告不表示已经执行生产部署、安装发布、marketplace 发布、包发布、Git push、用户 HOME/CODEX_HOME 写入、云资源变更或外部系统写入。

## 2. 证据来源

| 证据 | 路径 | 用途 |
| --- | --- | --- |
| 99-run 摘要 | `reports/codex-live-runs/core99-ablation-rootfix-20260625-031010/summary.json` | 机器可读发布事实源 |
| 99-run Markdown 摘要 | `reports/codex-live-runs/core99-ablation-rootfix-20260625-031010/summary.md` | 人读摘要与 case/capability 展示 |
| 运行清单 | `reports/codex-live-runs/core99-ablation-rootfix-20260625-031010/run-manifest.json` | 运行模式、variant、case 列表 |
| 运行日志 | `reports/codex-live-runs/core99-ablation-rootfix-20260625-031010/run.log.jsonl` | 结构化运行事件 |
| 时间线 | `reports/codex-live-runs/core99-ablation-rootfix-20260625-031010/timeline.jsonl` | 事件时间线 |
| 职业化发布就绪 | `reports/professionalism-release-readiness.md` | 非 live-run 的发布就绪证据 |
| 旧顶层 live 摘要 | `reports/codex-live-benchmark-summary.json` | 对比 stale publication 风险 |

## 3. 核心结果

| 指标 | 结果 |
| --- | --- |
| Run id | `core99-ablation-rootfix-20260625-031010` |
| Benchmark mode | `ablation` |
| Auth policy | `borrow-current` |
| Variants | `baseline_clean`, `skills_only_clean`, `skills_with_hooks_clean` |
| Core cases | 11 |
| Result count | 99 |
| Benchmark eligible results | 99 |
| Benchmark passed results | 99 |
| Contaminated results | 0 |
| Evidence status | `pass` |
| Effect status | `neutral` |
| Dominant failure category | `none` |
| Process trace count | 99 |

所有 11 个 assertion-backed core cases 在三个 variants 中均为 3/3 通过：

1. `compact/context-retention-after-compaction`
2. `devex/minimal-correct-native-reuse`
3. `injection/professional-route-manifest-activation`
4. `injection/stage-specific-reference-loading`
5. `logging/redacted-structured-log-design`
6. `memory/repeated-failure-fragile-file`
7. `pressure/professional-boundary-under-user-pressure`
8. `process/full-pdd-ddd-sdd-tdd-review-repair`
9. `repo-intel/caller-callee-test-impact-map`
10. `review/repair-rereview-required`
11. `validation/stale-validation-after-edit`

## 4. 真实质量判断

这次结果不能被解读为 pass-rate 层面的技能提升，因为 baseline 已经达到 1.0 pass rate。正确发布口径是：

- `baseline_clean` pass rate: 1.0
- `skills_only_clean` pass rate: 1.0
- `skills_with_hooks_clean` pass rate: 1.0
- `skills_only_vs_baseline_delta`: 0.0
- `skills_with_hooks_vs_baseline_delta`: 0.0
- `effect_status`: `neutral`

但 capability/process evidence 层面显示技能质量改善：

- `capability_quality_ready`: true
- `assertion_backed_core_capability_count`: 11
- `skill_quality_improved`: true
- `skill_capability_evidence_improved`: true
- `skill_pass_rate_improved`: false
- `no_quality_regression`: true
- `skills_only_route_process_evidence_rate`: 1.0
- `skills_with_hooks_route_process_evidence_rate`: 1.0
- `skills_with_hooks_hook_bounded_evidence_rate`: 1.0
- `skills_only_strict_process_trace_rate`: 1.0
- `skills_with_hooks_strict_process_trace_rate`: 1.0

发布判断：rd-skills 的真实核心能力质量可以认定为 assertion-backed core capability evidence 已达发布阈值；但不能宣传为 pass-rate 提升或效率提升。

## 5. 根因结论

本次 99-run 说明，先前“基本没有通过”的直接发布风险不是当前 core cases 本身继续失败，而是 evidence aggregation / publication path 不一致：

- 新 run-specific `summary.json` 记录 `benchmark_passed_result_count=99`、`benchmark_eligible_result_count=99`、`capability_quality_ready=true`。
- 旧顶层 `reports/codex-live-benchmark-summary.json` 仍记录 `benchmark_passed_result_count=9`、`capability_quality_ready=false`、`assertion_backed_core_capability_count=0`，并列出 capability coverage missing 项。
- `README.md` 和 `reports/professional-scorecard.md` 仍从旧顶层摘要展示 `Codex CLI live capability coverage` 为 `fail`。

因此，发布前必须把 run-specific 99-run evidence 与顶层 public summary / scorecard / README evidence 同步，或者在发布材料中明确旧顶层摘要不是本次发布依据。

## 6. 发布就绪状态

| Gate | 状态 | 证据 |
| --- | --- | --- |
| Core 99-run collection | Pass | 99/99 eligible results passed |
| Capability quality readiness | Pass | 11 assertion-backed core capabilities ready |
| Strict process trace evidence | Pass | 99 process traces; strict process rates 1.0 for skills variants |
| Contamination check | Pass | contaminated results = 0 |
| Professionalism release readiness | Pass | `reports/professionalism-release-readiness.md` status `strict-release-ready` |
| Public summary synchronization | Blocking before external publication | top-level public/scorecard evidence still references stale live summary |
| Efficiency claim | Not allowed | token/command overhead is telemetry only; no efficiency improvement claim |

Release decision:

- Internal release review: ready with noted publication caveat.
- External/public evidence publication: blocked until top-level summaries are regenerated or release notes explicitly link only to the run-specific report.

## 7. 成本与效率口径

Cost telemetry is not a quality gate in this benchmark. The report must not claim cost reduction or efficiency improvement.

Observed telemetry:

- `skills_with_hooks_clean` vs baseline input token overhead: +234.06%
- output token overhead: +45.63%
- reasoning token overhead: +49.96%
- average command execution delta: +22.61
- pass-rate delta: 0.0

Interpretation: skills/hooks improve evidence completeness and traceability in this run, but they are heavier. Any release communication must present this as a quality-first result with explicit cost caveat.

## 8. 发布说明草案

### Added

- Added a run-specific release evidence package for `core99-ablation-rootfix-20260625-031010`.
- Added assertion-backed coverage for 11 core capabilities across 99 eligible ablation results.

### Changed

- Core capability quality should now be judged from strict process/capability evidence, not pass-rate deltas alone, because baseline pass rate is saturated.
- Release communication should treat cost metrics as telemetry only.

### Fixed

- Clarified that the old “almost nothing passed” interpretation is stale for the new 99-run result and should not be used as the current core capability judgment.

### Known Publication Gap

- `reports/codex-live-benchmark-summary.json`, `reports/public-benchmark-summary.md`, `reports/professional-scorecard.md`, and README scorecard snippets still reflect the older live benchmark summary. Regenerate these before external publication.

## 9. 回滚与前进修复

Report-only rollback:

- Delete or revert `reports/core99-ablation-release-report-20260625.md`.
- No runtime skill content, registry, dist artifact, installation, deployment, or external system state is changed by this report.

Publication rollback:

- If the top-level public summary cannot be regenerated cleanly, keep the older public summary as-is and do not publish a global scorecard update.
- Publish only the run-specific report path as limited evidence, with the stale-summary caveat retained.

Forward fix before external release:

1. Regenerate top-level live benchmark summary from the accepted run-specific evidence.
2. Regenerate public benchmark summary and professional scorecard.
3. Refresh README scorecard snippet if those generated artifacts are accepted for publication.
4. Re-run live benchmark report validation and process trace validation after any regeneration.

## 10. Security / Privacy Boundary

This report uses aggregate metrics and repository-relative paths only. It does not include raw prompts, raw command output, credentials, environment values, API keys, user-specific content corpus references, HOME/CODEX_HOME state, or external account identifiers.

Tool boundary for this report generation:

- Shell commands used for inspection are read-only.
- The only planned state mutation is adding this Markdown file under `reports/`.
- No deploy, publish, install, push, migration, cloud, connector, or network write is part of this report.

## 11. Required Validation Before Handoff

Run after generating this report:

```bash
python3 scripts/validate-codex-live-benchmark-reports.py --run-dir reports/codex-live-runs/core99-ablation-rootfix-20260625-031010
python3 scripts/validate-process-traces.py --run-dir reports/codex-live-runs/core99-ablation-rootfix-20260625-031010 --require-present
test -f reports/core99-ablation-release-report-20260625.md
rg -n "sk-[A-Za-z0-9_-]{10,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|PRIVATE) KEY" reports/core99-ablation-release-report-20260625.md
```

Expected result: the first three commands pass; the `rg` command returns no matches.

## 12. Residual Risk

- Top-level public evidence is stale relative to this run-specific report until regenerated.
- This report validates local benchmark evidence, not real-world adoption, marketplace availability, production deployment behavior, or user productivity.
- Run metadata has null timestamps in `run-manifest.json`; publish the run id and file paths as provenance rather than implying an exact wall-clock run window from the manifest.
- Cost telemetry comes from local Codex telemetry and is not a billing ledger.
