---
name: requirement-clarification
description: Clarifies product-change requirements by separating blocking unknowns, non-blocking unknowns, assumptions, and safe assumptions before implementation begins.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "01"
changeforge_version: 0.1.0
---

# Mission

Convert ambiguous change input into a decision-ready clarification record that separates verified facts, stakeholder claims, repository evidence, project memory, graph leads, execution history, blocking unknowns, non-blocking unknowns, safe assumptions, unsafe assumptions, and owner decisions before implementation begins. The goal is to prevent hidden product, domain, security, legal, operational, data, or release decisions from being silently encoded into code, tests, schemas, permissions, APIs, jobs, or docs.

# When To Use

Use this capability when a request lacks enough specificity about current behavior, desired behavior, actors, scope, non-goals, data ownership, authorization, compatibility, migration, rollout, rollback, observability, acceptance evidence, or authority to safely begin downstream planning or implementation. Also use it when inputs conflict across stakeholders, issues, comments, tickets, project memory, repository graph, prior execution results, or generated artifacts.

# Do Not Use When

Do not use this capability to restructure already-resolved facts, write acceptance criteria, design implementation, decide product/security/legal answers without authority, or delay work on questions that are truly isolated. Route to `requirement-structuring` once blocking unknowns are resolved, `acceptance-standard-definition` when the behavior is known but done evidence is weak, `non-goal-boundary-definition` when the primary gap is scope exclusion, and the relevant specialist gate when the unresolved authority sits in security, data/API, reliability, release, legal, or compliance.

# Stage Fit

Use during requirement intake before design, task planning, code changes, migration work, release work, or review when the implementation path could depend on an unanswered decision. Use during debugging or incident intake when the report names only a symptom and not the desired restored behavior. Use during review when a plan, PR, or agent trajectory appears to have answered an authority question implicitly. Hand off only after the proceed/block decision, minimum safe scope, evidence limits, and owner responses are clear.

# Non-Negotiable Rules

- **Classify every unresolved question before implementation.** Mark each gap as blocking, non-blocking, safe assumption, explicit stakeholder assumption, rejected unsafe assumption, or verified fact.
- **Blocking is mandatory when an answer can change contract, data, permission, lifecycle, migration, rollout, rollback, compliance, money, privacy, reliability, or user-visible behavior.**
- **Non-blocking means isolated, reversible, and owned.** A deferred question needs a safe default, isolation method, follow-up owner, and evidence that the default cannot leak into public behavior.
- **Stakeholder statements are not verified facts.** Treat them as claims until checked against current source, current docs, production-like data, telemetry, generated contracts, or the relevant authority.
- **Repository graph, project memory, and prior execution are evidence leads, not truth.** Accept or reject them against current files, routes, schemas, tests, reports, and known owners.
- **Do not encode answers to blocking questions in implementation choices.** Defaults for authorization, data retention, billing, irreversible actions, or compliance require owner approval.
- **Clarification can reopen during SDD.** If system design exposes material ambiguity about architecture, public API, data, security, migration, rollback, acceptance, or user-visible behavior, route back to clarification or the SDD Design Choice Gate. Design choice authority belongs to the user or owner, not the agent.
- **The clarification record must state what may proceed now, what must wait, and why.** "Proceed with caution" is not enough.
- **Every owner response needs decision shape, owner, due date or trigger, and downstream gate.** A question without an owner is still unresolved.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| Ambiguity triage | Missing current behavior, desired behavior, actor, scope, non-goal, or done signal. | Determine whether planning may start and what must be answered first. | Raw request excerpts, fact/claim/question map, blocking classification. | `requirement-structuring`, `acceptance-standard-definition` | Architecture or implementation planning. |
| Authority decision gap | Unknown touches auth, money, compliance, legal, privacy, migration, retention, rollback, or irreversible action. | Stop hidden authority decisions before they become code. | Decision owner, decision needed, affected surface, downstream gate. | `security-privacy-gate`, `data-api-contract-changer`, `delivery-release-gate` | Safe-default guessing. |
| Stakeholder conflict | Two sources disagree on behavior, priority, scope, date, actor, or acceptance. | Preserve conflict and block only material uncertainty. | Source excerpts, conflict table, authority owner, safe assumption if any. | `non-goal-boundary-definition`, `change-impact-analyzer` | Choosing the louder source. |
| Evidence freshness check | Project memory, graph, old ticket, prior eval, or old validation is used as input. | Accept, reject, or mark stale before relying on it. | Inspected paths/reports, current-source confirmation, freshness limit. | `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis` | Treating memory as source of truth. |
| Partial proceed decision | Some work is safe while other decisions remain open. | Bound the minimum safe scope and forbidden work. | Can-implement-now list, must-wait list, isolation method, review gate. | `non-goal-boundary-definition`, `quality-test-gate` | Opportunistic adjacent work. |
| Bug or incident intake | Symptom-only report, "used to work", screenshot/log without desired restored behavior. | Separate observed behavior, expected behavior, reproduction, and not-yet-diagnosed gap. | Repro condition, observed output, expected output, regression boundary. | `failure-diagnosis`, `regression-testing` | Root-cause claims without requirement clarity. |

