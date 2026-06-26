# Design Pattern Matrix

Load this reference for L3+ structure decisions, multiple pattern candidates, public interfaces/base classes/registries/providers, lifecycle/concurrency/IO/runtime risk, or AI-generated pattern usage without evidence.

| Pattern | Use when | Reject when | Object relationship | Performance risk | Test boundary |
| --- | --- | --- | --- | --- | --- |
| Factory Method | One product family has current variants or construction policy | Simple constructor is enough | Creator owns construction policy | Per-call heavy construction | Constructor contract and variant creation |
| Abstract Factory | Families of related objects must vary together | One family or speculative provider | Factory family plus products | Object graph churn | Family compatibility contract |
| Builder | Construction has many validated steps or immutable aggregate setup | Trivial DTO | Builder owns construction state | Allocation and validation cost | Invalid/complete build behavior |
| Prototype | Cloning configured objects is cheaper or preserves setup | Copy semantics unclear | Source prototype to clone | Stale mutable state | Deep/shallow copy contract |
| Singleton | One lifecycle-owned process resource is required | Hidden global mutable state | Global owner plus consumers | Lock contention, test reset | Lifecycle, sync, teardown tests |
| Object Pool | Measured allocation/connection cost dominates | No profile evidence | Pool owns reusable objects | Contention, stale reset | Profile, reset, leak tests |
| Adapter | External protocol or legacy shape differs from domain contract | Same contract or only naming | Port plus adapter | Hidden IO or mapping cost | Contract plus resource cleanup |
| Facade | Simplify a stable subsystem API | God object or policy dumping ground | Facade to cohesive subsystem | Latency aggregation | Public facade behavior |
| Decorator | Add ordered cross-cutting behavior to same contract | Side effects/order hidden | Wrapper chain | Allocation, latency, order | Contract and ordering tests |
| Proxy | Control remote/lazy/access behavior through same contract | Network IO hidden | Proxy to subject | Hidden latency, timeout | IO timeout and cleanup tests |
| Composite | Tree of uniform parts and whole operations exists | No real tree | Parent/child tree | Traversal cost | Tree invariants and traversal |
| Bridge | Abstraction and implementation axes vary independently | One axis only | Abstraction delegates to implementor | Dispatch and allocation | Each axis contract |
| Strategy | Multiple current algorithms behind stable interface | One implementation | Context plus strategy family | Dispatch/allocation overhead | Shared contract tests |
| State | Object has real state machine with state-specific behavior | Flags are simple | Context plus state objects | Object churn | Transition/invalid path tests |
| Command | Actions need queue, undo, audit, retry, or scheduling | Direct call is enough | Command plus handler | Allocation, idempotency/retry | Command contract and retry tests |
| Observer/PubSub | Event fan-out has independent subscribers | No unsubscribe/lifecycle | Publisher to subscribers | Unbounded fan-out | Unsubscribe, backpressure, isolation |
| Mediator | Peer objects need coordinated interaction | Mediator becomes god object | Peers through mediator | Bottleneck | Interaction contract |
| Chain of Responsibility | Ordered handlers may accept/pass work | Fixed if/else clearer | Linked handlers | Hidden order, latency | Order and fallback tests |
| Template Method | Stable algorithm skeleton with variant hooks | Base class only for reuse | Base skeleton plus subclass hooks | Inheritance cost | Base/subclass contract |
| Visitor | Many operations traverse stable object structure | Breaks encapsulation | Visitor to elements | Traversal and coupling | Operation/element matrix |
| Specification | Reusable predicates combine domain policies | One local predicate | Policy object/value | Allocation and query translation | Predicate and composition tests |
| Null Object | Default no-op preserves contract safely | Hides missing data/error | Concrete no-op implementation | Silent behavior | Explicit no-op contract |
| Repository | Domain needs persistence boundary | Business policy in repository | Domain/service to repository | Storage IO hidden | Persistence contract and transactions |
| Unit of Work | Changes must commit atomically across repositories | One simple write | UoW owns transaction | Long transactions/locks | Commit/rollback tests |
| Dependency Injection | Dependencies vary by environment/test/runtime | Service locator hides deps | Constructor/config ownership | Lifecycle churn | Wiring and contract tests |
| Domain Event | Committed domain change fans out asynchronously | Event before invariant commit | Aggregate emits event | Duplicate/fan-out cost | Outbox/idempotency tests |
| Port/Adapter | Domain must not depend on external protocol | Adapter leaks domain policy | Port contract plus adapter | IO lifecycle | Provider contract tests |
| Anti-Corruption Layer | External model conflicts with domain language | Simple mapping is enough | Translation boundary | Mapping/latency cost | Translation contract |
| Producer-Consumer | Producer and consumer rates differ | Synchronous flow is enough | Queue boundary | Queue growth | Bounded queue tests |
| Worker Pool | Bounded parallel workers process work | Unbounded tasks or no load | Pool owns workers | Saturation | Pool, cancellation tests |
| Pipeline | Staged transforms have independent rates | Stages are trivial | Stage chain | Buffering/backpressure | Stage and end-to-end tests |
| Reactor/Proactor | IO multiplexing or async completion is central | Blocking thread model is simpler | Event loop plus handlers | Event-loop blocking | Non-blocking tests |
| Bounded Fan-out | Async tasks fan out today | Unbounded gather/all | Coordinator plus semaphore | Queue/task growth | Timeout/cancellation tests |
| Backpressure | Downstream cannot accept unlimited work | Caller can fail fast simply | Producer to bounded consumer | Latency and drops | Overload behavior tests |
| Circuit Breaker/Bulkhead | Dependency failure isolation is needed | Local direct call only | Boundary guard | State/metric cost | Reliability gate contract |
