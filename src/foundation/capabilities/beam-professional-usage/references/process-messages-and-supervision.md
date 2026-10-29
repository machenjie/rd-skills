# BEAM Processes, Messages, and Supervision

Load for BEAM link/monitor choices, mailbox pressure, restart dependencies, or distributed result uncertainty.
Skip service changes that preserve these process contracts.

## Decision Rules

- Identify the process owning each state transition and the caller observing its completion.
- Choose links when coupled exit behavior is intended.
- Use monitors for observation without that exit coupling.
- Check exit trapping and monitor cleanup against the actual process protocol.
- Match replies by request reference rather than message shape alone.
- Handle late replies after timeout, including their effect on later receives.
- Bound admission when mailbox growth can exceed processing capacity.
- Inspect selective receive patterns for unmatched-message accumulation.
- Recover process identity after restart instead of reusing a stale PID.
- Choose supervision strategy from child dependencies and reconstructible state.
- Test restart intensity exhaustion and the resulting parent failure path.
- Reconcile external effects separately from process restart and node reconnection.
- Reuse operation identity when an unknown outcome can otherwise cause duplicate effects.

## Failure Probes

| Probe | Required distinction |
|---|---|
| Worker crashes before replying | Caller observes failure through its selected link or monitor |
| Reply arrives after timeout | Old reply cannot satisfy a new operation |
| Unrelated messages accumulate | Admission or receive design addresses mailbox growth |
| Child restarts | Callers refresh identity and required state |
| Repeated crashes exceed restart limits | Parent failure or recovery is explicit |
| Node disconnects after an external write | Outcome remains unknown until reconciled |

## Source Limits

- A supervisor restores process availability; it does not prove external effect rollback.

## Sources

- [Elixir processes](https://elixir.hexdocs.pm/processes.html)
- [Elixir supervisors](https://elixir.hexdocs.pm/Supervisor.html)
- [Erlang processes and monitors](https://www.erlang.org/doc/system/ref_man_processes.html)
