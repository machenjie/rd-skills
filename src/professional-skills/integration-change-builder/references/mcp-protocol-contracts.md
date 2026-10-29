# MCP Protocol Contracts

**Reference type:** targeted
**Load when:** An MCP client, server, or SDK boundary changes negotiation, tool schemas, results, authorization, or operation outcomes.
**Do not load when:** The task has no MCP protocol boundary or only renames ordinary internal functions.
**Required by:** analysis-agent, task-agent
**Required output:** boundary-decision, failure-decision, validation-plan, proof-limit

## Contract Decisions

- Pin the client, server, SDK, transport, and supported specification versions. Verify their compatible intersection before using a protocol feature.
- Derive initialization, session, capability negotiation, and reconnect behavior from that selected specification and transport.
- Bind invocation to the discovered tool schema. Refresh or reject cached assumptions when the server changes the schema.
- Validate the actual result shape and advertised output contract. Distinguish malformed output from a valid business failure.
- Separate JSON-RPC protocol errors from tool execution errors. Under the 2025-11-25 tools contract, tool failures can use `isError` results.
- Preserve resource identifiers, content types, and access semantics when consuming resources or tool results. Textual resemblance does not establish equivalent contracts.
- Treat annotations such as read-only or idempotent as hints. Establish the operation's actual authority and effects before relying on them.
- Bind an access token's audience to the receiving MCP server. An audience for another resource leaves this server unauthorized.
- Use separately issued upstream credentials where required. Passing the received client token through to another service violates the cited authorization contract.
- Associate cancellation with the identified request and supported capability. Cancellation can race with successful completion.
- Treat timeout or disconnect after dispatch as an unknown operation outcome until the business contract resolves it.
- Query operation status or use established idempotency semantics before repeating a consequential operation. A repeated non-idempotent call can create another external effect.

## Failure Matrix

| Scenario | Required distinction |
| --- | --- |
| Client or SDK lacks the selected version or capability | Unsupported contract versus a failed business operation |
| Cached tool schema differs from discovery | Refresh/revalidate versus invoking with stale arguments |
| Token has another resource's audience | Authentication material exists but does not authorize this server |
| Tool advertises read-only but performs writes | Annotation is not proof of permission or harmlessness |
| Tool returns a valid `isError` result | Business failure versus JSON-RPC parsing or protocol failure |
| Caller times out after the external operation commits | Reconcile the completed result instead of blindly repeating it |

Return the negotiated contract, error mapping, credential boundary, and retry decision with unresolved external outcomes.
Protocol fixtures prove their modeled contracts; they do not prove arbitrary provider behavior.

## Version Sources

- Examples use MCP 2025-11-25: [tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools), [authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization), and [cancellation](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/cancellation).
- Check the target specification before applying initialization, transport, session, or authorization details.
