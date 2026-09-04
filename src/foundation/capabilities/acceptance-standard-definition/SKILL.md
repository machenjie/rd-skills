---
name: acceptance-standard-definition
description: "`analysis-agent`/`task-agent`/`review-agent`: use when completion needs measurable acceptance evidence; skip when no task-local acceptance standard must be defined."
---

# acceptance-standard-definition

## Registry Trigger

**Use when**

- define measurable acceptance criteria evidence and verification standard

**Do not use when**

- no task-local acceptance standard definition decision is required

## Skill Role

Convert desired behavior into objective done standards proven by tests, review evidence, observability, or accountable stakeholder acceptance. Reject criteria that cannot be falsified.

## High-Value Rules

- Reject vague criteria unless translated into observable outcomes, rejection conditions, and an evidence type.
- For broad work, bound acceptance to the selected deliverable slice and identify deferred acceptance unless an accountable owner approves broader scope.
- When the user specifies a proof gate or order, preserve that mapping and sequence in the acceptance standard.
- Define condition, action, expected result, evidence, and the decision owner when objective proof cannot settle a material product judgment.
- Select negative, denied, error, regression, and recovery criteria in proportion to the affected risk.
- Mark an acceptance criterion ready only from current proof tied to the affected behavior; identify stale, missing, or inaccessible evidence as an acceptance gap.
- Keep implementation correctness and release readiness unaccepted until `quality-test-gate` or the applicable specialist gate judges current proof.
- Trace non-functional claims and criteria to their source, measured objective, control, or applicable standard rather than a qualitative adjective.

## Anti-Patterns

- Accept qualitative criteria or metrics without an owner, unit, population, measurement point, observation window, operating condition, or cited objective or policy.
- Apply criteria outside the explicit task scenario or leave scope-changing conditions unresolved.
- Specify success alone without a rejection condition that blocks acceptance or records owned residual risk.
- Rely on evidence whose production a reviewer cannot repeat from task-accessible sources.
- Omit denied authority, expired state, tenant isolation, invalid input, partial failure, or recovery criteria when the affected boundary and risk trigger them.

## Stop Conditions

Escalate when acceptance depends on unresolved performance or availability metrics, regulated claims, ownerless security controls, customer-contractual SLAs, or external partner contracts. Also escalate for unrehearsable production-like data migration, irreversible side effects, or subjective judgment without an accountable approver. Escalate scope conflicts to the product owner, cross-system criteria to architecture, regulated controls to the security or privacy gate, and reliability thresholds to SRE.

## Output Contract

- acceptance-standard decision with per-criterion condition/action/result, rejection or pass-fail condition, evidence/validator mapping and freshness, missing/stale disposition, decision owner, proof limits, residual-risk owner, and material release consequence
- boundary statement that criterion readiness does not establish implementation correctness or release readiness; current proof judgment remains with `quality-test-gate` or the applicable specialist gate

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Competing criterion shapes change rejection, ownership, or release blocking | Actor, behavior, authority, and criterion shape are already settled | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Criteria span denial, recovery, permissions, or nonfunctional thresholds | One bounded observable outcome has complete negative coverage | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Acceptance depends on fresh validation or accountable stakeholder sign-off | Current artifacts directly prove every blocking criterion | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
