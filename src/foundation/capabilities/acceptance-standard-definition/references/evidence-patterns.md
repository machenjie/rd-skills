# Acceptance Standard Evidence Patterns

Use this reference when acceptance closure depends on proof freshness, stakeholder authority, or criterion-to-validation mapping. Load only the rows matching the acceptance surface.

## Evidence Map
- **Functional criterion:** map requirement or scenario id to given/when/then/not_then, test command, artifact, exit code, and regression scope.
- **Negative or permission criterion:** prove denied actor, invalid state, tenant or scope boundary, audit/log expectation, same-pattern scan, and release consequence.
- **Non-functional criterion:** prove threshold, scope, environment, benchmark or dashboard/report artifact, freshness, and specialist gate owner.
- **Subjective criterion:** prove single accountable accepter, review artifact, decision date, rejection condition, and what objective evidence remains unavailable.
- **Operational or release criterion:** prove rollback, alert, dashboard, runbook, support diagnosis, owner, and not-run or stale validation status.

## Evidence Rules
- For a directly executable criterion, record its acceptance-to-validator mapping. When acceptance depends on stakeholder judgment, freshness-sensitive evidence, or a material proof limit, record the accountable owner or review artifact and evidence freshness. The record states what the evidence proves, its non-proofs, and the recommended next step.
- prior task evidence, generated plans, repository inspection, and old tickets are selectors only until current source, owner review, or validation evidence confirms the criterion.
