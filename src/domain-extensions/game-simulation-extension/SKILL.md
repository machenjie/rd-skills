---
name: game-simulation-extension
description: "For analysis/task/review agents: use for game or simulation clocks, physics, replay, authority, or saves; skip ordinary UI animation."
---

# game-simulation-extension

## Role

Focused Layer 3 Domain Skill: `analysis-agent` resolves rules; `task-agent` implements; `review-agent` checks evidence.

Apply simulation-state, clock, replay, and asset-lifecycle constraints to game clients, authoritative workers, and reusable engines.

## When To Use

- Simulation steps, input sampling, physics, pause, catch-up, or frame budgets affect behavior.
- Scene lifecycle, save migration, authority, prediction, rollback, or replay changes persistent or simulated state.

## Do Not Use

- The task is ordinary webpage animation without simulation state or game lifecycle.
- Language or engine names appear without a simulation-specific decision.

## Required Inputs

- Simulation and render clocks, timestep policy, input identity, authoritative state, and target-device budget.
- Physics assumptions, scene/asset ownership, save versions, replay records, and network recovery contract.

## Professional Decision Rules

- Separate render frames from simulation steps and define the mapping from elapsed time to state updates.
- Bound catch-up work while preserving the accepted simulation-time policy.
- Specify input sampling and event identity across prediction, replay, and rollback.
- Keep irreversible external effects outside replayable simulation steps or reconcile them by stable identity.
- Define pause and slow-motion effects on simulation, audio, timers, and network state.
- Preserve scene, asset, and save compatibility through load, unload, migration, and recovery.
- Bound determinism claims by engine, numeric behavior, platform, concurrency, and input sequence.

## High-Value Gotchas

- Frame-rate independence does not prove cross-platform deterministic simulation.
- Replaying a state transition can duplicate achievements, purchases, or other external effects.

## Execution Checklist

1. Identify authoritative state and the clocks that can advance it.
2. Replay stall, pause/resume, reconnect, and save-upgrade sequences.
3. Compare state invariants and frame budgets on the claimed target devices.

## Stop / Escalation Conditions

- Stop deterministic or replay claims when input order, state authority, or execution environment is unspecified.
- Escalate save migration that cannot preserve or recover accepted player state.

## Output Contract

- Return clock/authority rules, replay boundaries, migration behavior, state evidence, and determinism or device limits.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [scene assets and save migration](references/scene-assets-and-save-migration.md) | targeted | scene transitions, asset lifetime, asynchronous loading, save compatibility, or recovery | game changes that preserve scene, artifact, and persistent-state contracts | analysis-agent, task-agent, review-agent | decision-record, failure-decision, validation-plan, proof-limit |
| [simulation clock authority and replay](references/simulation-clock-authority-and-replay.md) | targeted | timestep, input sampling, physics, pause, prediction, rollback, or replay decisions | cosmetic animation without simulation state or authoritative effects | analysis-agent, task-agent, review-agent | decision-record, failure-decision, validation-plan, proof-limit |
