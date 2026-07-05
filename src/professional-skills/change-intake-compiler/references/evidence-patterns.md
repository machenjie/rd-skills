# Change Intake Evidence Patterns

Use this reference when intake closure depends on raw-input-to-field mapping, stakeholder authority, source freshness, blocking-question evidence, or proof limits. Keep `SKILL.md` for selection and output rules; load this file only for concrete evidence closure.

## Evidence Map

- **Raw input synthesis:** map each source excerpt to fact, assumption, decision, conflict, or open question; name source, date or artifact path, and authority.
- **Current behavior:** record observable evidence, repro command or condition, screenshot/log/report path when available, and what remains unverified.
- **Desired behavior:** record outcome-first statement, implementation choices moved to constraints/options, non-goals preserved, and acceptance signal.
- **Stakeholder conflict:** record conflicting sources, affected contract/risk, blocking status, owner, deadline, and safe assumption only when non-blocking.
- **Scope boundary:** record affected product surfaces, skipped specialist gates with rationale, residual unknowns, and next gate.

## Intake Field Map

```yaml
raw_input_to_change_request_map:
  source: ""
  field: current_behavior | desired_behavior | non_goal | constraint | assumption | open_question | user_value | completion_signal | risk_flag
  excerpt_or_evidence: ""
  classification: fact | assumption | decision | conflict | question
  owner: ""
  validation_path: ""
  residual_risk: ""
```

## Closure Checks

- Do not turn a solution-first request into an implementation task until the problem and desired behavior are outcome-first.
- Treat missing authority as blocking for data, security, contract, money, migration, or irreversible behavior.
- Separate intake readiness from impact analysis, design approval, implementation correctness, and release readiness.
- Name any unavailable source channel, stakeholder confirmation, repro evidence, or product surface as an evidence limit.
