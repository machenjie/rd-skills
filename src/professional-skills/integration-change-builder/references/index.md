# Integration Change Builder Reference Index

Reference type: index
Load when: choosing one local reference for a selected integration risk; record why a plausible reference is skipped.
Do not load when: the root contract or a named reference already identifies the needed material.

| Reference | Load When | Do Not Load When | Depends On | Conflicts With | Professional Depth | Output Fragment |
|---|---|---|---|---|---|---|
| [references/checklist.md](checklist.md) | Closing or reviewing an external integration change needs a compact gate checklist for provider contract, timeout, retry, backoff, circuit breaker, idempotency, webhook signature, replay, sandbox, credentials, reconciliation, tests, and monitoring. | The inline `SKILL.md` quality gate is sufficient for a compact read or a deeper capability reference already covers the same checklist with task-specific detail. | `SKILL.md` mode selection and quality gate. | Loading every capability reference by default; replacing task-specific validation evidence with checklist completion. | extended | Compact checklist coverage, skipped-reference rationale, and validation/evidence gaps. |
| [references/solution-optimality.md](solution-optimality.md) | An outbound call, webhook, provider migration, retry, concurrency, delivery, or reconciliation design has a material failure, latency, cost, or state-consistency tradeoff. | The provider contract and accepted task already determine a bounded adapter change with no material delivery or failure-mode choice. | Provider guarantees and limits, workload, failure consequence, consistency boundary, material alternative, and current evidence. | Generic simplicity or fixed retry/queue/circuit-breaker choices used without timeout, idempotency, replay, and recovery evidence. | extended | Contextual questions on delivery shape, amplification, provider limits, reconciliation, simpler supported paths, and evidence limits. |
