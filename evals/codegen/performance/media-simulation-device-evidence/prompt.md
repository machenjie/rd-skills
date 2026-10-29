# Benchmark Prompt

## Task

Implement three independent recorded-evidence validators in `subject.py`. This is a deterministic validation fixture. It is not a media, game, or device runtime.

## Context

Input records describe observed presentations, simulation steps, and device events. Assertions derive timing, conservation, identity, and ordering independently. Policies are supplied by each fixture.

## Requirements

- `media_evidence(record, policy)` returns failures, normalized `pts`, normalized `dts`, and presented frame IDs. A timestamp is `[ticks, timebase_numerator, timebase_denominator]`. Use exact rational arithmetic.
- Keep decode order separate from presentation time. Check required tracks and recorded coverage. Require actual presentation records; upload exit or connection success is insufficient.
- Compare audio and video presentation time with the supplied inclusive tolerance. The supplied `drop` policy forbids presenting frames older than `max_lateness`; `keep` permits them.
- Seek evidence names decoded and presented frame IDs. Decode from a keyframe at or before the target. Keep decode timestamps ordered. Present only decoded frames at or after the target. The first presented position must meet the supplied seek tolerance.
- Track starts and stops must pair. EOF, cancellation, and failure leave no live track. An open recording may retain tracks.
- `simulation_evidence(record, policy)` derives fixed step counts from render deltas. Pause freezes accumulation and stepping. Resume uses retained backlog. Apply the supplied catch-up cap.
- Retain backlog or explicitly discard excess whole steps under the supplied policy. Report steps, active time, leftover time, and discarded time. Recorded step durations must use the fixed step, not render delta.
- The fixture save schema migrates version 1 counter to version 2 score. Unknown versions cannot prove migration. Deduplicate identical event IDs; reject conflicting identity, invalid tick order, duplicate effects, or mismatched score.
- Compare replay effects and score only within the declared environment and seed. A mismatch there diverges. Different environments or seeds are out of scope for a deterministic claim.
- `device_evidence(record, required)` validates a finite trace. Submission creates pending work. A signal records completion; completed wait records the host dependency. Host reads additionally need explicit visibility. Reuse needs completion and a wait, but not read visibility.
- New work on an owned resource declares its predecessor fence. Device loss advances the epoch and invalidates old resources, fences, and pipelines.
- Pair shader, asset, layout, interface, compile options, and device epoch. Reload changes required identity. A broad interface match cannot validate stale cache contents.

## Constraints

All effects are records. Use no network, real clock, GPU, codec, renderer, or general state engine. These traces do not establish actual playback, device API equivalence, GPU visibility semantics, physical simulation accuracy, or cross-environment determinism.

## Deliverables

Implement the three callable interfaces. Keep supplied policies distinct from universal thresholds. Report concrete failure dimensions and proof limits.

## Completion Evidence

Run the passing candidate and reject the incomplete starter plus focused time, pause, completion, and artifact-identity controls. Exercise legitimate traces, boundary values, missing evidence, and forbidden effects.
