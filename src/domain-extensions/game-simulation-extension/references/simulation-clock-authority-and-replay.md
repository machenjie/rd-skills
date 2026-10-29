# Simulation Clock, Authority, and Replay

Load for timestep, input sampling, physics, pause, prediction, rollback, or replay decisions.
Skip cosmetic animation without simulation state or authoritative effects.

## Decision Rules

- Separate render time, simulation time, wall time, and network time where each drives behavior.
- Define fixed-step or variable-step semantics from the simulation contract, not the display refresh rate.
- Bound catch-up work after a stall and state what happens to accumulated elapsed time.
- Sample and assign input to simulation steps with stable ordering and identity.
- Validate physics and collision assumptions against movement scale and the chosen integration step.
- Define which clocks pause or scale during pause and slow motion.
- Keep authoritative simulation state distinct from predicted or interpolated presentation.
- Bind rollback and replay to retained inputs, state snapshots, and compatible simulation versions.
- Deduplicate events that could repeat across rollback, reconnect, or replay.
- Place irreversible external effects behind their existing confirmation or reconciliation boundary.
- Compare deterministic claims only within the declared engine, numeric, platform, and scheduling scope.
- Measure frame budgets on target devices with representative simulation and rendering load.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Long stall creates accumulated steps | Catch-up remains bounded and preserves the declared time policy |
| Pause and resume surround timed actions | Only the designated clocks advance |
| Late input triggers rollback | Recomputed state and external effect identity remain consistent |
| Reconnect replays previously accepted events | Authoritative state avoids duplicate rewards or actions |
| Replay runs on another execution environment | Any determinism claim states its supported scope |

## Proof Limits

- A replay fixture proves the exercised sequence, not determinism across every compiler, device, or physics configuration.
