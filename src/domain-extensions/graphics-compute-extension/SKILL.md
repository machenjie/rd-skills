---
name: graphics-compute-extension
description: "For analysis/task/review agents: use for graphics or GPU execution, resources, synchronization, or device recovery; skip CSS and CPU-only calculations."
---

# graphics-compute-extension

## Role

Apply device execution, memory visibility, and rendering constraints to graphics and GPU computation.

## When To Use

- GPU resources, command submission, synchronization, shader interfaces, or device loss affect behavior.
- Coordinates, color, depth, kernel execution, or device-memory layout determine accepted output.

## Do Not Use

- The task changes ordinary CSS, labels, or CPU-only computation.
- A GPU vendor or API name appears without a device execution or resource decision.

## Required Inputs

- API/runtime and device versions, capabilities, queue/stream topology, resource ownership, and shader/kernel artifacts.
- Buffer/image layouts, coordinate/color conventions, error bounds, target workload, and observable output.

## Professional Decision Rules

- Trace CPU and GPU ownership from allocation through final use and destruction.
- Distinguish command submission from execution completion and host-visible results.
- Match synchronization and memory visibility to actual producer/consumer dependencies.
- Validate layouts, strides, alignment, formats, and shader interfaces against the selected API.
- Keep coordinate, color-space, depth, and numerical-error assumptions explicit.
- Recreate invalid resources through the device-loss recovery contract.
- Compare image or numerical correctness before accepting performance changes.

## High-Value Gotchas

- Validation success does not establish correct pixels, correct numbers, or sufficient synchronization on every target.
- A returned enqueue call does not prove the device completed the operation.

## Execution Checklist

1. Identify the affected API, device, resource, and execution dependency.
2. Exercise synchronization, lifetime, device-loss, and output-error cases relevant to that path.
3. Capture representative output and performance within the stated device scope.

## Stop / Escalation Conditions

- Stop when resource lifetime, execution ordering, layout, or output-error authority is unresolved.
- Report unsupported devices and unavailable captures instead of inferring portability.

## Output Contract

- Return ownership and synchronization decisions, artifact compatibility, output/error evidence, recovery behavior, and device limits.

## Targeted References

- No task-local Reference is indexed for this Skill.
