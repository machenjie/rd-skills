# ASGI Request Resource Lifecycle

**Reference type:** targeted
**Load when:** ASGI dependencies, streaming responses, background work, or lifespan resources cross a request boundary.
**Do not load when:** The change has no ASGI resource-lifetime or response-execution decision.
**Required by:** analysis-agent, task-agent, review-agent
**Required output:** boundary-decision, validation-plan, proof-limit

## Lifetime Decisions

- Bind the ASGI server, framework, and relevant dependency versions. Dependency cleanup timing is framework behavior, not a timeless ASGI guarantee.
- Draw acquisition, handler return, response iteration, disconnect, background work, and cleanup on one timeline.
- Keep streaming resources alive until their last read. Handler return does not mean response iteration has finished.
- Select FastAPI dependency scope from the consumer lifetime. A function-scoped resource cannot support later streaming reads after its cleanup.
- Give background work its own resource scope when it outlives the request. Pass stable identifiers instead of request-bound sessions or cursors.
- Bind application resources to actual lifespan startup and shutdown. Repeated startup, failed startup, and partial shutdown need valid ownership.
- Observe disconnect and cancellation at the actual server/framework boundary. Close acquired resources without disguising partial delivery as successful completion.
- Preserve the original operation failure when cleanup also fails.
- Report whether response headers or body bytes had already been sent when the operation failed.
- Exercise test-client lifespan explicitly. Constructing a client alone may not enter the application's lifespan context.
- Separate in-process client evidence from real server behavior. Buffering, disconnect propagation, middleware, and worker shutdown may differ.

## Version-Specific FastAPI Examples

| Version or scope | Resource-lifetime consequence |
| --- | --- |
| 0.106.0 through 0.117.x | Yield-dependency cleanup can precede sending a streaming response |
| 0.118.0 change | Default cleanup returns to after response sending |
| 0.121.0+ `scope="function"` | Cleanup occurs after the path function, before response sending |
| 0.121.0+ default `scope="request"` | Cleanup follows response sending |

Verify the target release before applying these examples.

## Distinguishing Checks

| Scenario | Observable check |
| --- | --- |
| Stream several chunks from a dependency-owned resource | Reads finish before the matching cleanup |
| Disconnect between chunks | The resource closes and incomplete delivery remains visible |
| Background work runs after request cleanup | It acquires its own resources from stable input |
| Enter and exit the test client's context | Lifespan startup and shutdown actually execute |

Return the execution timeline, scope choice, cleanup evidence, and server conditions not exercised.

## Version Sources

- Check [FastAPI dependency lifetime](https://fastapi.tiangolo.com/advanced/advanced-dependencies/) and [Starlette lifespan testing](https://starlette.dev/lifespan/).
