---
name: skill-efficacy-benchmark
description: Defines baseline-versus-treatment evaluation for ChangeForge skill and capability changes, including routing quality, evidence quality, review defects, token and turn overhead, and caveat discipline.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "121"
changeforge_version: 0.1.0
---

# Mission
Evaluate whether a ChangeForge skill, capability, routing rule, hook prompt, or benchmark change improves professional agent behavior without making unsupported real-world claims. The benchmark compares baseline and treatment behavior against explicit tasks, defect outcomes, routing quality, evidence quality, and token or turn overhead.

# When To Use
- When adding or materially changing skills, foundation capabilities, routing rules, stage signals, hook prompts, or evaluation fixtures.
- When claiming that a skill improves agent quality, evidence, routing, review, validation, or repair behavior.
- When a regression fixture should prove over-routing, under-routing, wrong placement, missing validation, or unsafe tool behavior.
- Before release notes or documentation describe a professional behavior improvement.

# Do Not Use When
- The change is a typo or formatting-only edit with no professional behavior claim.
- The user asks only to author a capability stub without evaluating its effect.
- The available data is structural only and the output would be framed as real-world performance.

# Boundary And Source Truth
The capability owns benchmark evidence for ChangeForge skill behavior claims; it does not own product analytics, live user productivity measurement, private prompt mining, or application performance experiments. Source truth is the bounded task, baseline artifact, treatment artifact, evaluator command, validator output, registry or routing diff, and explicit caveat. Project memory, repository graph, execution trajectory, generated reports, and prior runbooks are selectors that can widen benchmark scope, but they are not proof until reconciled with current source and validation output.

# Stage Fit
Use during skill-authoring, routing-rule, hook-runtime, eval-fixture, report-generation, review, validation, testing, code-review, and release-readiness stages when a professional behavior claim needs evidence. Use before final handoff when the change says a skill is more professional, safer, deeper, broader, more efficient, better routed, or better coupled to memory, graph, validation, or execution discipline.

# Non-Negotiable Rules
- Do not claim real-world efficacy without representative baseline and treatment evidence.
- Every benchmark case must define a task, baseline, treatment, metrics, verdict, and caveats.
- Track token and turn overhead even when not collected; use `not_collected` rather than omitting the fields.
- Distinguish structural fixture validation from empirical agent performance.
- Record over-routing and under-routing risk, not only success.
- Use an explicit required-reference allow-list; never use "all references" as a treatment plan.
- Treat skill, capability, router, hook, memory, graph, validation, trajectory, and adapter changes as behavior surfaces unless proven docs-only.
- Do not use benchmark fixtures as a general-purpose source corpus.
- Keep benchmark inputs bounded, reproducible, and reviewable in repository source.

# Industry Benchmarks
- **A/B experiment discipline**: Treatment claims require baseline, treatment, metric, and caveat.
- **Evaluation-driven development**: Behavior changes ship with fixtures that can catch regressions.
- **Human code review quality**: Findings, missing tests, and false approval are tracked as review outcomes.
- **Cost-aware AI evaluation**: Quality improvements must be balanced against token and turn overhead.
- **Reproducible research**: Claims separate observed evidence from unsupported generalization.

