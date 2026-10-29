---
name: beam-professional-usage
description: "For analysis/task/review agents: use for Elixir/Erlang process, mailbox, supervision, or distributed-call semantics; skip generic service changes."
---

# beam-professional-usage

## Registry Trigger

**Use when**

- BEAM processes, messages, links, monitors, supervisors, or distributed nodes affect completion and recovery.
- A restart or timeout can leave queued messages, stale process identity, or an unknown external effect.

**Do not use when**

- Elixir or Erlang appears only in dependency metadata or unchanged source.
- Generic service logic changes without a BEAM process or runtime boundary.

## Skill Role

Protect process identity, message correlation, supervision semantics, and distributed result uncertainty.

## High-Value Rules

- Give process state and external effects separate recovery contracts.
- Classify linked exit propagation separately from monitor notifications.
- Map replies to operation references and current process generations.
- Bound mailbox growth and inspect selective receives that leave unrelated messages behind.
- Choose supervision strategy and restart limits from actual child dependencies.
- Treat timeout and node disconnection as possible unknown outcomes.
- Verify cancellation, retry, and deduplication at the external effect owner.
- Validate OTP behavior and version assumptions against the deployed runtime.

## Anti-Patterns

- Supervisor restart is treated as undoing a payment, write, or other external effect.
- A cached PID remains authoritative after a child restarts.
- Repeated unmatched messages grow a mailbox while expected replies still arrive.
- Node disconnection is interpreted as proof that a command never executed.

## Stop Conditions

- Resolve process authority, delivery outcome, and supervision policy before retrying effects or accepting recovery.

## Output Contract

- Return mailbox, failure, restart, identity, and distributed-outcome decisions with sequence evidence.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [process messages and supervision](references/process-messages-and-supervision.md) | targeted | BEAM link/monitor choices, mailbox pressure, restart dependencies, or distributed result uncertainty | service changes that preserve these process contracts | analysis-agent, task-agent, review-agent | decision-record, failure-decision, validation-plan |
