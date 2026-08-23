---
name: change-intake-compiler
description: "Use `analysis-agent` when engineering intent lacks desired behavior, boundaries, constraints, or completion signals. Skip requests with an accepted Engineering Brief and no-repo direct-answer work."
---

# change-intake-compiler

## Role

Support `analysis-agent` in separating source-backed change intent from
reversible assumptions and user-owned decisions.

## When To Use

- ambiguous request
- missing desired behavior

## Do Not Use

- accepted Engineering Brief already exists
- no-repo direct-answer mode

## Required Inputs

- request summary
- observed current behavior

## Professional Decision Rules

- Define the intent slice as the smallest independently observable unit containing current behavior, desired behavior, acceptance or completion signal, constraints, non-goals, and affected surfaces.
- Separate facts discoverable from source from choices only the user can make.
- Proceed with explicit reversible assumptions only when they cannot change public behavior, data, authorization, or domain meaning.
- Reject solution wording that hides the actual problem or success condition.

## High-Value Gotchas

- Do not turn an ambiguous request into an invented requirement.
- A source-discoverable fact is not a reason to interrupt the user.
- Make every reversible assumption explicit in the output.

## Evidence Resolution Source Declaration

The following closed declaration is the semantic source for control-plane gap
projections. Control may retain labels and actions only when they validate
exactly against this declaration.

<!-- BEGIN CHANGEFORGE EVIDENCE RESOLUTION SOURCE -->
```json
{"contract":"changeforge.evidence-resolution-source/v1","gap_classes":[{"id":"repo-resolvable-fact","source_semantic":"discoverable-fact","source_anchor":"A source-discoverable fact is not a reason to interrupt the user.","subtypes":[]},{"id":"user-owned-choice","source_semantic":"user-owned-choice","source_anchor":"Classify each gap as discoverable fact, reversible assumption, or user-owned choice.","subtypes":["semantic-choice","execution-level-choice"]},{"id":"route-or-material-unknown","source_semantic":"unsafe-or-non-reversible-assumption","source_anchor":"Proceed with explicit reversible assumptions only when they cannot change public behavior, data, authorization, or domain meaning.","subtypes":[]}],"decision_rules":{"repo-resolvable-fact":{"question":"forbidden","route_affecting":"analyzed","otherwise":"direct-bounded-discovery"},"semantic-choice":{"question":"one-minimum-concrete","invalidation":"protected-brief-semantics"},"execution-level-choice":{"question":"one-minimum-concrete","invalidation":"execution-level-projection-only"},"route-or-material-unknown":{"question":"forbidden","decision":"analysis-or-fail-closed"}}}
```
<!-- END CHANGEFORGE EVIDENCE RESOLUTION SOURCE -->

## Execution Checklist

1. Reconstruct current behavior, desired behavior, acceptance or completion signal, constraints, non-goals, and affected surfaces from the request and source evidence.
2. Classify each gap as discoverable fact, reversible assumption, or user-owned choice.
3. Choose the smallest intent slice that retains every required field and whose acceptance can be observed independently.
4. Stop routing when a missing choice can change contract, data, authority, or domain meaning.

## Stop / Escalation Conditions

- Stop planning when current behavior, desired behavior, constraints, non-goals,
  completion signal, authority, or affected surface is missing.
- Escalate assumptions that could change contract, data, security, migration,
  rollback, user-visible behavior, or acceptance.
- Stop solution-first requests when the named implementation is not backed by an outcome, constraint, authority, and rejected simpler option.
- Stop conflict resolution when stakeholders disagree on behavior, priority, rollout, role, date, or acceptance and no decision owner or deadline is named.
- Escalate when required source channels, issue trackers, production evidence, or stakeholder context cannot be inspected through authorized, redacted, fresh read/search access.

## Output Contract

- minimal intent slice with current behavior, desired behavior, observable acceptance or completion signal, constraints, non-goals, and affected surfaces
- assumptions
- open questions

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [change request](references/change-request-template.md) | template | Drafting or normalizing the durable Change Request artifact | Only readiness classification or gap triage is needed | analysis-agent | completed-contract |
| [checklist](references/checklist.md) | decision-checklist | Auditing intake readiness quickly before routing downstream | The request is blocked by a single missing authority or evidence fact | analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Closure depends on raw-input-to-field mapping, stakeholder authority, source freshness, blocking-question evidence, or proof limits | No evidence conflict, authority, or freshness issue is material | analysis-agent | evidence-record, proof-limit, residual-risk |
| [index](references/index.md) | index | competing change intake compiler references require dependency, conflict, or output-fragment selection | the change intake compiler root or a task-named reference already resolves selection | analysis-agent | reference-selection |
