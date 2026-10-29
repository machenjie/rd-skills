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

## Constraints

Use Python standard-library code without network, real clocks, or external services. Do not edit assertions or add expected-answer fields to input records.

## Deliverables

Implement the callable interfaces and explain the unproved boundaries. Preserve the distinction between supplied policy and universal behavior.

## Completion Evidence

Run passing-candidate assertions and reject the incomplete starter and the single-mechanism faulty control. These local traces do not run React, ASGI, MCP, browser extensions, IDE hosts, media devices, or external providers.
