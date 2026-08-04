# Go Lifetime And Error Contract

This contract focuses Go review on ownership and runtime semantics that can silently change across contexts, goroutines, channels, interfaces, resources, and toolchain versions.

## Go Decision Matrix

| Go facet | Facts to establish | Accident signal |
| --- | --- | --- |
| Context lineage | Operation owner, parent deadline and cause, values that may cross the boundary, derived cancellation, external calls, and public-signature compatibility | Mid-path background/TODO context or stored request context disconnects cancellation and cleanup |
| Goroutine lifetime | Start owner, completion observation, cancellation, work bound, error and partial-result policy, and shutdown | Work survives its owner, blocks after return, or loses the first material failure |
| Channel contract | Sender and receiver set, close authority, buffering/backpressure, blocked-path cancellation, and closed/nil behavior | A participant closes without proving no future send, or an unobserved send/receive cannot terminate |
| Shared state | Publication edge, mutex/atomic/channel owner, copy behavior, map/slice aliasing, closure capture, and race-relevant schedule | State is published without synchronization or a live synchronization value is copied |
| Error and interface | Wrapped cause, caller classification, cancellation/deadline identity, typed error or sentinel contract, typed-nil interface, and panic/recover boundary | Formatting, comparison by text, typed nil, or recovery changes retry, status, exit, cancellation, or invariant failure into success |
| Resource lifecycle | Acquisition and cleanup owner for body, rows, file, timer, ticker, lock, cancel function, subprocess, and loop iteration | Defer accumulates in a loop, cleanup misses an exit, or reuse is lost because the resource is not closed correctly |
| Interface and version | Current consumer or independent boundary, zero value, option defaults, Go directive/toolchain, range capture, build tags, GOOS/GOARCH, and generated source | A speculative interface or remembered version rule changes API or platform behavior |
| Module and proof boundary | Standard/approved alternatives, capability gap, package route, affected tags/platforms, focused tests, race/vet evidence, and not-run limits | A module or concurrency claim is approved from one default-platform compile or test |

## Decision Limits

- Use the repository Go directive, toolchain, public contracts, and platform matrix as authority; generic Go guidance does not override a fixed compatibility boundary.
- A structured goroutine owner may use repository mechanisms rather than a prescribed helper, provided lifetime, bound, cancellation, and failure observation stay explicit.
- Race, vet, and focused tests establish exercised code, schedules, tags, and platforms; package, build, performance, and broader concurrency conclusions remain with their specialist owners.
