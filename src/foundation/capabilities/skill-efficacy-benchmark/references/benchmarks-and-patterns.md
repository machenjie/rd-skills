# Skill Efficacy Benchmark Benchmarks And Patterns

Use this reference when `skill-efficacy-benchmark` needs deeper metric definitions, baseline/treatment comparison patterns, structural-vs-empirical classification, over/under-routing guards, context overhead, privacy-safe fixture rules, or anti-pattern review beyond the inline `SKILL.md` body.

## Contents

- Benchmark Anchors
- Case Shape Matrix
- Baseline Treatment Comparison
- Metric Definitions
- Routing And Reference Budget Guards
- Structural Versus Empirical Verdicts
- Privacy-Safe Fixture Boundaries
- Anti-Patterns To Reject
- Handoff Boundaries

## Benchmark Anchors

| Benchmark | Efficacy implication | Evidence to require |
| --- | --- | --- |
| A/B experiment discipline | Treatment claims need a comparable baseline and the same task boundary. | Baseline artifact, treatment artifact, metric set, verdict, and caveat. |
| Evaluation-driven development | Behavior changes should ship with fixtures or validators that fail for the old behavior. | Negative baseline, repaired output, regression command, and failure mode. |
| Human review quality | Better professional behavior means catching specific defects, missing evidence, or unsafe closure. | Defect class, reviewer expectation, caught/missed result, and residual risk. |
| Cost-aware AI evaluation | Improvement must not silently increase context, tokens, or turns beyond the benefit. | Selected/skipped reference counts, token/turn overhead, and over-budget rationale. |
| Reproducible research | Reports must separate observed repository evidence from unsupported population claims. | Case source, command, generated report, sample size, and evidence limits. |
| Privacy-by-design | Fixtures must not collect raw prompts, secrets, environment values, personal archives, or broad source corpora. | Redaction rule, bounded facts retained, rejected data, and rollback path. |

## Case Shape Matrix

| Case type | Strong case | Weak case to reject |
| --- | --- | --- |
| Skill body improvement | Same task, old body or report, new body, expected professional behavior delta, validator. | "Score improved" with no behavior that would fail before. |
| Reference loading improvement | Selected and skipped references, budget mode, JIT rationale, over/under-routing guards. | Adding references without proving they stay unloaded until needed. |
| Routing rule improvement | Prompt fixture, expected route, skipped route rationale, hidden-risk trigger, regression command. | Keyword match that does not validate owner/reviewer/gate selection. |
| Evidence closure improvement | Baseline closure misses proof, treatment blocks or caveats it, validation after final edit. | Report says "evidence stronger" without a weak-evidence case. |
| Hook/runtime support | Runtime signal, bounded injected facts, privacy boundary, state location, build/install validator. | Hook prompt stores raw prompts, full output, or project source slices. |
| Agent behavior fixture | Pressure scenario, forbidden behavior, expected repair, strict validator. | Fixture passes by section existence or generic phrase count. |

## Baseline Treatment Comparison

```yaml
skill_efficacy_case:
  case_id: ""
  behavior_claim: ""
  task_boundary: ""
  baseline:
    artifact: ""
    observed_behavior: ""
    defect_or_gap: ""
    validation: ""
    token_overhead: not_collected
    turn_overhead: not_collected
  treatment:
    artifact: ""
    observed_behavior: ""
    defect_or_gap: ""
    validation: ""
    token_overhead: not_collected
    turn_overhead: not_collected
  verdict: improved|regressed|no_change|unknown|not_enough_evidence
  caveats:
    - ""
```

Baseline and treatment must use the same task, route risk, and evidence boundary. If the old artifact is unavailable, state that the comparison is structural-only and avoid empirical improvement language.

## Metric Definitions

| Metric | Strong measurement | Evidence limit |
| --- | --- | --- |
| Routing correctness | Expected owner, reviewer, capabilities, skipped routes, and quality gates match the fixture. | Does not prove live prompt distribution behavior. |
| Evidence completeness | Required proof fields, validation freshness, proof limits, and residual risk are present and concrete. | Does not prove the underlying product behavior unless validators run. |
| Defect catch rate | Fixture names the defect and confirms old behavior fails or is marked weak. | Small fixtures do not estimate population catch rate. |
| Validation freshness | Command runs after final material edit and maps to changed paths. | Does not cover unrun validators or external CI. |
| Over-routing | Trivial or out-of-scope cases do not load heavy skills/references. | Does not prove all unrelated prompts stay lean. |
| Under-routing | Hidden-risk case selects required gate/capability. | Does not prove every risk synonym is covered. |
| Token overhead | Token estimate or `not_collected` plus selected/skipped reference counts. | Proxy estimates are not live model usage. |
| Turn overhead | Turn count or `not_collected` plus route/repair loop count. | Does not prove user-perceived latency. |

## Routing And Reference Budget Guards

| Guard | Required check |
| --- | --- |
| Selected reference guard | Each loaded reference has a task-specific reason tied to route risk. |
| Skipped reference guard | Nearby references and domain extensions are skipped with a reason. |
| Over-routing guard | A trivial docs/formatting case avoids heavy gates and domain extensions. |
| Under-routing guard | A hidden-risk case selects the correct specialist gate. |
| Context budget guard | Budget mode, selected count, skipped count, JIT plan, and overhead caveat are recorded. |
| Runtime profile guard | Source-only, recommended/full compiled reference, and dev profile behavior are not confused. |

## Structural Versus Empirical Verdicts

Use `structural-only` when the evidence is a validator, report, route fixture, static diff, or generated artifact check. Use empirical wording only when representative agent runs, sample size, sampling method, and live-run limitations are available. A structural improvement may justify release of a skill change, but it must not be described as proven real-world productivity, quality, or user outcome improvement.

## Privacy-Safe Fixture Boundaries

Accept fixture inputs that are bounded, synthetic, repository-owned, redacted, and reproducible. Reject or redact:

- raw user prompts outside a maintainer-approved fixture;
- secrets, tokens, environment values, credentials, private URLs, or production identifiers;
- full command output when a bounded summary plus exit code is enough;
- private source archives or personal knowledge corpora;
- connector payloads without a data boundary and retention rule.

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| Score-only success | Numeric movement can hide wrong behavior or context bloat. | Add behavior case, baseline/treatment, and caveat. |
| Benchmark with no negative case | Validator may pass both old and new behavior. | Add a failing/weak baseline or forbidden output. |
| "All references" treatment | Measures context stuffing, not precision. | Use selected/skipped reference allow-list. |
| Raw prompt corpus | Turns benchmark into user-content ingestion. | Use bounded synthetic or approved redacted fixtures. |
| Live efficacy claim from static report | Overgeneralizes structural evidence. | Mark structural-only and state what remains unmeasured. |
| Validation before final edit | Certifies a stale artifact. | Rerun mapped validator after final material edit. |

## Handoff Boundaries

- Use `skill-authoring-expert` when the benchmark reveals trigger, output, reference-loading, or skill-body changes are needed.
- Use `change-forge-router` when the benchmark changes route selection, skipped gates, or manifest requirements.
- Use `quality-test-gate` when benchmark validation becomes release evidence or stale validation blocks closure.
- Use `validation-broker` when changed paths need mapped validators or generated report freshness.
- Use `context-control-plane` when overhead, selected/skipped references, or tool-output boundaries decide the verdict.
- Use `agent-execution-discipline` when completion language, repair/re-review, or residual-risk handoff is the behavior under test.