# Industry Benchmarks

Anchor against ISO/IEC/IEEE 29148 and IEEE 830 for complete, consistent, unambiguous, verifiable, traceable requirements; Agile Definition of Ready for blocking questions and dependencies; RFC 2119 for normative language; OWASP ASVS for security requirements as first-class requirements; product discovery practice for known facts vs known unknowns; and evidence-based engineering intake for current-source, graph, memory, and execution freshness. Keep this body focused on selection, evidence, output, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for decision trees, classification matrices, templates, graph-memory-trajectory rules, and examples.

# Selection Rules

Select this capability when **the primary problem is whether enough is known to proceed**. Adjacent routing:

- Prefer `requirement-structuring` when facts are resolved and need a professional change brief.
- Prefer `acceptance-standard-definition` when desired behavior is clear but completion evidence is vague.
- Prefer `non-goal-boundary-definition` when exclusions, version limits, or forbidden future artifacts are the primary gap.
- Prefer `scenario-decomposition` when the clarified brief needs path coverage across happy, alternate, edge, failure, abuse, and recovery paths.
- Prefer a specialist gate when a blocking unknown is already known to be security/privacy, data/API, release, reliability, integration, legal, or compliance ownership.

# Risk Escalation Rules

Escalate immediately when the unanswered decision can affect authorization, tenant boundaries, financial records, subscriptions, refunds, ledgers, legal retention, privacy/PII, regulated data, migration behavior, data loss, external contracts, irreversible user actions, incident mitigation, rollback, or public API compatibility. Escalate when an agent or PR proceeds after answering one of those questions implicitly.

# Proactive Professional Triggers

- **Signal:** The request says "just", "quick", "simple", or names a solution but omits current behavior, desired behavior, actor, or done evidence. **Hidden risk:** downstream work optimizes the wrong contract. **Required professional action:** classify gaps before planning. **Route to:** `requirement-structuring`, `acceptance-standard-definition`. **Evidence required:** fact/unknown map and proceed/block decision.
- **Signal:** A permission, tenant, billing, migration, deletion, compliance, or rollback behavior is unstated. **Hidden risk:** implementation embeds an authority decision. **Required professional action:** mark blocking and name the authority owner. **Route to:** `security-privacy-gate`, `data-api-contract-changer`, or `delivery-release-gate` according to the authority surface. **Evidence required:** decision owner, decision shape, downstream gate, and rollback or reversal note.
- **Signal:** Source, ticket, stakeholder, project memory, repository graph, or previous run disagree. **Hidden risk:** stale or conflicting evidence becomes the requirement. **Required professional action:** preserve conflict and verify current source before proceeding. **Route to:** `repository-context-map`, `project-memory-governance`. **Evidence required:** accepted/rejected evidence map, current-source inspection command or report, and freshness limit.
- **Signal:** Non-blocking unknown has no safe default, isolation method, follow-up owner, or not-present check. **Hidden risk:** deferred decision becomes hidden behavior. **Required professional action:** reclassify as blocking or define isolation. **Route to:** `non-goal-boundary-definition`, `quality-test-gate`. **Evidence required:** safe default, forbidden assumption, validation hook.
- **Signal:** Bug report supplies symptom/log/screenshot but no expected restored behavior. **Hidden risk:** diagnosis solves the wrong problem. **Required professional action:** clarify observed vs expected behavior before root cause. **Route to:** `failure-diagnosis`, `regression-testing`. **Evidence required:** reproduction condition, expected output, acceptance signal.

