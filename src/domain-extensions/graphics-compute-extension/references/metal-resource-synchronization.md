# Metal Resource Synchronization

Load for Metal resource ownership, command dependencies, CPU/GPU visibility, or completion handling.
Skip non-Metal paths and changes without Metal resource or execution semantics.

## Decision Rules

- Bind Metal version, device family, resource storage mode, and supported synchronization features.
- Trace CPU and GPU reads and writes for each resource through command completion.
- Identify dependencies within an encoder, across encoders, across command buffers, and across queues.
- Select fences, events, or shared events according to their actual supported scope.
- Check CPU/GPU visibility requirements for the chosen resource storage and access mode.
- Keep resource lifetimes and reused buffer regions separate from command submission return.
- Validate shader argument layout, texture formats, color conventions, and depth behavior.
- Observe command failure and interruption before publishing output as successful.
- Rebuild invalid rendering state using the application recovery policy after device or command failure.
- Compare output correctness and error bounds before accepting lower frame time or higher throughput.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Producer and consumer use different command buffers | The selected synchronization primitive covers the actual dependency |
| CPU reads before GPU completion | Completion and visibility are established before use |
| Buffer region is reused while in flight | Ownership prevents overwrite of pending work |
| Shader interface or texture format changes | Pipeline compatibility and image results are checked |
| Command fails after submission | Application reports failure and does not publish incomplete output |

## Proof Limits

- Primitive availability and storage semantics depend on the target Metal environment.
- Success on Metal is not evidence for another graphics API.

## Sources

- [Metal resource synchronization](https://developer.apple.com/documentation/metal/resource-synchronization)
