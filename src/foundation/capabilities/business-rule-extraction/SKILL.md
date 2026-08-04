---
name: business-rule-extraction
description: "`analysis-agent`/`task-agent`: use when extracting policies, calculations, constraints, or invariants from scattered layers; skip when no business-rule decision is needed."
---

# business-rule-extraction

## Registry Trigger

**Use when**

- extract invariants policies calculations constraints and decision authority

**Do not use when**

- no task-local business rule extraction decision is required

## Skill Role

Extract decisions from current policy, contracts, code, data, examples, and owner evidence. Normalize conditions, outcomes, invariants, precedence, uncertainty, and enforcement boundaries without redesigning the domain.

## High-Value Rules

- **Name source and authority separately.** A code path, document, example, or data pattern shows current behavior; identify which current contract, policy, invariant, or accountable owner can decide the intended rule.
- **Normalize each decision boundary.** Express trigger, relevant facts, allowed and denied outcomes, state transition or calculation, effective scope, exceptions, and evidence of precedence without copying prose mechanically.
- **Distinguish invariant from workflow.** Preserve conditions that protect valid business state while treating UI order, approvals, handoffs, and operational habits as mechanisms unless an authoritative rule makes them consequential.
- **Resolve overlap and precedence explicitly.** Show how general, product, tenant, jurisdiction, temporal, and exception rules interact; do not infer precedence from file order or the last code branch inspected.
- **Preserve precision and uncertainty.** Carry units, currency, timezone, rounding, effective dates, subject scope, and unknown or contradictory terms into the extracted result instead of silently choosing a convenient interpretation.
- **Trace rule to enforcement and observation.** Locate current writers, validators, readers, bypasses, stored state, and externally enforced boundaries; identify duplicated or missing enforcement without assigning architecture prematurely.
- **Test the decision surface.** Derive positive, boundary, negative, conflicting, stale, and exception cases that can falsify the normalized rule, then hand implementation and final acceptance to the relevant owners.

## Anti-Patterns

- Treat the most recent code path, UI wording, or example as authoritative without checking contract and owner evidence.
- Merge distinct policy, calculation, eligibility, permission, and workflow concerns into one vague rule.
- Hide ambiguity behind a polished requirement or invent precedence, default, exception, or threshold absent from current authority.

## Stop Conditions

Escalate when authoritative sources conflict, ownership is absent, a material exception or precedence is unknown, or implementation differs from policy without accepted authority. Escalate for specialist review when extraction crosses a regulated, financial, permission, safety, or destructive-data boundary.

## Output Contract

- normalized business-rule set with source and authority, conditions, outcomes, invariants, precedence, precision, exceptions, enforcement map, falsifying cases, and unresolved terms

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Rule authority, precedence, or decision-table representation remains contested | One authoritative rule owner and enforcement layer are established | analysis-agent, task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Rules span exceptions, effective dates, precedence, or bypass entry points | No business decision or invariant changes | analysis-agent, task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Rule completeness depends on fresh entry-point and replay evidence | No rule-authority claim is being finalized | analysis-agent, task-agent | evidence-record, proof-limit, residual-risk |
