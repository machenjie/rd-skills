# Professionalism Enhancement Standard

Owner: ChangeForge skill maintainers.

Responsibility: define the authoring and evaluation standard for professional
skills and high-value foundation capabilities. This document governs
professional engineering judgment, risk discovery, evidence closure, and
anti-bloat discipline. It does not create a new runtime layer, marketplace,
catalog, persona, slash command, plugin surface, MCP workflow, or personal asset
mapping.

## Scope

Apply this standard when modifying:

- `src/professional-skills/*/SKILL.md`
- selected professional-skill `references/`
- key foundation capabilities under `src/foundation/capabilities/`
- professionalism and benchmark evaluation scripts

Professional skills remain the top-level entry points. Foundation capabilities
remain selectively loaded support rules. Domain extensions remain domain-specific
enhancements. In `recommended` and `full` profiles, foundation capabilities must
stay compiled into professional skill `references/`, not promoted to top-level
skills.

## Mode Matrix Standard

Every professional skill should distinguish the real engineering mode it is
serving. A generic "When To Use" list is not enough for non-trivial skills.

Supported modes, tailored per skill:

| Mode | Use |
| --- | --- |
| `new-build` | New capability, feature, module, endpoint, workflow, schema, integration, or operational path. |
| `modify-existing` | Existing logic, contract, screen, workflow, policy, query, deployment, or test is changed. |
| `bug-fix` | A known defect is corrected and regression risk must be bounded. |
| `debugging-diagnosis` | Root cause is unknown and diagnosis evidence is required before mutation. |
| `code-review` | Existing or AI-generated code is reviewed for correctness, risk, maintainability, and evidence. |
| `refactoring` | Behavior-preserving movement, extraction, simplification, or cleanup. |
| `testing` | Test strategy, coverage repair, fixtures, assertions, or verification evidence. |
| `release-delivery` | Rollout, rollback, migration, configuration, CI/CD, or runtime delivery. |
| `performance-reliability` | Latency, throughput, capacity, concurrency, retry, rate limit, circuit breaker, fallback, observability, or incident risk. |
| `security-sensitive` | Authentication, authorization, tenant isolation, sensitive data, secrets, input boundaries, audit, abuse, or privacy risk. |

Each mode entry must include:

- **Trigger signals**: concrete signals in the user request, code, tests, logs,
  diff, config, or runtime behavior.
- **Professional focus**: the judgment an experienced engineer must make in
  that mode, not a task checklist.
- **Required evidence**: files inspected, boundaries traced, commands run,
  outputs observed, compatibility checked, or risks ruled out.
- **Common hidden risks**: risks users often omit, such as same-pattern defects,
  object ownership, partial success, release skew, stale fixtures, or silent
  fallbacks.
- **Companion capabilities/gates**: the targeted capabilities or professional
  gates to load when the mode signals require them.
- **Explicit skip guidance**: what should not be loaded or expanded by default
  for that mode.

Mode matrices should stay concise in `SKILL.md`. If the matrix needs examples,
decision tables, or long failure catalogs, put those in a skill-owned
`references/` file and link it from the body with a loading condition.

## Proactive Professional Triggers Standard

Every professional skill must include hidden-risk triggers. These are not normal
checklists. They are early warning patterns that let an agent upgrade the route
before the user has named the risk.

Required trigger format:

- **Signal:**
- **Hidden risk:**
- **Required professional action:**
- **Route to:**
- **Evidence required:**

Trigger quality rules:

- The signal must be something the user, code, diff, logs, config, test, or
  prompt can expose without explicitly saying the risk name.
- The hidden risk must be non-obvious and materially change the required
  professional path.
- The action must force inspection, route repair, capability loading, or
  validation, not generic advice.
- The route must name existing professional skills, foundation capabilities, or
  domain extensions.
- The evidence must be concrete enough to prove the trigger was addressed or
  ruled out.
- A trigger like "tests mentioned -> run tests" is not sufficient. A trigger
  like "bug fix touches one permission query -> same-pattern scan for
  tenant/object ownership filters" is sufficient.

Minimum trigger count:

- Core professional skills: at least 5 high-value triggers.
- High-risk professional skills such as security, reliability, delivery,
  backend, data, integration, and AI code review: at least 8 triggers when the
  body can hold them without violating content governance. Otherwise keep 5-10
  critical trigger summaries in `SKILL.md` and place the full list in
  `references/`.

## Evidence Contract Standard

Every professional skill Output Contract or Evidence Contract must be able to
answer these questions:

