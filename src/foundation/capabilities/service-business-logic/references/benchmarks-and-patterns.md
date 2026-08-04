# Service Orchestration Decision Patterns

These patterns compare application use-case ownership, authorization order, consistency, external effects, failure translation, reads, and long-running workflow sequencing.

## Placement And Sequencing Matrix

| Orchestration pressure | Application decision | Specialist handoff |
| --- | --- | --- |
| Use-case boundary | actor, intent, accepted input, terminal results, and one accountable sequence | rule truth or lifecycle semantics to `domain-logic-implementation` |
| Authorization order | identity and scope before sensitive retrieval, or a non-disclosing scoped lookup | permission model to `permission-boundary-modeling` |
| Consistency | commit owner, participating writes, rollback behavior, and durable handoff | isolation or multi-write atomicity to `transaction-consistency` |
| External effect | position relative to commit, unknown outcome, duplicate behavior, and recovery | full effect path to `data-side-effect-flow-tracing`; replay to `idempotency-retry-design` |
| Failure translation | stable use-case outcomes while dependency details remain behind their owner | cross-boundary taxonomy to `failure-contract-design` |
| Read use case | visibility, consistency source, bounds, ordering, and named intentional effects | storage semantics to `repository-persistence` |
| Long workflow | durable step, status, cancellation, compensation, and terminal owner | scheduler and worker lifecycle to `async-job-design` |

## Crash And Partial-Completion Questions

- What durable fact exists if the process stops before commit, after commit, before effect dispatch, or after the provider acts but before the result is recorded?
- Which actor can retry, and what operation identity prevents a second business effect or cross-principal result reuse?
- Which failures roll back local state, which require compensation or reconciliation, and which end in an operator-visible terminal state?
- Which old and new service versions can observe in-flight work during rollout or recovery?

## Placement Boundary

Keep transport parsing in `controller-api-implementation`, rule authority in `domain-logic-implementation`, storage behavior in `repository-persistence`, model translation in `model-boundary-mapping`, and the complete data/effect path in `data-side-effect-flow-tracing`.
