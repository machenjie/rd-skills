# Media Processing, Completeness, and Seek

Load for codec/container changes, transcoding, clipping, media completion, or seek behavior.
Skip uploads that preserve an opaque artifact without making playback claims.

## Decision Rules

- Bind codec, container, track layout, duration, and target-player support to the output contract.
- Distinguish decoding order from presentation order where the format requires it.
- Preserve timestamp and timebase meaning through trimming, concatenation, and transcoding.
- Check required headers, indexes, initialization data, and terminal metadata before accepting a finalized artifact.
- Validate duration and frame or sample continuity at segment boundaries.
- Exercise seek at the start, middle, end, and affected keyframe or segment boundaries.
- Bound decode dimensions, processing work, memory, temporary storage, and output size.
- Handle cancellation and truncated input without publishing an incomplete artifact as final.
- Inspect representative decoded content, audio/video synchronization, and track presence.
- Preserve the primary processing failure when cleanup or output deletion also fails.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Transcode exits successfully with truncated output | Playback or structural completeness check rejects the artifact |
| Seek reaches a segment boundary | Decoded result begins at the accepted position |
| Input contains unusual dimensions or duration | Resource limits bound the operation |
| Cancellation occurs before final metadata is written | Partial output remains distinguishable from final media |
| Timestamp conversion rounds repeatedly | Duration and synchronization remain within the accepted error budget |

## Proof Limits

- A command exit code, file size, or upload checksum alone cannot establish playable and seekable media.