- **Mode selected**: Which engineering mode was selected, and which signal
  selected it?
- **Inspected boundaries**: Which files, modules, interfaces, configs, callers,
  data boundaries, permission boundaries, release boundaries, or external
  contracts were inspected?
- **Professional judgment**: What was determined, what remains possible, and
  which plausible risks were ruled out with evidence?
- **Reuse and placement rationale**: Why does new or modified code belong here?
  What reuse candidates, existing patterns, ownership boundaries, and
  public/private decisions were considered?
- **Behavior preservation**: For modification, refactor, review, and bug fix
  modes, what old behavior is intentionally preserved and how was that proven?
- **Validation evidence**: Which commands, tests, manual checks, inspections, or
  generated reports ran, and what was the result?
- **What evidence proves**: Which obligation or risk is covered by each piece of
  evidence?
- **What evidence does not prove**: Which adjacent risks, environments, scales,
  consumers, or failure paths remain unproven?
- **Residual risk**: What was not verified, why, who owns it, and what
  compensating evidence or follow-up gate remains?
- **Next gate / handoff**: Which skill, capability, quality gate, release gate,
  or handoff target should run next, or why no next gate is required?

The contract must be answerable from the agent's actual work. Completion claims
without command output, inspected boundary lists, or residual-risk statements do
not satisfy the contract.

## Professionalism Eval Standard

`scripts/eval-skill-professionalism.py` scores professional skills and
foundation capabilities with the dimensions below. Each dimension is 0-5:

| Dimension | Measures |
| --- | --- |
| `trigger_accuracy` | Signals route the right skill/capability without broad catch-all language. |
| `mode_coverage` | The body distinguishes real engineering modes and has enough mode-specific evidence. |
| `stage_fit` | The skill/capability names its engineering stage fit and avoids cross-stage overloading. |
| `professional_depth` | Rules reflect senior engineering judgment and concrete failure modes. |
| `proactive_trigger_quality` | Hidden-risk triggers include signal, risk, action, route, and evidence. |
| `failure_mode_coverage` | Known professional failure modes are named with consequences. |
| `evidence_contract_strength` | Output/Evidence Contract answers boundary, judgment, validation, and residual risk. |
| `output_actionability` | Output is specific enough for implementation, review, testing, release, or handoff. |
| `boundary_clarity` | Scope, skip guidance, ownership, trust, module, data, and release boundaries are explicit. |
| `reference_precision` | References are targeted, linked, and selected by policy instead of dumped into the body. |
| `validation_obligation` | Validation commands, test proof, review proof, or manual evidence are required. |
| `anti_bloat_control` | Body stays within governance budgets and avoids duplicated template prose. |

Evaluation behavior:

- Default mode is warning-only. The script must not fail the build solely because
  a score is below threshold.
- Markdown and JSON reports are required:
  - `reports/skill-professionalism-eval.md`
  - `reports/skill-professionalism-eval.json`
  - `reports/professional-coverage-matrix.md`
  - `reports/professional-coverage-matrix.json`
- Suggested warning thresholds:
  - dimension score `<= 2`
  - total score below 42 out of 60
  - required professional sections missing
  - trigger section present but lacking hidden risk, route, or evidence fields
- JSON must preserve per-skill scores and warnings so maintainers can track
  improvement over time.
- Markdown must prioritize actionable findings over cosmetic advice.

The coverage matrix is generated output, not a catalog surface. It covers all
professional skills and key foundation capabilities across Mode Matrix,
Proactive Triggers, Evidence Contract, Failure Modes, Quality Gate, Reference
Loading Hint, Routing Coverage, Benchmark Coverage, and Output Contract
Strength.

`scripts/eval-professional-benchmarks.py` supports schema-only validation and
offline baseline-vs-with-skill comparison. When a benchmark case includes
`baseline_output.md` and `with_skill_output.md`, comparison mode checks that the
with-skill output covers more professional obligations without calling a model.
It writes:

- `reports/professional-benchmarks-report.md`
- `reports/professional-benchmarks-report.json`

## Anti-Bloat And Reference Precision

`SKILL.md` bodies should keep the decision-critical content:

- mission, use/skip boundaries
- non-negotiable rules
- mode matrix summary
- highest-value proactive triggers
- evidence/output contract
- reference loading policy
- quality gate and handoff

Move deep examples, expanded mode tables, trigger catalogs, failure catalogs,
and long technique references into `references/` when they would make the body
hard to scan. Every new reference must be linked from the body with a loading
condition and must serve selected professional judgment, not general education
or user-specific content mapping.
