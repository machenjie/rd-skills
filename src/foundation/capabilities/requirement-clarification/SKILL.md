---
name: requirement-clarification
description: "`analysis-agent`: use when goals, constraints, assumptions, or missing facts need blocking, non-blocking, and safe-assumption decisions; skip when requirements are clear."
---

# requirement-clarification

## Registry Trigger

**Use when**

- clarify ambiguous goals constraints assumptions missing information

**Do not use when**

- no task-local requirement clarification decision is required

## Skill Role

Detect material ambiguity, search local evidence, classify blockers, bound assumptions, frame options, and identify proceed-or-wait boundaries. Exclude requirement restructuring and implementation.

## High-Value Rules

- **Clarify only decision-changing ambiguity.** Name the missing or conflicting fact, affected behavior or risk, plausible interpretations, and what implementation or validation would differ.
- **Search current local evidence before asking.** Inspect request context, contracts, repository structure, schemas, configuration, tests, examples, and accepted decisions, while treating stale or indirect evidence as a lead rather than authority.
- **Classify the decision boundary.** Block when interpretations could change public behavior, data, permission, safety, compatibility, irreversible effects, or acceptance; continue with a bounded assumption for reversible local choices.
- **Make assumptions explicit and testable.** State selected interpretation, source or rationale, affected scope, consequence if wrong, validation path, and signal that reopens the decision.
- **Offer bounded options when authority is external.** Present viable choices with material tradeoffs and a recommended default only where current evidence supports one, avoiding broad preference questions.
- **Record what can proceed and what waits.** Separate safe analysis or implementation slices from blocked decisions, dependencies, and externally owned evidence so uncertainty does not freeze unrelated work.
- **Update downstream artifacts after resolution.** Propagate the accepted answer into scope, contracts, rules, tasks, acceptance, and risk boundaries instead of leaving clarification detached from execution.

## Anti-Patterns

- Ask broad questions answerable from current repository or contract evidence.
- Hide a material product, permission, data, or compatibility choice inside an implementation assumption.
- Treat all uncertainty as blocking, or proceed under a vague caution with no scope, owner, or reopen signal.

## Stop Conditions

Escalate when decision authority is unavailable, current sources conflict, a safe bounded assumption cannot contain consequence, or the unresolved choice affects irreversible, regulated, financial, security, privacy, safety, or public compatibility behavior.

## Output Contract

- clarification decision with material ambiguity, inspected evidence, blocking classification, bounded assumptions or options, proceed and wait boundary, owner questions, reopen signals, and downstream updates

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | unknown authority reversibility or partial progress leaves options viable | one verified owner decision resolves every material ambiguity | analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | request contains blocking unknowns assumptions conflicts or unsafe defaults | current facts and authority establish all behavior-changing decisions | analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | stakeholder source freshness or prior-decision claims need verification | current source and owner records prove each clarification fact | analysis-agent | evidence-record, proof-limit, residual-risk |
