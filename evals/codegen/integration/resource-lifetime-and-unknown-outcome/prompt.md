# Benchmark Prompt

## Task

Complete the bounded fixture adapters in `subject.py` for deterministic validation. This is test infrastructure, not product implementation or a new runtime.

## Context

The accepted contracts are fixed below. Candidate functions consume raw records or controlled collaborators; assertions derive expected behavior independently.

## Requirements

- `stream(open_resource)` opens lazily during consumption, yields each read until `None`, and closes once after completion, cancellation, or an exception.
- `effect_scope(subscribe)` subscribes once and returns an idempotent cleanup callable. Each new scope has its own resource.
- `cached_value(cache, tenant, locale, entity, load)` isolates these three identity dimensions and reuses an existing matching value.
- `recover_timeout(provider, operation_id)` calls `lookup`. Return completed results; return `None` for pending; execute only after an explicit absent result; reject unknown outcomes.
- The fixture provider defines absent as no prior effect and `execute` as accepting this operation identity. These supplied semantics are not universal provider guarantees.
- `activate(storage)` persists schema-2 visit counts. Migrate schema 1's `counter` to schema 2's `visits`, then increment; reject unsupported schemas.
- `unload(storage)` preserves persistent data. `uninstall(storage, retain_data)` erases the fixture namespace only when the supplied policy is false.
- `message_allowed(message, expected_origin, expected_context)` requires both supplied identity dimensions to match.
- `transaction_values(transaction, build_query, max_rows)` constructs and evaluates the supplied lazy query inside the context manager, returns materialized values, and closes the transaction on success or error. Reject a negative/non-integer row bound or a result exceeding it. Construction alone does not execute a read; later serialization must not issue a query.
- `mcp_call(contract, discovery, invocation, token, grants, send)` uses this fixture's selected version only when it belongs to each supplied client, server, and SDK support set. This is the fixture adapter's compatibility policy, not a universal MCP SDK rule. Reject disagreement before dispatch.
- Bind the invocation's name and complete `input_schema` to discovery. The fixture schema maps required field names to `integer`, finite `number`, or `string`; reject missing/extra fields, wrong types, and booleans used as numbers. These flat schemas are not a general JSON Schema implementation.
- Require `token.aud` to equal the receiving `contract.resource` and a trusted `(resource, tool name, contract.action)` grant. Discovery annotations, including `readOnlyHint`, cannot supply that grant or change the trusted action. Audience and permission failures raise `PermissionError` before `send`.
- This fixture accepts request IDs of exact integer or string type; booleans, floating-point numbers, null, and other values raise `ValueError` before dispatch. Its JSON-RPC envelope has version `2.0`, an ID with the same type and value as the invocation, and exactly one `error` or `result`. The restricted ID domain is a fixture policy, not a claim that all JSON-RPC numbers must be integers. An error has integer `code` and string `message`; return `{"kind":"protocol-error","code":code}`. A successful result has boolean `isError: false` and `structuredContent` matching the discovered output schema; return `{"kind":"success","data":structuredContent}`. A business failure has `isError: true` and one text content item; return `{"kind":"business-error","message":text}`. Reject malformed envelopes/results with `ValueError`. These are selected fixture shapes, not every legal MCP response shape.
- `render_hydration(server, client_renders)` compares the server snapshot with the first client snapshot, even if a later effect agrees with the server. Snapshots contain integer UTC epoch seconds, an integer fixed timezone offset in minutes within -840..840, and locale `en` or `fr`. Render `en:YYYY-MM-DD HH:MM` or `fr:DD/MM/YYYY HH:MM` and return `server_markup`, `initial_markup`, and `matches`. No real clock, platform locale, IANA timezone, or framework renderer is consulted.
- `serialize_transfer(value)` copies only null, booleans, integers, finite floats, strings, lists, and string-keyed dictionaries. Shared values lose object identity; cycles, callables, live resources, and other objects raise `ValueError` without invoking them. This fixture declares a JSON-shaped boundary with no additional codecs.
- `server_action(principal, request, authorize, perform)` validates a positive integer `amount`, always calls the authoritative `authorize(principal, resource)`, and invokes `perform(resource, amount)` only when allowed. A page visit or a `page_authorized` request hint cannot authorize the action. Reject invalid input with `ValueError` and denied authority with `PermissionError`.

## Constraints

Use Python standard-library code without network, real clocks, or external services. Do not edit assertions or add expected-answer fields to input records.

## Deliverables

Implement the callable interfaces and explain the unproved boundaries. Preserve the distinction between supplied policy and universal behavior.

## Completion Evidence

Run passing-candidate assertions and reject the incomplete starter and each single-mechanism faulty control. These local traces do not run React, ASGI, Django, an MCP client/server/SDK, browser extensions, IDE hosts, media devices, or external providers. They do not establish actual database isolation, protocol negotiation, browser hydration, or deployed authorization.
