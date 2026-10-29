---
name: realtime-media-extension
description: "For analysis/task/review agents: use for media timing, codec, playback, tracks, or real-time transport; skip ordinary uploads and generic connections."
---

# realtime-media-extension

## Role

Apply timing, playback, and media-resource constraints to clients, media workers, and reusable media components.

## When To Use

- Capture, encode, container, transport, decode, playback, or seek behavior changes.
- Clock mapping, jitter, latency, track changes, or transcoding resources determine acceptance.

## Do Not Use

- The task only uploads opaque files or establishes a connection without media behavior.
- A media filename appears without a codec, timeline, playback, or resource decision.

## Required Inputs

- Media formats, codecs, containers, timestamps/timebases, track identities, and pipeline stages.
- Latency/quality policy, target devices, transport behavior, queue limits, and playback acceptance.

## Professional Decision Rules

- Trace timestamp and timebase conversions across capture, processing, transport, and playback.
- Keep audio/video synchronization tied to the chosen clock and discontinuity policy.
- Bound buffering and define when stale frames are dropped rather than delivered late.
- Separate transport success from decodability, playback, seek, and content completeness.
- Assign track and device resources explicit stop, replacement, and reconnect behavior.
- Validate bitrate adaptation against quality, latency, loss, and queue evidence.
- Bound transcoding memory, work, temporary storage, and partial-output behavior.

## High-Value Gotchas

- A successful transcode exit can leave unreadable, truncated, or unseekable media.
- A reconnect can revive stale tracks or reset timestamps without an explicit discontinuity.

## Execution Checklist

1. Locate the changed pipeline stage and its timing/resource contract.
2. Exercise jitter, discontinuity, track replacement, cancellation, and partial output as applicable.
3. Inspect actual playback, synchronization, and seek on the supported targets.

## Stop / Escalation Conditions

- Stop acceptance when timebase, synchronization authority, output completeness, or the latency/drop policy is unresolved.
- Report unavailable target playback or device evidence as a concrete proof limit.

## Output Contract

- Return pipeline and clock decisions, queue/drop behavior, track recovery, playable-output evidence, and target limitations.

## Targeted References

- No task-local Reference is indexed for this Skill.