# Critical Details

- Clarification is a gate between ambiguity and implementation, not a meeting summary.
- Blocking unknowns are not failures; they are evidence that implementation would otherwise guess.
- A safe engineering assumption must be reversible, conventional for the current repo, testable, and outside product/security/legal authority.
- An explicit stakeholder assumption must retain its source and verification status.
- A rejected unsafe assumption should state the tempting default and the unacceptable risk it would create.
- Minimum safe scope prevents partial proceed from becoming uncontrolled adjacent work.
- Current-source inspection matters: code, docs, generated contracts, reports, and tests may contradict memory or stakeholder assumptions.
- Requirement clarity is not completion. It only authorizes the next gate when evidence says the downstream path is safe.

### Anti-examples

| Anti-pattern | Failure | Required correction |
| --- | --- | --- |
| Developer assumes "admin-only" for deletion. | Authorization decision is hidden in code. | Mark blocking and request product/security decision. |
| Stakeholder says no existing nulls; migration trusts it. | Production migration fails or corrupts data. | Verify data or mark as unverified stakeholder assumption. |
| "Copy can change later" influences API field naming. | Copy decision becomes public contract. | Isolate copy in i18n/content layer. |
| Old project memory says route exists. | Renamed route or retired behavior is treated as current. | Inspect current source and graph before accepting memory. |
| Partial proceed lacks forbidden work. | Implementer builds the blocked portion while nearby. | State can-implement-now and must-wait surfaces explicitly. |

# Failure Modes

- **Authority downgrade:** Blocking authorization, billing, compliance, migration, or rollback question is classified as non-blocking to maintain velocity.
- **Stakeholder-claim drift:** Stakeholder claim is treated as verified fact and later contradicts source, data, telemetry, or generated contracts.
- **Stale memory trust:** Project memory or prior validation is stale, but implementation trusts it without current-source inspection.
- **Ownerless question:** Clarification asks questions but does not name owners, deadlines/triggers, or decision shape.
- **Overbroad partial proceed:** Partial proceed authorizes too much and lets unapproved schema, endpoint, UI, job, flag, or permission behavior appear.
- **Symptom-only diagnosis:** Bug diagnosis starts from symptoms without expected restored behavior, so the fix passes tests but misses the real requirement.
- **Permanent hidden default:** Non-blocking unknowns have no follow-up owner and become permanent hidden defaults.
- **Unmapped validation gap:** A safe assumption, owner answer, or forbidden artifact is not mapped to a validation command, review check, not-present scan, or residual-risk owner.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 selection, rules, output, and gates. Load only the reference needed for the active clarification decision:

- Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete clarification record.
- Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when blocking/non-blocking classification, safe-default reasoning, stakeholder conflict, partial proceed boundaries, owner response shape, or template detail needs more depth.
- Load [references/evidence-patterns.md](references/evidence-patterns.md) when the clarification depends on current-source proof, repository graph, project memory, execution trajectory, validation freshness, forbidden-artifact scans, tool permission boundaries, or evidence limits.

Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or metadata-only edits with no clarification decision.

# Output Contract

Return a clarification record with:

