# Review Rubric

## Passing Standard

The fixture adapters satisfy their accepted contracts under direct function and trace assertions.

## Scoring

Assess read, cancel, normal completion, error cleanup, repeated effect cleanup, cache identity, outcome reconciliation, persistent migration, and host message identity.

## Automatic Failure Conditions

Closing the resource before the stream consumer finishes. Repeating a completed operation after timeout or sharing cached values across tenants.

## Reviewer Notes

These local traces do not run React, ASGI, MCP, browser extensions, IDE hosts, media devices, or external providers. Static definitions and starter rejection do not replace a passing-candidate run.
