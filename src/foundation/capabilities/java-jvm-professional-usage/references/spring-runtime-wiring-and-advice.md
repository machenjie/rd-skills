# Spring Runtime Wiring and Advice

**Reference type:** targeted
**Load when:** Spring bean wiring, proxy advice, asynchronous context, rollback, or conditional configuration changes runtime behavior.
**Do not load when:** The change has no Spring-specific wiring or execution-boundary decision.
**Required by:** analysis-agent, task-agent, review-agent
**Required output:** boundary-decision, validation-plan, proof-limit

## Runtime Decisions

- Bind Spring, Spring Boot, JDK, and relevant integration versions to the deployed configuration.
- Trace the actual bean instance and caller path. An annotation on an object created outside the container does not establish advice execution.
- Identify proxy or weaving mode before judging self-invocation. In proxy mode, a call inside the target bypasses its proxy.
- Check the actual proxy type and method visibility. Do not assume every annotated method is interceptable under that configuration.
- Match injected state to bean scope. A singleton retaining request state can outlive the request even when its dependencies are valid beans.
- Resolve qualifiers, conditional beans, configuration properties, and active profiles from effective configuration rather than class names.
- Trace `@Async` through the configured executor and interception path. Assign ownership for rejected work and unobserved task failures.
- Verify which security, tracing, locale, and transaction contexts cross the asynchronous boundary. Thread-local state does not propagate merely through annotation.
- Bind rollback expectations to actual rules, exception types, propagation, and the transaction manager. A caught exception may change the observed outcome.
- Check after-commit work against the real commit result. Successful method return is not evidence that a later resource commit succeeded.
- Choose a test context that includes the relevant advice, transaction manager, and conditional wiring. A narrow test slice may exclude them.

## Distinguishing Checks

| Boundary | Compare |
| --- | --- |
| Advice reachability | External call through the injected proxy versus self-invocation |
| Rollback configuration | Runtime exception and checked exception under the actual rollback rules |
| Async context | Caller state, worker state, cancellation, rejection, and failure observation |
| Scope lifetime | Consecutive requests and concurrent requests through the same singleton |
| Conditional wiring | Intended production condition and a condition that selects a different bean |
| Test fidelity | Slice behavior versus the smallest context that exercises the deployed boundary |

Return the resolved bean/call graph, transaction outcome, asynchronous ownership, and omitted deployment conditions.
Reuse generic JVM resource and transaction methods for their underlying rules.

## Version Sources

- Verify interception against [Spring declarative transactions](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html).
- Treat proxy-mode self-invocation limits separately from AspectJ weaving and version-specific framework configuration.
