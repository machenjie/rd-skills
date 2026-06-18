---
name: skill-efficacy-benchmark
description: Defines baseline-versus-treatment evaluation for ChangeForge skill and capability changes, including routing quality, evidence quality, review defects, token and turn overhead, and caveat discipline.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "121"
changeforge_version: 0.1.0
---

# Skill Efficacy Benchmark

## Mission
Evaluate whether a ChangeForge skill, capability, routing rule, hook prompt, or benchmark change improves professional agent behavior without making unsupported real-world claims. The benchmark compares baseline and treatment behavior against explicit tasks, defect outcomes, routing quality, evidence quality, and token or turn overhead.

## When To Use
- When adding or materially changing skills, foundation capabilities, routing rules, stage signals, hook prompts, or evaluation fixtures.
- When claiming that a skill improves agent quality, evidence, routing, review, validation, or repair behavior.
- When a regression fixture should prove over-routing, under-routing, wrong placement, missing validation, or unsafe tool behavior.
- Before release notes or documentation describe a professional behavior improvement.

## Do Not Use When
- The change is a typo or formatting-only edit with no professional behavior claim.
- The user asks only to author a capability stub without evaluating its effect.
- The available data is structural only and the output would be framed as real-world performance.

## Non-Negotiable Rules
- Do not claim real-world efficacy without representative baseline and treatment evidence.
- Every benchmark case must define a task, baseline, treatment, metrics, verdict, and caveats.
- Track token and turn overhead even when not collected; use `not_collected` rather than omitting the fields.
- Distinguish structural fixture validation from empirical agent performance.
- Record over-routing and under-routing risk, not only success.
- Do not use benchmark fixtures as a general-purpose source corpus.
- Keep benchmark inputs bounded, reproducible, and reviewable in repository source.

## Industry Benchmarks
- **A/B experiment discipline**: Treatment claims require baseline, treatment, metric, and caveat.
- **Evaluation-driven development**: Behavior changes ship with fixtures that can catch regressions.
- **Human code review quality**: Findings, missing tests, and false approval are tracked as review outcomes.
- **Cost-aware AI evaluation**: Quality improvements must be balanced against token and turn overhead.
- **Reproducible research**: Claims separate observed evidence from unsupported generalization.

## Selection Rules
- Select this capability when a skill authoring change introduces or changes expected agent behavior.
- Select it when routing, hook runtime, eval fixtures, or professional benchmark scripts are updated.
- Select it when documentation says a capability improves safety, review quality, evidence, or validation.
- Select it with `quality-test-gate` when benchmark validation becomes part of release evidence.
- Select it with `ai-code-review-refactor` when generated skill content needs spec-first review before quality claims.

## Risk Escalation Rules
- Escalate when a change makes an efficacy claim without baseline/treatment data.
- Escalate when a fixture passes by matching keywords but does not test the professional behavior claimed.
- Escalate when token or turn overhead is omitted.
- Escalate when routing improvements hide over-routing drag or under-routing safety gaps.
- Escalate when benchmark data includes raw prompts, secrets, user-specific source material, or unbounded command output.

## Critical Details
- A benchmark can be useful even when overhead is `not_collected`; the caveat must be explicit.
- A structural fixture validates schema and evaluation plumbing, not live agent productivity.
- The unit of comparison is the same task under baseline and treatment conditions.
- Verdicts should be conservative: `unknown` or `not_enough_evidence` is better than an inflated win.
- Benchmark reports should name what changed, what improved, what did not, and what remains unmeasured.

## Failure Modes
- **Unsupported claim**: A capability is described as improving code quality without comparative evidence.
- **Keyword-only pass**: The eval checks that a capability name appears but not whether the route is correct.
- **Overhead blind spot**: Treatment improves one score but doubles turns or tokens and the cost is not recorded.
- **Fixture contamination**: Test data includes user-specific source material or raw prompts that should not be source content.
- **No negative cases**: A benchmark validates happy paths but misses destructive tool, wrong placement, or extra-file drift.

## Output Contract
Return a `skill_efficacy_benchmark` record with:
- **Case id**: stable identifier.
- **Capability or skill under test**: selected skill, capability, hook, or routing rule.
- **Task**: bounded repository task, expected risk, and required behavior.
- **Baseline**: prior route or behavior, result, findings, validation, token cost, and turn count.
- **Treatment**: new route or behavior, result, findings, validation, token cost, and turn count.
- **Metrics**: routing correctness, evidence completeness, defect catch rate, validation freshness, over-routing, under-routing, token overhead, and turn overhead.
- **Verdict**: improved, regressed, no-change, unknown, or not-enough-evidence.
- **Caveats**: structural-only, not collected, sample size, evaluator limitations, or unmeasured production behavior.
- **Regression command**: validator or eval command that checks the case.

## Quality Gate
1. Each case has task, baseline, treatment, metrics, verdict, and caveats.
2. Token and turn overhead fields exist, even if set to `not_collected`.
3. Claims distinguish structural validation from empirical behavior.
4. Over-routing and under-routing are explicit metrics.
5. Benchmark data is bounded and contains no raw secrets, raw prompts, user-specific source material, or full command output.
6. Validation command is stated and reproducible from repository source.
7. Reports avoid broad claims beyond the collected evidence.

## Used By
- `change-forge-router`
- `skill-authoring-expert`
- `quality-test-gate`
- `ai-code-review-refactor`
- `change-documentation-gate`
- `agent-execution-discipline`

## Handoff
Hand off benchmark records to `quality-test-gate` for validation, to `ai-code-review-refactor` for spec-first review of AI-authored changes, and to `change-documentation-gate` when release notes or docs mention efficacy.

## Completion Criteria
The capability is complete when every skill-efficacy claim is backed by bounded baseline-versus-treatment records, overhead fields, conservative caveats, reproducible validation, and no unsupported real-world performance assertion.
