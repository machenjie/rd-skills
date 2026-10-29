# Review Rubric

## Passing Standard

The fixture adapters satisfy their accepted contracts under direct function and trace assertions.

## Scoring

Assess resource and transaction event order, selected protocol/schema/audience/effect authority, distinct error outcomes, first-render input agreement, serialization boundaries, server-action authorization, cache identity, outcome reconciliation, persistent migration, and host message identity.

## Automatic Failure Conditions

Fail premature release, deferred reads beyond the transaction, stale tool-schema use, mismatched token audience, permission derived from a read-only hint, business failure reported as success, later effects hiding hydration mismatch, unsupported transfer values, and server actions relying on page authorization. Repeating a completed operation or crossing tenant cache boundaries also fails.

## Reviewer Notes

These local traces do not run React, Django, ASGI, an MCP client/server/SDK, browser extensions, IDE hosts, media devices, or external providers. The selected version/SDK sets, closed message shapes, fixed-offset render formats, and JSON-shaped transfer policy belong to this fixture; they are not universal platform rules. Static definitions and starter rejection do not replace a passing-candidate run.
