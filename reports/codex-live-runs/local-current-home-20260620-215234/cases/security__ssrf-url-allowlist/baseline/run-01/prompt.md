You are Codex running a local code-generation benchmark.

Solve the requested task in the candidate repository. Prefer small,
maintainable changes, reuse existing code where it fits, and run the relevant
tests. Do not rely on hidden external files, personal archives, or network-only
resources.


## Benchmark Task

You are working inside an isolated copy of a starter repository.

Read the task below, modify only the candidate repository, and leave a concise
final answer that includes:

- files changed;
- validation commands run and their result;
- reuse or placement evidence when relevant;
- residual risk.

# Benchmark Prompt

## Task

Implement a focused change to add server side URL fetch validation with an explicit allowlist and safe network denial behavior.

## Context

The starter repo represents a backend endpoint fetches metadata from user supplied URLs for preview generation. In its initial state, the starter behavior trusts parsed hostnames and does not reject private network targets. The implementation should be small enough to review but complete enough to prove the professional quality target.

## Requirements

- Allowed HTTPS hosts can be fetched with bounded timeout and response size.
- Loopback, link local, private ranges, and metadata service addresses are rejected.
- Redirect chains are revalidated before any outbound request continues.
- Denied requests return client safe errors without leaking internal network details.

## Constraints

- Validation canonicalizes scheme, host, port, and resolved addresses before fetch.
- Network policy is centralized and covered by unit and integration tests.
- Error handling fails closed for parse, DNS, redirect, and timeout failures.
- Preserve the existing public contract unless the prompt explicitly asks for a compatible addition.
- Do not replace the benchmark with documentation-only output.

## Deliverables

- Source changes in the starter repo that implement the requested behavior.
- Tests or executable checks that prove the required behavior and denial paths.
- A short implementation note describing important tradeoffs and residual risk.

## Completion Evidence

- `bash setup.sh`
- `bash ../test-suite/run.sh`
- `bash ../security-checks/run.sh`
- Review evidence that no automatic failure condition applies.

