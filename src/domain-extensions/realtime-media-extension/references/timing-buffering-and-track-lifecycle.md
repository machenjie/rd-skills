# Media Timing, Buffering, and Track Lifecycle

Load for live capture, clock mapping, jitter, bitrate adaptation, tracks, or reconnect behavior.
Skip opaque file transfer and connections without media timing decisions.

## Decision Rules

- Map capture, transport, decode, and presentation timestamps into their actual timebases.
- Identify the synchronization clock and policy for drift, discontinuity, and missing timestamps.
- Bound buffering at each stage using the product latency and quality budget.
- Define whether late video or audio is dropped, concealed, resampled, or allowed to delay playback.
- Distinguish packet loss, jitter, queue growth, decoder stalls, and rendering delay before choosing a repair.
- Judge bitrate adaptation against received quality, queue delay, loss, and available device resources.
- Preserve track identity and cleanup through device replacement, permission revocation, and disconnect.
- Reconcile reconnect state with the current session rather than reviving obsolete tracks.
- Bound capture, codec, transport, and rendering work when consumers slow or stop.
- Observe end-to-end playout rather than treating connection establishment as media success.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Jitter delays packets without losing them | Buffer policy meets the selected latency/continuity tradeoff |
| Video falls behind audio | Clock and queue evidence explain synchronization repair |
| Camera or microphone changes during capture | Old tracks release resources and new identity is visible |
| Connection restarts after queued frames accumulate | Obsolete frames follow the declared drop/discontinuity policy |
| Decoder is slower than incoming media | Memory remains bounded and overload outcome is explicit |

## Proof Limits

- Static traces test timing decisions; actual devices and playback are needed for latency and synchronization claims.
