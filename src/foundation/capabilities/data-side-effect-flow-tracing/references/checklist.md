# Data Side-Effect Flow Tracing Checklist

- Name the changed flow entry point, trust boundary, validation boundary, policy decision, mutation command, and terminal state.
- For the current changed entry point, inventory reachable side effects across persistence, cache, event/queue, search/index, external IO, file/storage IO, time/random/env read, logging, metrics, tracing, timer, lock, process signal, retry, and compensation.
- For each side effect, record owner boundary, caller, callee, order, durable/transient status, duplicate behavior, failure behavior, observability, and validation status.
- Confirm pure decisions, mappers, getters, validators, serializers, schema converters, policies, and domain objects do not hide external mutation or IO unless local framework convention is explicit and tested.
- State transaction boundary, commit point, outbox or publish-after-commit decision, rollback behavior, and consumer visibility.
- State cache source of truth, key dimensions, invalidation/write-through order, stale tolerance, and failure behavior.
- Bound external/file IO with timeout, cancellation, retry/no-retry stance, idempotency, cleanup, reconciliation, and operator-visible failure.
- Make nondeterministic reads injectable or centralized; name default, test override, replay/audit impact, and config/flag handoff.
- Scan same-pattern siblings: mappers, validators, policies, repositories, adapters, jobs, decorators, generated wrappers, and framework hooks.
- Map side-effect assertions to their verification evidence: tests, validators, review artifacts, report paths, exit codes, freshness, skipped edges, residual risk, and next owner.