- `mode_selected` (ambiguity triage, authority decision gap, stakeholder conflict, evidence freshness check, partial proceed decision, bug or incident intake)
- `request_summary` (neutral 1-2 sentence request statement)
- `boundaries_inspected` (request source, ticket/docs, source paths, tests, registry/config, generated artifacts, reports, repository graph, project memory, prior execution, and skipped boundaries with reason)
- `source_evidence` (current facts with paths, commands, reports, stakeholder source, or not-verified marker)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified claims from repo graph, memory, previous plans, previous validations, or execution history)
- `known_facts` (verified current behavior or constraints with source)
- `explicit_stakeholder_assumptions` (stated but not verified, with source and verification needed)
- `safe_engineering_assumptions` (reversible, conventional, testable, not authority-owned, with rationale)
- `unsafe_assumptions_rejected` (tempting assumption, risk, and required evidence or owner response)
- `blocking_unknowns` (id, question, category, owner, decision needed, downstream gate, why blocking)
- `non_blocking_unknowns` (id, question, safe default, isolation method, follow-up owner, validation/check, expiration or trigger)
- `proceed_block_decision` (block, proceed, or partial proceed with justification)
- `minimum_safe_scope` (can implement now, must wait, forbidden assumptions/artifacts, and review boundary)
- `changed_clarification_to_validation_map` (each question, assumption, owner response, evidence claim, safe default, and forbidden scope mapped to validation, review check, or residual risk)
- `handoff_boundaries` (structuring, acceptance, non-goals, scenarios, security, reliability, data/API, release, diagnosis, or quality gate)
- `evidence_limits` (what was not inspected, unverifiable stakeholder claims, stale memory, unknown production data, unavailable telemetry, missing authority, or residual risk owner)

# Evidence Contract

Close requirement clarification only when these answers are concrete:

- **Basis:** selected mode, risk class, and why unanswered decisions block or do not block work.
- **Current evidence inspected:** request source, source files, docs, tests, generated artifacts, reports, graph, memory, and previous execution evidence accepted or rejected.
- **Authority and ownership:** each blocking question has an owner, decision shape, expected date/trigger, and downstream gate.
- **Safe-scope rationale:** non-blocking unknowns have reversible safe defaults, isolation, not-present checks, and follow-up owners.
- **Validation and handoff:** changed-clarification-to-validation map, freshness, evidence limits, residual risk, and next capability are recorded.

# Benchmark Coverage

This capability covers readiness classification, blocking vs non-blocking decisions, safe and unsafe assumptions, stakeholder claim traceability, authority ownership, partial proceed boundaries, graph/memory/trajectory freshness, bug-intake expected behavior, and owner-response routing. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for deeper templates and decision trees.

# Routing Coverage

Routes from `change-intake-compiler`, `change-forge-router`, `acceptance-criteria-builder`, `task-dag-planner`, and specialist gates should arrive here when unresolved intent or authority determines whether work may proceed. Route away when facts are resolved and the primary need is structure, acceptance standards, scenario coverage, task ordering, implementation, test strategy, or release planning.

# Quality Gate

The clarification record is complete only when:

1. Mode, boundaries inspected, source evidence, graph-memory-trajectory judgment, and evidence limits are recorded.
2. Every unresolved question is classified with reasoning as blocking, non-blocking, safe assumption, stakeholder assumption, rejected unsafe assumption, or verified fact.
3. Authorization, money, compliance, data loss, irreversibility, migration, rollback, and public-contract unknowns are blocking unless a named authority approves a bounded safe default.
4. Non-blocking unknowns have safe defaults, isolation methods, follow-up owners, and validation or not-present checks.
5. Stakeholder claims are separated from verified facts and carry source plus verification status.
6. Unsafe assumptions are explicitly rejected with risk and required evidence.
7. Proceed/block/partial-proceed decision is unambiguous and bounded.
8. Minimum safe scope names can-implement-now, must-wait, and forbidden assumptions/artifacts.
9. Blocking unknowns have owner, decision shape, expected date or trigger, and downstream gate.
10. Changed-clarification-to-validation map, handoff boundaries, rollback/reversal note for assumptions, and residual risk owner are explicit.

# Used By

- change-intake-compiler

# Handoff

Hand off to `requirement-structuring` once blocking unknowns are resolved and facts need a traceable brief; `acceptance-standard-definition` when done evidence needs precision; `non-goal-boundary-definition` when partial proceed or exclusions need not-present checks; `scenario-decomposition` when path coverage is the next risk; `security-privacy-gate`, `data-api-contract-changer`, `reliability-observability-gate`, or `delivery-release-gate` when an owner decision sits in that domain; and `quality-test-gate` when validation obligations must be made executable.

# Completion Criteria

The capability is complete when ambiguity is classified, risk-bearing unknowns are blocked with owners, safe assumptions are documented and reversible, graph/memory/trajectory evidence is freshness-scoped, the proceed/block decision is bounded, and the downstream path can continue without silently answering authority questions.
