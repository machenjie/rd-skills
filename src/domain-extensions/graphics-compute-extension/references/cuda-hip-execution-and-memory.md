# CUDA and HIP Execution and Memory

Load for CUDA or HIP kernels, device memory, streams, events, asynchronous copies, or synchronization.
Skip CPU-only C/C++ and graphics-only paths without CUDA or HIP execution.

## Decision Rules

- Bind the actual runtime, compiler, device architecture, and supported memory model.
- Map kernel launch shape to index bounds, tensor strides, layout, and allocated capacity.
- Check shared-memory and barrier participation against the kernel control flow.
- Distinguish host enqueue completion from kernel or transfer completion.
- Express cross-stream dependencies with supported events or waits rather than inferred ordering.
- Verify the configured default-stream behavior instead of assuming identical CUDA and HIP semantics.
- Keep host and device allocations valid through every asynchronous user.
- Check transfer direction, staging requirements, and host visibility before reading results.
- Observe launch and asynchronous execution failures at the relevant completion boundary.
- Validate reduction order, mixed precision, and accumulation range against the numerical error budget.
- Bound memory use and cleanup across cancellation, failure, and device recovery.
- Measure transfer, launch, kernel, and synchronization costs separately when identifying the actual bottleneck.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Two streams write and read shared data | Explicit dependency establishes the intended order |
| Host frees a transfer buffer after enqueue | Lifetime extends through the transfer completion |
| Kernel handles a partial final block | Index and synchronization behavior remain valid |
| Launch returns before a device error appears | Completion observation prevents false success |
| Optimized reduction changes accumulation order | Independent numeric oracle evaluates error before speedup acceptance |
| Port moves from CUDA to HIP | Target-specific defaults and supported behavior are revalidated |

## Proof Limits

- Shared source syntax does not establish identical scheduling, memory, or performance behavior across CUDA and HIP.

## Sources

- [CUDA asynchronous execution](https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/asynchronous-execution.html)
- [HIP asynchronous execution](https://rocm.docs.amd.com/projects/HIP/en/latest/how-to/hip_runtime_api/asynchronous.html)
