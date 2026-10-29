# WebGPU Device and Render Contracts

Load for WebGPU resources, command submission, shader interfaces, rendering conventions, or device loss.
Skip other graphics APIs and CSS-only rendering.

## Decision Rules

- Bind WebGPU features, limits, formats, and shader language support to the actual adapter and device.
- Map buffer usage, offsets, sizes, alignment, and bind-group layouts to shader access.
- Check texture format, color space, sample count, and render/depth attachment compatibility.
- Preserve the coordinate, depth, and alpha conventions used by each pipeline stage.
- Distinguish host method return from device-timeline validation and execution completion.
- Observe validation failures through the intended error mechanism instead of assuming enqueue success.
- Keep resources alive until their submitted work no longer depends on them.
- Handle device loss by invalidating old-device resources and reconstructing state on a usable device.
- Reject stale asynchronous completions associated with a lost or replaced device.
- Compare rendered images or computed values against a defined oracle and error budget.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Shader binding disagrees with buffer layout | Validation and output checks identify the incompatible interface |
| Device is lost during submitted work | Old resources and results cannot be reused as current |
| Color-space or alpha convention changes | Image comparison detects the semantic difference |
| Method returns before device work fails | Error observation prevents a false success claim |
| Adapter limits differ from the development device | Unsupported capability follows an explicit path |

## Proof Limits

- The WebGPU specification evolves; use the deployed implementation and supported feature contract.
- Validation cleanliness does not prove pixel correctness or cross-device performance.

## Sources

- [WebGPU specification](https://www.w3.org/TR/webgpu/)
