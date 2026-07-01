# Runtime And Contract Coupling

Load this reference when a design pattern can change public contracts, generated clients, lifecycle, IO visibility, concurrency, queues, pools, cancellation, backpressure, teardown, or reliability behavior.

## Coupling Checks

| Coupling | Pattern signals | Required decision evidence | Companion route |
| --- | --- | --- | --- |
| Public contract | Adapter, facade, proxy, repository, strategy interface, base class, SDK export, generated client | API diff, consumer inventory, compatibility test, migration or rollback path | `contract-testing`, `consumer-impact-analysis` |
| Hidden IO | Adapter, proxy, repository, decorator, facade, anti-corruption layer | IO map, timeout/retry/cancellation rule, resource cleanup, observability point | `integration-change-builder`, `reliability-observability-gate` |
| Lifecycle owner | Singleton, pool, observer, worker, client factory, dependency injection container | setup/teardown owner, shutdown path, test reset, error/cancel cleanup | `language-performance-safety`, `quality-test-gate` |
| Concurrency | Worker pool, producer-consumer, pipeline, bounded fan-out, observer fan-out | queue bound, lock scope, backpressure, cancellation, saturation behavior | `concurrency-control`, `async-job-design` |
| Performance | Object pool, proxy, decorator chain, visitor traversal, bridge/strategy dispatch | profile or benchmark, allocation/latency threshold, hot-path budget | `profiling`, `solution-optimality-evaluation` |
| Domain invariant | Repository, command, visitor, adapter, unit of work, domain event | invariant owner, transaction boundary, permission/business rule proof | `domain-impact-modeler`, `business-semantic-control-plane` |

## Approval Rules

- Accept direct code when a pattern would hide IO, lifecycle, or contract behavior that callers need to see.
- Approve proxy, adapter, repository, or facade only when the call site still exposes latency, partial failure, timeout, retry, and cleanup obligations.
- Approve observer, worker, queue, pool, pipeline, or fan-out only with bounded work, cancellation, teardown, and overload evidence.
- Approve public interfaces, base classes, registries, providers, and generated clients only with current consumers or variants and a compatibility path.
- Escalate rather than approve when runtime proof requires profiling, load tests, reliability review, or owner confirmation not available in the current task.
