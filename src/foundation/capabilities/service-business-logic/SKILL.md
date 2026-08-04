---
name: service-business-logic
description: "`analysis-agent`/`task-agent`: use when a use case coordinates authorization, domain work, transactions, or external effects; skip transport, storage, and rule-only work."
---

# service-business-logic

## Registry Trigger

**Use when**

- place application use-case orchestration authorization transaction domain invocation repository coordination and external effects

**Do not use when**

- work changes transport mapping persistence mechanics or domain rules without an application orchestration decision

## Skill Role

Implement application-level sequencing within one use case through authorization context, commit boundaries, domain invocation, persistence coordination, and external-effect handoff. Exclude domain rules, storage behavior, transport, and translation.

## High-Value Rules

- Name the actor, intent, inputs, domain authority, terminal results, and effect sequence. Split orchestration when policy, transaction, lifecycle, or recovery authority differs; method or class shape alone is not a boundary.
- Establish authorization scope before sensitive retrieval, or use a scoped lookup whose absence semantics do not disclose protected existence. Permission-model design belongs to `permission-boundary-modeling`.
- Invoke the domain authority for invariants, transitions, and calculations. An application precheck can improve flow but cannot become the last enforceable guard.
- Make commit ownership and participating writes explicit. When downstream work depends on committed source state, coordinate the durable handoff with that state or name the crash gap and reconciliation owner.
- Sequence provider, network, file, queue, cache, and notification effects against commit. Define timeout, cancellation, unknown outcome, retry identity, duplicate behavior, compensation, and terminal ownership where reachable.
- Preserve permission, absence, conflict, partial, timeout, duplicate, cancellation, dependency, and terminal distinctions while translating repository, domain, and provider outcomes into the use-case contract.
- For reads, name visibility, consistency source, bounds, ordering, and any intentional effect. Lazy state or an unowned write crossing the service result is a boundary defect.

## Anti-Patterns

- Creating a service/repository/controller chain by ceremony, or grouping unrelated workflows behind a broad noun service.
- Reimplementing a domain invariant in orchestration because one caller needs an early check.
- Hiding commit, event publication, provider I/O, retry, or compensation inside a helper whose failure cannot be represented by the use case.
- Treating a framework annotation, mock happy path, or neighboring service shape as proof of ownership or effect order.

## Stop Conditions

- Escalate when authorization order, commit ownership, cross-boundary consistency, unknown effect outcome, retry identity, partial completion, or irreversible provider state lacks an accountable recovery decision.

## Output Contract

- Return an application-orchestration contract: state actor intent, domain authority, transaction/effect order, typed outcomes, recovery, evidence limits, and consistency owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Use-case ownership authorization order commit and effect sequencing or workflow durability leaves competing placements | The current application boundary and specialist owners resolve the sequence | task-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Orchestration crosses authorization domain transaction persistence external-effect or recovery boundaries | Local sequencing preserves the established actor commit effect and failure contract | task-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Authorization order domain delegation commit handoff failure translation or recovery claims need fresh proof | Current callers and scoped sequence and failure evidence close each changed orchestration claim | task-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
