---
name: go-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use when Go context, goroutine, channel, error, interface, or resource semantics affect behavior; skip generic or non-Go work."
---

# go-professional-usage

## Registry Trigger

**Use when**

- Go code changes context lineage, goroutine or channel lifetime, shared state, error identity, interface behavior, timers, or resource cleanup.
- Toolchain-version semantics, build tags, platform variants, or generated boundaries can change the meaning of an otherwise local Go edit.

**Do not use when**

- The open question is generic language style, package selection, build mechanics, performance tuning, or test portfolio without a Go-specific semantic decision.
- No Go source, generated Go surface, or Go runtime obligation changes.

## Skill Role

Protect Go context lineage, goroutine and channel ownership, memory-model-sensitive behavior, error identity, interface nil semantics, and resource lifecycle.

## High-Value Rules

- Pass context from the owning operation while preserving deadline, cancellation cause, and required values.
- Give each goroutine owned completion, cancellation, bounded admission, failure observation, and shutdown.
- Name channel senders, receivers, close authority, backpressure intent, and cancellation unblocking.
- Define shared-state access and synchronization according to the Go memory model.
- Preserve error identity, cancellation causes, and goroutine-local panic boundaries.
- Define cleanup ownership for rows, bodies, timers, tickers, locks, and cancel functions within their bounded lifetime.
- Define interfaces at current consumers with explicit zero-value semantics.
- Verify range capture, build tags, APIs, and platform assumptions against the repository toolchain.

## Anti-Patterns

- A request context is stored beyond its operation, discarded mid-path, or replaced so cancellation no longer reaches external work.
- A goroutine or channel can wait after its owner returns, block on an unobserved send, close from the wrong side, or lose the first material error.
- Error text, a fresh wrapper, or a typed-nil interface changes retry, status, exit-code, or cancellation behavior.
- Cleanup is deferred inside an unbounded loop or a response body, timer, ticker, subprocess, or worker outlives its owner.

## Stop Conditions

- Route lock ordering, atomicity, races, and cross-owner coordination to `concurrency-control`.
- Route hot paths, allocation, blocking, and garbage collection to `language-performance-safety`.
- Route modules, builds, tests, and public contracts to their specialist owners.

## Output Contract

- Go semantic decision with inspected scope, context lineage, goroutine and channel ownership, memory-model boundary, error identity, interface and zero-value behavior, resource lifecycle, version assumptions, evidence and findings, proof limits, residual risk, and specialist routes

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | A Go change affects context goroutine channel shared-state error interface resource or toolchain-version semantics | The Go edit preserves these runtime obligations and follows established repository behavior | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