Use [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete benchmark record. Use [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when a case needs deeper metric definitions, baseline/treatment comparison patterns, structural-vs-empirical classification, over/under-routing guards, or privacy-safe fixture rules. Use [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on graph, memory, trajectory, validation freshness, runtime profile boundary, report generation, or what the benchmark proves versus does not prove.

# Mode Matrix
| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Skill behavior benchmark | Skill, capability, reference, or routing behavior changes. | Compare baseline and treatment on the same bounded task. | Task, baseline output, treatment output, metrics, verdict, caveats. | `skill-authoring-expert`, `quality-test-gate` | Live productivity claims. |
| Routing and reference budget benchmark | Route, trigger, used_by, reference loading, or context budget changes. | Prove better selection without over-routing or context bloat. | Selected/skipped references, over-routing guard, under-routing case, token/turn overhead. | `change-forge-router`, `repository-context-map` | Loading all references as treatment. |
| Evidence and closure benchmark | Evidence Contract, Quality Gate, validation, review, or handoff rules change. | Prove closure catches weak evidence without overclaim. | Required proof fields, negative baseline, validation command, stale/not-run disclosure. | `validation-broker`, `plan-execution-consistency` | Report-only confidence. |
| Memory/graph/trajectory benchmark | Memory, graph, trajectory, hook prompt, or runtime support influences closure. | Ensure selector evidence is reconciled with current source and validation. | Accepted/rejected memory, graph freshness, trajectory order, changed-skill-to-validation map. | `project-memory-governance`, `repository-graph-analysis`, `execution-trajectory-analysis` | Treating selectors as proof. |

# Selection Rules
- Select this capability when a skill authoring change introduces or changes expected agent behavior.
- Select it when routing, hook runtime, eval fixtures, or professional benchmark scripts are updated.
- Select it when project memory, repository graph, validation broker, trajectory, or executor adapter semantics affect closure evidence.
- Select it when documentation says a capability improves safety, review quality, evidence, or validation.
- Select it with `quality-test-gate` when benchmark validation becomes part of release evidence.
- Select it with `ai-code-review-refactor` when generated skill content needs spec-first review before quality claims.

# Proactive Professional Triggers
- **Signal:** a skill, capability, routing rule, hook prompt, or reference change claims better professionalism, safety, review quality, validation, or efficiency without a baseline-versus-treatment case. **Hidden risk:** prose improvement is accepted as behavior evidence. **Required professional action:** require a bounded task, baseline output, treatment output, metric set, verdict, and caveat before the claim can close. **Route to:** `skill-authoring-expert`, `quality-test-gate`, `agent-execution-discipline`. **Evidence required:** case id, source diff, baseline/treatment artifacts, validator command, and claim boundary.
- **Signal:** a routing or reference-loading change improves a score but does not test over-routing, under-routing, selected/skipped references, or token/turn overhead. **Hidden risk:** a higher score hides context waste or missed risk. **Required professional action:** add an over-routing guard, under-routing case, context budget record, and overhead fields even when values are `not_collected`. **Route to:** `change-forge-router`, `repository-context-map`, `plan-execution-consistency`. **Evidence required:** benchmark case id, selected route, skipped reference reasons, over-routing guard result, under-routing guard result, token/turn fields, and residual-risk owner.
- **Signal:** project memory, repository graph, execution trajectory, generated reports, or prior runbooks are used as proof that the treatment improved. **Hidden risk:** stale selector evidence becomes empirical efficacy. **Required professional action:** reconcile selector evidence with current source, validation freshness, and final diff before accepting it. **Route to:** `project-memory-governance`, `repository-graph-analysis`, `execution-trajectory-analysis`, `validation-broker`. **Evidence required:** accepted/rejected memory, graph freshness, trajectory order, changed-skill-to-validation map, and evidence limits.
- **Signal:** benchmark data includes raw prompts, secrets, environment values, full command output, personal archives, or user-specific source material. **Hidden risk:** evaluation fixtures become a privacy or corpus-ingestion channel. **Required professional action:** redact or reject the data, keep bounded structural facts, and disclose the privacy boundary. **Route to:** `security-privacy-gate`, `agent-tool-permission-sandbox`, `skill-authoring-expert`. **Evidence required:** excluded sensitive material, retained bounded facts, fixture source, redaction rule, and rollback note.
- **Signal:** an eval fixture passes by keyword presence, section existence, or generic score movement without checking the forbidden behavior. **Hidden risk:** wrong or unverified benchmark green status hides that professional behavior did not change. **Required professional action:** require the negative baseline, forbidden treatment output, expected repaired behavior, and validator that fails for the old behavior. **Route to:** `ai-code-review-refactor`, `quality-test-gate`, `validation-broker`. **Evidence required:** failing or weak baseline, treatment comparison, defect caught, validator output, and caveat.

# Risk Escalation Rules
- Escalate when a change makes an efficacy claim without baseline/treatment data.
- Escalate when a fixture passes by matching keywords but does not test the professional behavior claimed.
- Escalate when token or turn overhead is omitted.
- Escalate when routing improvements hide over-routing drag or under-routing safety gaps.
- Escalate when benchmark data includes raw prompts, secrets, user-specific source material, or unbounded command output.

# Critical Details
- A benchmark can be useful even when overhead is `not_collected`; the caveat must be explicit.
- A structural fixture validates schema and evaluation plumbing, not live agent productivity.
- The unit of comparison is the same task under baseline and treatment conditions.
- Verdicts should be conservative: `unknown` or `not_enough_evidence` is better than an inflated win.
- Benchmark reports should name what changed, what improved, what did not, and what remains unmeasured.

# Failure Modes
- **Unsupported claim**: A capability is described as improving code quality without comparative evidence.
- **Keyword-only pass**: The eval checks that a capability name appears but not whether the route is correct.
- **Overhead blind spot**: Treatment improves one score but doubles turns or tokens and the cost is not recorded.
- **Fixture contamination**: Test data includes user-specific source material or raw prompts that should not be source content.
- **No negative cases**: A benchmark validates happy paths but misses destructive tool, wrong placement, or extra-file drift.
- **Selector overclaim**: project memory, graph output, or trajectory order is reported as efficacy proof without current source and validation reconciliation.
- **Boundary drift**: a benchmark fixture becomes a general corpus of user prompts, source archives, or full command outputs instead of a bounded case.
- **Report-only confidence**: a regenerated report improves the numeric score but the changed skill lacks a case that would fail on the prior behavior.

# Reference Loading Policy
The `SKILL.md` body is the authoritative L1/L2 contract for benchmark routing, output shape, and closure gates. Load references only when their decision surface is active:

- **L1:** Use this `SKILL.md` only for ordinary skill-authoring route selection, compact benchmark records, and small review.
- **L2:** Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete benchmark case, score-improvement claim, route/reference budget case, or report-supported handoff.
- **L3:** Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when defining metric sets, baseline/treatment comparison, over-routing and under-routing guards, context overhead, privacy-safe fixtures, or structural-vs-empirical verdicts.
- **Evidence closure:** Load [references/evidence-patterns.md](references/evidence-patterns.md) when graph, memory, execution trajectory, validation freshness, generated reports, runtime profile output, or proof limits decide whether a benchmark can close.
- **Companion references:** Use selected companion capability references only when the concrete case depends on skill authoring, routing, validation brokerage, graph, memory, trajectory, context control, or plan-execution reconciliation.
- **Anti-bloat rule:** Do not load unrelated references, live benchmark logs, raw prompts, private source archives, or "all references" as a treatment condition.

# Output Contract
Return a `skill_efficacy_benchmark` record with:
- **Mode selected**: skill behavior benchmark, routing/reference budget benchmark, evidence/closure benchmark, or memory/graph/trajectory benchmark.
- **Boundary scope**: source-vs-dist status, runtime profile, public/private claim boundary, owner, and non-goals.
- **Source evidence**: source files, registry or routing diff, generated reports, validation output, graph/memory/trajectory evidence, and skipped evidence with reason.
- **Case id**: stable identifier.
- **Capability or skill under test**: selected skill, capability, hook, or routing rule.
- **Task**: bounded repository task, expected risk, and required behavior.
- **Baseline**: prior route or behavior, result, findings, validation, token cost, and turn count.
- **Treatment**: new route or behavior, result, findings, validation, token cost, and turn count.
- **Metrics**: routing correctness, evidence completeness, defect catch rate, validation freshness, over-routing, under-routing, token overhead, and turn overhead.
- **Context budget**: mode (`minimal`, `single-stage`, `staged-plan`, or `full`), selected/skipped reference counts, proxy token estimate, and over-budget decision.
- **Graph memory trajectory coupling**: accepted/rejected memory claims, graph freshness, trajectory order, validation broker status, and selector limits.
- **Changed skill to validation map**: each changed skill body, reference, registry route, hook prompt, eval fixture, generated report, or runtime profile output mapped to validator, reviewer, owner approval, or residual risk.
- **Verdict**: improved, regressed, no-change, unknown, or not-enough-evidence.
- **Caveats**: structural-only, not collected, sample size, evaluator limitations, or unmeasured production behavior.
- **Regression command**: validator or eval command that checks the case.
- **Claim boundary and evidence limits**: what the benchmark proves, what it does not prove, and which production, user, or agent-population claims remain unsupported.
- **Handoff boundaries**: next owner for skill authoring, routing, validation, review, documentation, release, or privacy remediation.

# Evidence Contract
Close a skill efficacy benchmark only when these answers are concrete:
- **Basis:** the claim being evaluated, the behavior surface changed, and why a benchmark is required instead of prose.
- **Current evidence:** target source, registry/routing, generated reports, validation output, graph, memory, trajectory, and skipped boundaries inspected.
- **Comparison and boundary:** same task under baseline and treatment, source-vs-dist and runtime profile boundary, owner, selected/skipped references, and public/private claim limits.
- **Metrics and overhead:** routing correctness, evidence completeness, defect catch rate, validation freshness, over-routing, under-routing, token overhead, turn overhead, and `not_collected` caveats where needed.
- **Validation and closure:** regression command, changed-skill-to-validation map, what evidence proves, what evidence does not prove, rollback note, residual risk, and next gate.

# Benchmark Coverage
This capability covers baseline/treatment comparison, skill/routing/reference behavior claims, graph-memory-trajectory selector discipline, context budget overhead, over-routing and under-routing guards, privacy-safe fixture boundaries, structural-vs-empirical caveats, validation freshness, and evidence-limited handoff.

# Routing Coverage
Routes from `change-forge-router`, `skill-authoring-expert`, `quality-test-gate`, `ai-code-review-refactor`, `change-documentation-gate`, and `agent-execution-discipline` should arrive here when a ChangeForge behavior claim, benchmark case, routing/reference budget, hook/runtime support behavior, report/eval fixture, or professional evidence improvement needs baseline-versus-treatment proof. Route away when the task is pure formatting with no behavior claim or when product analytics, live user experimentation, or application performance measurement is the primary evidence domain.

# Quality Gate
1. Each case has task, baseline, treatment, metrics, verdict, and caveats.
2. Token and turn overhead fields exist, even if set to `not_collected`.
3. Claims distinguish structural validation from empirical behavior.
4. Over-routing and under-routing are explicit metrics.
5. Required references are an allow-list; skipped references have a reason.
6. Benchmark data is bounded and contains no raw secrets, raw prompts, user-specific source material, or full command output.
7. Validation command is stated and reproducible from repository source.
8. Reports avoid broad claims beyond the collected evidence.
9. Source-vs-dist, runtime profile, owner, public/private claim boundary, and non-goals are explicit.
10. Graph, memory, trajectory, generated report, and validation evidence are accepted, rejected, stale, or not verified before influencing the verdict.
11. Each changed skill, reference, registry route, hook prompt, eval fixture, report, or runtime output maps to validation or residual risk.
12. Privacy and data boundaries exclude raw prompts, secrets, environment values, private archives, and unbounded source corpora.
13. The final verdict includes what evidence proves, what it does not prove, rollback note, residual risk, and next gate.

# Used By
- `change-forge-router`
- `skill-authoring-expert`
- `quality-test-gate`
- `ai-code-review-refactor`
- `change-documentation-gate`
- `agent-execution-discipline`

# Handoff
Hand off benchmark records to `quality-test-gate` for validation, to `ai-code-review-refactor` for spec-first review of AI-authored changes, and to `change-documentation-gate` when release notes or docs mention efficacy.

# Completion Criteria
The capability is complete when every skill-efficacy claim is backed by bounded baseline-versus-treatment records, overhead fields, conservative caveats, reproducible validation, and no unsupported real-world performance assertion.
